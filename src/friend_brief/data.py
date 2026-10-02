from __future__ import annotations

import json
from pathlib import Path

from friend_brief.models import CompanySnapshot, Snapshot


def load_snapshot(path: str | Path) -> Snapshot:
    return Snapshot.model_validate_json(Path(path).read_text(encoding="utf-8"))


def company_by_symbol(snapshot: Snapshot, symbol: str) -> CompanySnapshot:
    normalized = symbol.strip().upper()
    for company in snapshot.companies:
        if company.symbol.upper() == normalized:
            return company
    raise KeyError(f"Company {normalized!r} is not present in the snapshot")


def evidence_catalog(company: CompanySnapshot) -> str:
    payload = [fact.model_dump(exclude_none=True) for fact in company.facts]
    return json.dumps(payload, indent=2, default=str)
