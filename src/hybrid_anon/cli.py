import argparse
import json
from pathlib import Path

from .pipeline import anonymize, detect


def main() -> None:
    parser = argparse.ArgumentParser(description="Türkçe hibrit anonimleştirme PoC")
    parser.add_argument("text", nargs="?", help="Anonimleştirilecek metin")
    parser.add_argument("--engines", default="rules", help="Virgülle ayrılmış: rules,presidio,ner,gliner")
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--masker", choices=("python", "presidio"), default="python")
    parser.add_argument("--local-llm-model", help="Yalnız localhost Ollama üzerinden ikinci kontrol")
    parser.add_argument("--evaluate", type=Path, help="Etiketli JSONL veri seti")
    args = parser.parse_args()
    engines = tuple(x.strip() for x in args.engines.split(",") if x.strip())
    if any(x not in {"rules", "presidio", "ner", "gliner"} for x in engines):
        parser.error("Geçersiz engine. Seçenekler: rules,presidio,ner,gliner")
    try:
        if args.evaluate:
            from .evaluate import evaluate
            print(json.dumps(evaluate(args.evaluate, engines, args.threshold,
                                      args.local_llm_model),
                             ensure_ascii=False, indent=2))
        elif args.text is not None:
            output, spans = anonymize(args.text, engines=engines, threshold=args.threshold,
                                      masker=args.masker, local_llm_model=args.local_llm_model)
            print(output)
            print(json.dumps([s.as_dict() for s in spans], ensure_ascii=False, indent=2))
        else:
            parser.error("Bir metin veya --evaluate verin")
    except RuntimeError as exc:
        parser.exit(2, f"Hata: {exc}\n")


if __name__ == "__main__":
    main()
