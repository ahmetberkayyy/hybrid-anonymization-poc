"""Rebuild the synthetic span-annotated corpus without manual offset errors."""

import json
from pathlib import Path


CASES = [
    ("demo_invalid_tckn", "Ahmet Yılmaz'ın TC kimlik numarası 12345678901 ve plakası 34 ABC 123'tür.",
     [("Ahmet Yılmaz", "PERSON"), ("12345678901", "TCKN"), ("34 ABC 123", "VEHICLE_PLATE")]),
    ("valid_tckn", "Ayşe Demir'in TCKN 10000000146 olarak kaydedildi.",
     [("Ayşe Demir", "PERSON"), ("10000000146", "TCKN")]),
    ("contact", "İletişim: deniz.kaya@example.com, 0532 123 45 67.",
     [("deniz.kaya@example.com", "EMAIL"), ("0532 123 45 67", "PHONE")]),
    ("iban", "Ödeme IBAN: TR33 0006 1005 1978 6457 8413 26 hesabına yapılacak.",
     [("TR33 0006 1005 1978 6457 8413 26", "IBAN")]),
    ("insurance_ids", "Poliçe POL-2026-000123 ve hasar HSR-2026-456789 dosyası açıldı.",
     [("POL-2026-000123", "POLICY_NUMBER"), ("HSR-2026-456789", "CLAIM_NUMBER")]),
    ("address", "İkamet adresi: Atatürk Mahallesi No: 12/4, Ankara.",
     [("Atatürk Mahallesi No: 12/4", "ADDRESS")]),
    ("health", "Sigortalının diyabet tanısı var ve insülin kullanıyor.",
     [("diyabet", "HEALTH_INFORMATION"), ("insülin", "HEALTH_INFORMATION")]),
    ("alcohol", "Sürücünün 0,82 promil alkollü olduğu görüldü.",
     [("0,82 promil", "BAC_VALUE"), ("alkollü", "HEALTH_INFORMATION")]),
    ("medical_test", "Kanında etanol saptandı, engellilik oranı %40.",
     [("etanol", "HEALTH_INFORMATION"), ("engellilik", "HEALTH_INFORMATION")]),
    ("invalid_tckn_negative", "Sipariş referansı 12345678901 teslim edildi.", []),
    ("invalid_iban_negative", "Hatalı hesap kodu TR00 0000 0000 0000 0000 0000 00 yazıldı.", []),
    ("no_entity", "Poliçe kapsamı ve teminat koşulları görüşüldü.", []),
    ("plate_and_claim", "34 ABC 123 plakalı araç için HAS/2026/12345 kaydı var.",
     [("34 ABC 123", "VEHICLE_PLATE"), ("HAS/2026/12345", "CLAIM_NUMBER")]),
    ("free_person", "Eksper Mehmet Aksoy raporu inceledi.",
     [("Mehmet Aksoy", "PERSON")]),
    ("alternative_policy", "Poliçe numarası 2026/AB/12345 iptal edildi.",
     [("2026/AB/12345", "POLICY_NUMBER")]),
    ("indirect_health", "Sigortalı düzenli olarak kan şekeri ölçümü yapıyor.",
     [("kan şekeri ölçümü", "HEALTH_INFORMATION")]),
    ("medical_measurement", "Laboratuvar sonucunda HbA1c 8.7 görüldü.",
     [("HbA1c 8.7", "HEALTH_INFORMATION")]),
]


def main() -> None:
    destination = Path(__file__).with_name("synthetic_tr.jsonl")
    with destination.open("w", encoding="utf-8") as stream:
        for case_id, text, annotations in CASES:
            entities = []
            for value, label in annotations:
                assert text.count(value) == 1, (case_id, value)
                start = text.index(value)
                entities.append({"start": start, "end": start + len(value), "label": label})
            stream.write(json.dumps({"id": case_id, "text": text, "entities": entities},
                                    ensure_ascii=False) + "\n")
    print(f"{len(CASES)} sentetik örnek: {destination}")


if __name__ == "__main__":
    main()
