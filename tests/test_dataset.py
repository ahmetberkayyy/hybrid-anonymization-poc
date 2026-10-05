import json
import unittest
from collections import Counter
from pathlib import Path

from hybrid_anon.entities import EntitySpan
from hybrid_anon.rules import valid_structured_candidate


DATASET = Path(__file__).resolve().parents[1] / "data" / "synthetic_tr.jsonl"


class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = [json.loads(line) for line in DATASET.read_text(encoding="utf-8").splitlines()
                    if line.strip()]

    def test_dataset_size_balance_and_ids(self):
        self.assertGreaterEqual(len(self.rows), 100)
        self.assertEqual(len({row["id"] for row in self.rows}), len(self.rows))
        self.assertGreaterEqual(sum(not row["entities"] for row in self.rows), 15)
        self.assertTrue(all(row.get("split") == "test" for row in self.rows))

        counts = Counter(entity["label"] for row in self.rows for entity in row["entities"])
        minimum_support = {
            "PERSON": 15, "TCKN": 8, "IBAN": 6, "PHONE": 9, "EMAIL": 8,
            "VEHICLE_PLATE": 9, "POLICY_NUMBER": 10, "CLAIM_NUMBER": 9,
            "ADDRESS": 9, "HEALTH_INFORMATION": 20, "BAC_VALUE": 5,
        }
        for label, minimum in minimum_support.items():
            self.assertGreaterEqual(counts[label], minimum, (label, counts[label]))

    def test_offsets_are_valid_non_overlapping_and_structured_values_validate(self):
        for row in self.rows:
            text = row["text"]
            spans = []
            for entity in row["entities"]:
                start, end, label = entity["start"], entity["end"], entity["label"]
                self.assertTrue(0 <= start < end <= len(text), (row["id"], entity))
                span = EntitySpan(start, end, label, 1.0, "rules")
                self.assertTrue(valid_structured_candidate(text, span),
                                (row["id"], text[start:end], label))
                spans.append((start, end, label))
            self.assertEqual(len(spans), len(set(spans)), row["id"])
            for index, current in enumerate(spans):
                for other in spans[index + 1:]:
                    self.assertFalse(current[0] < other[1] and other[0] < current[1],
                                     (row["id"], current, other))


if __name__ == "__main__":
    unittest.main()
