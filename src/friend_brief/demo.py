from __future__ import annotations

import json
from pathlib import Path

from friend_brief.models import Brief


def load_demo_briefs(path: str | Path) -> dict[str, Brief]:
    demo_path = Path(path)
    if not demo_path.exists():
        return {}
    payload = json.loads(demo_path.read_text(encoding="utf-8"))
    return {
        symbol.upper(): Brief.model_validate(brief)
        for symbol, brief in payload.get("briefs", {}).items()
    }
