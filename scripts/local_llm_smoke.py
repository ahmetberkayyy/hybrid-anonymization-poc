"""Small end-to-end check for the local Ollama review layer."""

import argparse
import json

from hybrid_anon.local_llm import local_ollama_review


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen3:4b")
    parser.add_argument(
        "--text",
        default="Eksper Mehmet Aksoy, sigortalının HbA1c 8.7 sonucunu ve diyabet tanısını inceledi.",
    )
    args = parser.parse_args()

    spans = local_ollama_review(args.text, args.model)
    masked = args.text
    for span in reversed(spans):
        masked = masked[:span.start] + f"<{span.label}>" + masked[span.end:]

    print(masked)
    print(json.dumps([span.as_dict() for span in spans], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
