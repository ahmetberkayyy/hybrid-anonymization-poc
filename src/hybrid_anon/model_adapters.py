"""Optional on-prem models. Model downloads occur only when explicitly requested."""

from functools import lru_cache
import os

from .entities import EntitySpan


GLINER_MODEL = os.getenv("ANON_GLINER_MODEL", "urchade/gliner_multi-v2.1")
NER_MODEL = os.getenv("ANON_NER_MODEL", "ytu-ce-cosmos/modernbert-tr-pii-ner")
GLINER_LABELS = {
    "person": "PERSON",
    "address": "ADDRESS",
    "Turkish national identity number": "TCKN",
    "IBAN": "IBAN",
    "phone number": "PHONE",
    "email address": "EMAIL",
    "vehicle license plate": "VEHICLE_PLATE",
    "medical condition": "HEALTH_INFORMATION",
    "medication": "HEALTH_INFORMATION",
    "medical test result": "HEALTH_INFORMATION",
    "blood alcohol level": "BAC_VALUE",
    "insurance policy number": "POLICY_NUMBER",
    "insurance claim number": "CLAIM_NUMBER",
}
NER_LABELS = {
    "KISI_AD_SOYAD": "PERSON", "TCKN": "TCKN", "TELEFON": "PHONE",
    "EMAIL": "EMAIL", "ADRES": "ADDRESS", "PLAKA": "VEHICLE_PLATE",
    "IBAN_TR": "IBAN", "SAGLIK_BILGISI": "HEALTH_INFORMATION",
    "PERSON": "PERSON", "PER": "PERSON", "ADDRESS": "ADDRESS",
    "PHONE": "PHONE", "IBAN": "IBAN", "HEALTH_INFORMATION": "HEALTH_INFORMATION",
    "HASTALIK": "HEALTH_INFORMATION", "ILAC": "HEALTH_INFORMATION",
    "SEMPTOM": "HEALTH_INFORMATION", "TEST": "HEALTH_INFORMATION",
}


@lru_cache(maxsize=1)
def _gliner():
    try:
        from gliner import GLiNER
    except ImportError as exc:
        raise RuntimeError("GLiNER kurulu değil. 'pip install -e .[models]' komutunu kullanın.") from exc
    try:
        return GLiNER.from_pretrained(GLINER_MODEL)
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"GLiNER ağırlığı yüklenemedi: {GLINER_MODEL}. Yerel model yolunu ANON_GLINER_MODEL ile belirtin.") from exc


def detect_gliner(text: str) -> list[EntitySpan]:
    predictions = _gliner().predict_entities(text, list(GLINER_LABELS), threshold=0.35)
    return [EntitySpan(int(p["start"]), int(p["end"]), GLINER_LABELS[p["label"]],
                       float(p["score"]), "gliner") for p in predictions
            if p.get("label") in GLINER_LABELS]


@lru_cache(maxsize=1)
def _ner():
    try:
        from transformers import pipeline
    except ImportError as exc:
        raise RuntimeError("Transformers kurulu değil. 'pip install -e .[models]' komutunu kullanın.") from exc
    try:
        return pipeline("token-classification", model=NER_MODEL,
                        aggregation_strategy="first", device=-1)
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"Türkçe NER ağırlığı yüklenemedi: {NER_MODEL}. Yerel model yolunu ANON_NER_MODEL ile belirtin.") from exc


def detect_ner(text: str) -> list[EntitySpan]:
    predictions = _ner()(text)
    spans = []
    for p in predictions:
        raw_label = str(p.get("entity_group", "")).upper()
        label = NER_LABELS.get(raw_label)
        if label:
            spans.append(EntitySpan(int(p["start"]), int(p["end"]), label,
                                    float(p["score"]), "turkish_ner"))
    return spans
