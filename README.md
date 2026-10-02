# Argus Friend Brief

Argus Friend Brief turns structured Argus market research into a plain-language,
evidence-linked briefing using a local Gemma model through Ollama. It was created for
the Hacktoberfest 2026 **Build for a Friend** challenge.

The intended reader is the family member who shares the Argus research workflow but
does not want to decode every metric, filing, signal, and valuation table. This is a
research translator—not a trading system or investment adviser.

## What makes it different

- Local open-weight inference: the research snapshot stays on the laptop.
- Evidence-first generation: every factual claim must reference a compact exported evidence ID.
- Citation validation: unsupported evidence IDs trigger one repair attempt and then fail closed.
- Reproducible demo: a sanitized snapshot is committed, so no Argus or database credentials are required.
- Read-only ingestion: the exporter opens the Argus SQLite database in immutable read-only mode.

## Run locally

Requirements: Python 3.12+, `uv`, and [Ollama](https://ollama.com/) with a Gemma model.

```bash
ollama pull gemma3:4b
ollama serve
uv sync --extra dev
uv run streamlit run app.py
```

Configuration can be set through environment variables; see `.env.example`.

## Refresh the demo snapshot

The application ships with a sanitized 53-company snapshot. To create a small snapshot
from a local Argus SQLite database:

```bash
uv run python scripts/export_argus_snapshot.py \
  --database ../argus/data/app.db \
  --output data/demo_snapshot.json \
  --symbols NVDA VRT CEG
```

To export every active company from the production Postgres database without placing a
credential on the command line:

```bash
uv run python scripts/export_argus_snapshot.py \
  --env-file ../argus/.env \
  --output data/demo_snapshot.json \
  --all-active
```

The production connection is placed in a read-only transaction. The env file is read only
to construct the connection and is never copied into the snapshot.

The exporter deliberately excludes watchlist notes and authentication data. Do not commit
private notes, credentials, or an Argus database.

## Test

```bash
uv run pytest
uv run ruff check .
```

## Safety boundary

The model receives only the exported evidence catalog. Prompts forbid buy/sell/hold
instructions, personalized recommendations, invented price targets, and outside facts.
Outputs can still be wrong; inspect the cited evidence and source dates. Nothing produced
by this project is financial advice.

## License

MIT
