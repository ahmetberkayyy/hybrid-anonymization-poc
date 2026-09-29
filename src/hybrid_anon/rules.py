"""Conservative Turkish rules. Format checks are separate from context checks."""

import re

from .entities import EntitySpan


def valid_tckn(value: str) -> bool:
    if not re.fullmatch(r"[1-9]\d{10}", value):
        return False
    d = [int(x) for x in value]
    return (7 * sum(d[0:9:2]) - sum(d[1:8:2])) % 10 == d[9] and sum(d[:10]) % 10 == d[10]


def valid_iban(value: str) -> bool:
    compact = re.sub(r"\s+", "", value).upper()
    if not re.fullmatch(r"TR\d{24}", compact):
        return False
    expanded = compact[4:] + compact[:4]
    digits = "".join(str(ord(c) - 55) if c.isalpha() else c for c in expanded)
    return int(digits) % 97 == 1


PATTERNS = {
    "TCKN": re.compile(r"(?<!\d)[1-9]\d{10}(?!\d)"),
    "IBAN": re.compile(r"\bTR\d{2}(?:\s?\d{4}){5}\s?\d{2}\b|\bTR\d{24}\b", re.I),
    "EMAIL": re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?!\w)"),
    "PHONE": re.compile(r"(?<!\d)(?:\+90\s?|0)?5\d{2}[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}(?!\d)"),
    "VEHICLE_PLATE": re.compile(r"(?<!\w)(?:0[1-9]|[1-7]\d|8[01])\s?[A-ZÇĞİÖŞÜ]{1,3}\s?\d{2,4}(?!\w)", re.I),
    "POLICY_NUMBER": re.compile(r"(?<!\w)(?:POL|PLC)[-/ ]?\d{4}[-/ ]?\d{3,8}(?!\w)", re.I),
    "CLAIM_NUMBER": re.compile(r"(?<!\w)(?:HSR|HAS)[-/ ]?\d{4}[-/ ]?\d{3,8}(?!\w)", re.I),
}

TCKN_CONTEXT = re.compile(r"(?:T\.?C\.?\s*kimlik|TCKN|kimlik\s*(?:no|numara))", re.I)
PERSON_CONTEXT = re.compile(r"([A-ZÇĞİÖŞÜ][a-zçğıöşü]+\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+)(?=['’](?:ın|in|un|ün|nın|nin|nun|nün)\s+(?:TC|TCKN|kimlik))")
ADDRESS = re.compile(r"(?:(?:[A-ZÇĞİÖŞÜ][\wçğıöşü]+\s+){0,3}(?:Mahallesi|Mah\.|Caddesi|Cad\.|Sokak|Sk\.)\s*(?:No\s*:?\s*\d+[A-Za-z]?(?:/\d+)?)?)(?=\s|[,.;]|$)", re.I)
HEALTH_TERMS = re.compile(r"\b(?:diyabet|diabet|insülin|kanser|epilepsi|astım|hipertansiyon|etanol|alkollü|engellilik)\b", re.I)
BAC = re.compile(r"(?<!\d)\d{1,2}[,.]\d{1,2}\s*promil\b", re.I)


def detect_rules(text: str) -> list[EntitySpan]:
    found: list[EntitySpan] = []
    for label, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            score = 0.95
            if label == "TCKN":
                near = text[max(0, match.start() - 35): match.start()]
                if valid_tckn(match.group()):
                    score = 0.99
                elif TCKN_CONTEXT.search(near):
                    score = 0.65  # Invalid example may still contain a sensitive identifier.
                else:
                    continue
            elif label == "IBAN" and not valid_iban(match.group()):
                continue
            elif label in {"POLICY_NUMBER", "CLAIM_NUMBER"}:
                score = 0.85  # Institution-specific formats must be configured in production.
            found.append(EntitySpan(match.start(), match.end(), label, score, "rules"))
    for match in PERSON_CONTEXT.finditer(text):
        found.append(EntitySpan(match.start(1), match.end(1), "PERSON", 0.78, "person_context_rule"))
    for match in ADDRESS.finditer(text):
        if any(ch.isdigit() for ch in match.group()):
            found.append(EntitySpan(match.start(), match.end(), "ADDRESS", 0.67, "address_rule"))
    for match in HEALTH_TERMS.finditer(text):
        found.append(EntitySpan(match.start(), match.end(), "HEALTH_INFORMATION", 0.55, "health_lexicon"))
    for match in BAC.finditer(text):
        found.append(EntitySpan(match.start(), match.end(), "BAC_VALUE", 0.9, "bac_rule"))
    return found


def valid_structured_candidate(text: str, span: EntitySpan) -> bool:
    """Reject malformed model spans for entities with deterministic formats."""
    if not 0 <= span.start < span.end <= len(text):
        return False
    value = text[span.start:span.end]
    if span.label == "TCKN":
        return valid_tckn(value) or bool(TCKN_CONTEXT.search(text[max(0, span.start - 35):span.start]))
    if span.label == "IBAN":
        return valid_iban(value)
    if span.label == "BAC_VALUE":
        return bool(BAC.fullmatch(value))
    if span.label == "PERSON" and span.source == "gliner":
        return bool(re.fullmatch(r"[A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+)+", value))
    if span.label in {"EMAIL", "PHONE", "VEHICLE_PLATE"}:
        return bool(PATTERNS[span.label].fullmatch(value))
    return True
