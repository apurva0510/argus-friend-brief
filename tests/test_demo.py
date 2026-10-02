from __future__ import annotations

import json

from friend_brief.citations import validate_citations
from friend_brief.data import company_by_symbol, load_snapshot
from friend_brief.demo import load_demo_briefs
from friend_brief.safety import disallowed_language


def test_load_demo_briefs(tmp_path) -> None:
    path = tmp_path / "briefs.json"
    path.write_text(
        json.dumps(
            {
                "briefs": {
                    "nvda": {
                        "headline": "Evidence-led update",
                        "what_changed": [],
                        "why_it_matters": [],
                        "bull_case": [],
                        "bear_case": [],
                        "watch_next": [],
                        "limitations": ["Saved example"],
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    briefs = load_demo_briefs(path)

    assert briefs["NVDA"].headline == "Evidence-led update"


def test_load_demo_briefs_returns_empty_for_missing_file(tmp_path) -> None:
    assert load_demo_briefs(tmp_path / "missing.json") == {}


def test_committed_demo_briefs_are_grounded_and_safe() -> None:
    snapshot = load_snapshot("data/demo_snapshot.json")
    briefs = load_demo_briefs("data/demo_briefs.json")

    assert set(briefs) == {"NVDA", "VRT", "CEG"}
    for symbol, brief in briefs.items():
        company = company_by_symbol(snapshot, symbol)
        assert validate_citations(brief, company) == []
        assert disallowed_language(brief) == []
