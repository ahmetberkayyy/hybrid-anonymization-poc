"""Presidio with Turkish custom recognizers and no implicit English NLP model."""

from functools import lru_cache

from .entities import EntitySpan
from .rules import PATTERNS, TCKN_CONTEXT, valid_iban, valid_tckn


@lru_cache(maxsize=1)
def _analyzer():
    try:
        from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer, RecognizerRegistry
        from presidio_analyzer.nlp_engine import NoOpNlpEngine
    except ImportError as exc:
        raise RuntimeError("Presidio kurulu değil. 'pip install -e .[presidio]' komutunu kullanın.") from exc

    registry = RecognizerRegistry(supported_languages=["tr"])
    for label, regex in PATTERNS.items():
        registry.add_recognizer(PatternRecognizer(
            supported_entity=label, supported_language="tr",
            patterns=[Pattern(name=f"tr_{label.lower()}", regex=regex.pattern, score=0.7)],
        ))
    return AnalyzerEngine(nlp_engine=NoOpNlpEngine(models=[{"lang_code": "tr", "model_name": ""}]), registry=registry,
                          supported_languages=["tr"])


def detect_presidio(text: str) -> list[EntitySpan]:
    results = _analyzer().analyze(text=text, language="tr")
    spans: list[EntitySpan] = []
    for result in results:
        value = text[result.start:result.end]
        if result.entity_type == "TCKN" and not valid_tckn(value):
            if not TCKN_CONTEXT.search(text[max(0, result.start - 35):result.start]):
                continue
        if result.entity_type == "IBAN" and not valid_iban(value):
            continue
        spans.append(EntitySpan(result.start, result.end, result.entity_type,
                                result.score, "presidio_custom"))
    return spans
