from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from friend_brief.briefing import generate_grounded_brief
from friend_brief.data import company_by_symbol, load_snapshot
from friend_brief.ollama_client import OllamaClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate validated briefs for public demo mode.")
    parser.add_argument("--snapshot", default="data/demo_snapshot.json")
    parser.add_argument("--output", default="data/demo_briefs.json")
    parser.add_argument("--model", default="gemma3:4b")
    parser.add_argument("--base-url", default="http://127.0.0.1:11434")
    parser.add_argument("--symbols", nargs="+", default=["NVDA", "VRT", "CEG"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    snapshot = load_snapshot(args.snapshot)
    client = OllamaClient(args.base_url, args.model)
    if not client.is_available():
        raise SystemExit("Ollama is not available")

    briefs = {}
    for symbol in args.symbols:
        company = company_by_symbol(snapshot, symbol)
        brief = generate_grounded_brief(client, company, "Plain English")
        briefs[company.symbol] = brief.model_dump(mode="json")
        print(f"Generated {company.symbol}")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(UTC).isoformat(),
                "model": args.model,
                "briefs": briefs,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
