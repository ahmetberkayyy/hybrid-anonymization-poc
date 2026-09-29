"""Repeatable engine evaluation; records failures instead of pretending a test ran."""

import argparse
import importlib.metadata
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

from hybrid_anon.evaluate import evaluate


PACKAGES = ("presidio-analyzer", "presidio-anonymizer", "gliner", "transformers", "torch", "protobuf")
ENGINES = (("rules",), ("presidio",), ("rules", "presidio"),
           ("ner",), ("rules", "presidio", "ner"), ("gliner",),
           ("rules", "presidio", "ner", "gliner"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/synthetic_tr.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("docs/benchmark_results.json"))
    parser.add_argument("--include-models", action="store_true",
                        help="Ağırlıkları indirebilir; ner, gliner ve hibrit çalıştır")
    parser.add_argument("--include-ner", action="store_true",
                        help="Yalnız Türkçe NER içeren koşuları çalıştır")
    parser.add_argument("--include-gliner", action="store_true",
                        help="Yalnız GLiNER içeren koşuları çalıştır")
    args = parser.parse_args()
    versions = {}
    for package in PACKAGES:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    report = {"measured_at_utc": datetime.now(timezone.utc).isoformat(),
              "python": sys.version.split()[0], "platform": platform.platform(),
              "packages": versions, "dataset": str(args.data), "runs": []}
    for engines in ENGINES:
        name = "+".join(engines)
        run_ner = args.include_models or args.include_ner
        run_gliner = args.include_models or args.include_gliner
        if ("ner" in engines and not run_ner) or ("gliner" in engines and not run_gliner):
            report["runs"].append({"name": name, "status": "not_run",
                                   "reason": "İlgili --include-ner/--include-gliner seçilmedi"})
            continue
        try:
            result = evaluate(args.data, engines, 0.5)
            result.pop("details")
            report["runs"].append({"name": name, "status": "completed", "result": result})
        except (ImportError, RuntimeError, OSError) as exc:
            report["runs"].append({"name": name, "status": "failed",
                                   "reason": str(exc)})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
