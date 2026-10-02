from datetime import UTC, datetime

import pytest

from friend_brief.data import company_by_symbol
from friend_brief.models import CompanySnapshot, Snapshot


def test_company_lookup_is_case_insensitive():
    snapshot = Snapshot(
        generated_at=datetime.now(UTC),
        companies=[CompanySnapshot(symbol="NVDA", name="NVIDIA", facts=[])],
    )

    assert company_by_symbol(snapshot, "nvda").name == "NVIDIA"


def test_company_lookup_rejects_missing_symbol():
    snapshot = Snapshot(generated_at=datetime.now(UTC), companies=[])

    with pytest.raises(KeyError):
        company_by_symbol(snapshot, "NVDA")
