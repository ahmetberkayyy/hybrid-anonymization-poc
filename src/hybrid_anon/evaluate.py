"""Exact character-span evaluation for the shared synthetic test set."""

import json
from collections import Counter
from pathlib import Path
from time import perf_counter

from .pipeline import detect


def evaluate(path: Path, engines: tuple[str, ...], threshold: float,
             local_llm_model: str | None = None) -> dict:
    tp = fp = fn = 0
    by_label = {"tp": Counter(), "fp": Counter(), "fn": Counter()}
    cases = []
    start_time = perf_counter()
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            gold = {(e["start"], e["end"], e["label"]) for e in row["entities"]}
            predicted = {(s.start, s.end, s.label) for s in detect(row["text"], engines=engines,
                                                                      threshold=threshold,
                                                                      local_llm_model=local_llm_model)}
            tp += len(gold & predicted)
            fp += len(predicted - gold)
            fn += len(gold - predicted)
            for _, _, label in gold & predicted:
                by_label["tp"][label] += 1
            for _, _, label in predicted - gold:
                by_label["fp"][label] += 1
            for _, _, label in gold - predicted:
                by_label["fn"][label] += 1
            cases.append({"id": row["id"], "tp": len(gold & predicted),
                          "fp": len(predicted - gold), "fn": len(gold - predicted),
                          "missed": [list(x) for x in sorted(gold - predicted)],
                          "extra": [list(x) for x in sorted(predicted - gold)]})
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    labels = sorted(set().union(*[set(c) for c in by_label.values()]))
    per_entity = {}
    for label in labels:
        a, b, c = (by_label[k][label] for k in ("tp", "fp", "fn"))
        p = a / (a + b) if a + b else 0.0
        r = a / (a + c) if a + c else 0.0
        per_entity[label] = {"tp": a, "fp": b, "fn": c,
                             "precision": round(p, 4), "recall": round(r, 4)}
    return {"engines": engines, "local_llm_model": local_llm_model,
            "threshold": threshold, "cases": len(cases),
            "tp": tp, "fp": fp, "fn": fn, "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(2 * precision * recall / (precision + recall), 4)
            if precision + recall else 0.0,
            "per_entity": per_entity,
            "elapsed_seconds": round(perf_counter() - start_time, 3),
            "details": cases}
