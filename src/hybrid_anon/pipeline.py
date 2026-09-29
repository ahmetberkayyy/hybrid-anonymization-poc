"""Detector orchestration, overlap resolution and reversible-offset masking."""

from .entities import EntitySpan
from .rules import detect_rules, valid_structured_candidate


PRIORITY = {"TCKN": 10, "IBAN": 10, "EMAIL": 9, "PHONE": 9,
            "VEHICLE_PLATE": 8, "POLICY_NUMBER": 8, "CLAIM_NUMBER": 8,
            "PERSON": 6, "ADDRESS": 5, "BAC_VALUE": 5,
            "HEALTH_INFORMATION": 4}
SOURCE_PRIORITY = {"rules": 3, "presidio_custom": 2, "person_context_rule": 2,
                   "address_rule": 2, "bac_rule": 2, "turkish_ner": 1,
                   "gliner": 1, "health_lexicon": 2, "local_llm": 0}


def merge_spans(text: str, candidates: list[EntitySpan]) -> list[EntitySpan]:
    valid = [s for s in candidates if 0 <= s.start < s.end <= len(text)]
    ordered = sorted(valid, key=lambda s: (-PRIORITY.get(s.label, 0),
                                             -SOURCE_PRIORITY.get(s.source, 0), -s.score,
                                             -(s.end - s.start), s.start, s.source))
    accepted: list[EntitySpan] = []
    for span in ordered:
        if not any(span.start < other.end and other.start < span.end for other in accepted):
            accepted.append(span)
    return sorted(accepted, key=lambda s: (s.start, s.end))


def detect(text: str, *, engines: tuple[str, ...] = ("rules",), threshold: float = 0.5,
           local_llm_model: str | None = None) -> list[EntitySpan]:
    candidates: list[EntitySpan] = []
    if "rules" in engines:
        candidates.extend(detect_rules(text))
    if "presidio" in engines:
        from .presidio_adapter import detect_presidio
        candidates.extend(detect_presidio(text))
    if "gliner" in engines:
        from .model_adapters import detect_gliner
        candidates.extend(detect_gliner(text))
    if "ner" in engines:
        from .model_adapters import detect_ner
        candidates.extend(detect_ner(text))
    merged = merge_spans(text, [s for s in candidates if s.score >= threshold and
                                valid_structured_candidate(text, s)])
    if local_llm_model:
        from .local_llm import local_ollama_review, needs_review
        if needs_review(text):
            candidates.extend(local_ollama_review(text, local_llm_model))
            merged = merge_spans(text, [s for s in candidates if s.score >= threshold and
                                        valid_structured_candidate(text, s)])
    return merged


def anonymize(text: str, *, engines: tuple[str, ...] = ("rules",), threshold: float = 0.5,
              masker: str = "python", local_llm_model: str | None = None) -> tuple[str, list[EntitySpan]]:
    spans = detect(text, engines=engines, threshold=threshold,
                   local_llm_model=local_llm_model)
    if masker == "presidio":
        try:
            from presidio_anonymizer import AnonymizerEngine
            from presidio_anonymizer.entities import RecognizerResult
        except ImportError as exc:
            raise RuntimeError("Presidio anonymizer kurulu değil. 'pip install -e .[presidio]' kullanın.") from exc
        results = [RecognizerResult(entity_type=s.label, start=s.start, end=s.end, score=s.score)
                   for s in spans]
        return AnonymizerEngine().anonymize(text=text, analyzer_results=results).text, spans
    if masker != "python":
        raise ValueError("masker 'python' veya 'presidio' olmalı")
    result = text
    for span in reversed(spans):
        result = result[:span.start] + f"<{span.label}>" + result[span.end:]
    return result, spans
