import unittest
from unittest.mock import patch
from io import BytesIO
import json
import importlib.util

from hybrid_anon.pipeline import anonymize, merge_spans
from hybrid_anon.entities import EntitySpan
from hybrid_anon.rules import valid_tckn, valid_iban, valid_structured_candidate
from hybrid_anon.model_adapters import detect_gliner, detect_ner
from hybrid_anon.local_llm import local_ollama_review, needs_review


class CoreTests(unittest.TestCase):
    def test_demo_context_masks_invalid_tckn(self):
        text = "Ahmet Yılmaz'ın TC kimlik numarası 12345678901 ve plakası 34 ABC 123'tür."
        result, spans = anonymize(text)
        self.assertEqual(result, "<PERSON>'ın TC kimlik numarası <TCKN> ve plakası <VEHICLE_PLATE>'tür.")
        self.assertEqual(len(spans), 3)

    def test_checksums_and_negative_context(self):
        self.assertTrue(valid_tckn("10000000146"))
        self.assertFalse(valid_tckn("12345678901"))
        self.assertTrue(valid_iban("TR33 0006 1005 1978 6457 8413 26"))
        self.assertFalse(valid_iban("TR00 0000 0000 0000 0000 0000 00"))
        self.assertEqual(anonymize("Referans 12345678901 ve TR00 0000 0000 0000 0000 0000 00.")[1], [])

    def test_overlap_and_suffix(self):
        text = "34 ABC 123'ün"
        spans = merge_spans(text, [EntitySpan(0, 10, "VEHICLE_PLATE", .9, "rules"),
                                   EntitySpan(3, 10, "PERSON", .99, "ner")])
        self.assertEqual([(s.start, s.end, s.label) for s in spans], [(0, 10, "VEHICLE_PLATE")])
        self.assertEqual(anonymize(text)[0], "<VEHICLE_PLATE>'ün")

    def test_rule_address_wins_over_partial_model_span(self):
        text = "Atatürk Mahallesi No: 12/4, Ankara"
        spans = merge_spans(text, [EntitySpan(0, 26, "ADDRESS", .67, "address_rule"),
                                   EntitySpan(0, 20, "ADDRESS", .99, "turkish_ner")])
        self.assertEqual([(s.start, s.end) for s in spans], [(0, 26)])

    def test_optional_model_output_mapping(self):
        with patch("hybrid_anon.model_adapters._gliner") as model:
            model.return_value.predict_entities.return_value = [
                {"start": 0, "end": 12, "label": "person", "score": 0.8}]
            self.assertEqual(detect_gliner("Ahmet Yılmaz")[0].label, "PERSON")
        with patch("hybrid_anon.model_adapters._ner") as model:
            model.return_value.return_value = [
                {"start": 0, "end": 12, "entity_group": "KISI_AD_SOYAD", "score": 0.9}]
            self.assertEqual(detect_ner("Ahmet Yılmaz")[0].label, "PERSON")

    def test_invalid_model_iban_rejected(self):
        from hybrid_anon.pipeline import detect
        text = "Hatalı hesap kodu TR00 0000 0000 0000 0000 0000 00 yazıldı."
        with patch("hybrid_anon.model_adapters.detect_ner",
                   return_value=[EntitySpan(18, 22, "IBAN", .99, "turkish_ner")]):
            self.assertEqual(detect(text, engines=("ner",)), [])

    def test_gliner_role_and_non_alcohol_measurement_rejected(self):
        text = "Sigortalı 0,82 promil; engellilik oranı %40."
        self.assertFalse(valid_structured_candidate(text, EntitySpan(0, 9, "PERSON", .9, "gliner")))
        self.assertTrue(valid_structured_candidate(text, EntitySpan(10, 21, "BAC_VALUE", .9, "gliner")))
        self.assertFalse(valid_structured_candidate(text, EntitySpan(23, 42, "BAC_VALUE", .9, "gliner")))

    def test_local_llm_accepts_only_unique_exact_quotes(self):
        text = "Sigortalının HbA1c 8.7 sonucu var."
        payload = {"response": json.dumps({"entities": [
            {"quote": "HbA1c 8.7", "label": "HEALTH_INFORMATION"},
            {"quote": "olmayan ifade", "label": "PERSON"}]})}
        with patch("hybrid_anon.local_llm.urlopen",
                   return_value=BytesIO(json.dumps(payload).encode())):
            spans = local_ollama_review(text, "local-model")
        self.assertTrue(needs_review(text))
        self.assertEqual([(s.start, s.end, s.label) for s in spans],
                         [(13, 22, "HEALTH_INFORMATION")])

    @unittest.skipUnless(importlib.util.find_spec("presidio_analyzer"), "Presidio kurulu değil")
    def test_presidio_custom_detection_and_masking(self):
        text = "Poliçe POL-2026-000123 düzenlendi."
        result, spans = anonymize(text, engines=("presidio",), masker="presidio")
        self.assertEqual(result, "Poliçe <POLICY_NUMBER> düzenlendi.")
        self.assertEqual([(s.label, s.source) for s in spans],
                         [("POLICY_NUMBER", "presidio_custom")])


if __name__ == "__main__":
    unittest.main()
