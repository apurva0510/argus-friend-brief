from friend_brief.citations import validate_citations
from friend_brief.models import Brief, Claim, CompanySnapshot, EvidenceFact


def company() -> CompanySnapshot:
    return CompanySnapshot(
        symbol="NVDA",
        name="NVIDIA",
        facts=[
            EvidenceFact(
                id="NVDA.metric.return_1d.2026-09-18",
                label="One-day return",
                value=0.01,
                display_value="+1.0%",
                as_of="2026-09-18",
                source="fixture",
            )
        ],
    )


def brief(evidence_id: str) -> Brief:
    claim = Claim(text="The stock rose one percent.", evidence_ids=[evidence_id])
    return Brief(
        headline="A measured move",
        what_changed=[claim],
        why_it_matters=[],
        bull_case=[],
        bear_case=[],
        watch_next=[],
        limitations=[],
    )


def test_valid_citations_pass():
    assert validate_citations(brief("NVDA.metric.return_1d.2026-09-18"), company()) == []


def test_unknown_citations_are_reported():
    issues = validate_citations(brief("NVDA.metric.made_up.2026-09-18"), company())

    assert len(issues) == 1
    assert issues[0].invalid_evidence_ids == ["NVDA.metric.made_up.2026-09-18"]
