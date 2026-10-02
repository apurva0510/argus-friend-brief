from friend_brief.briefing import generate_grounded_brief
from friend_brief.models import Brief, Claim, CompanySnapshot, EvidenceFact


class FakeClient:
    def __init__(self, responses: list[Brief]):
        self.responses = iter(responses)
        self.calls = 0

    def generate(self, _system_prompt: str, _user_prompt: str) -> Brief:
        self.calls += 1
        return next(self.responses)


def make_company() -> CompanySnapshot:
    return CompanySnapshot(
        symbol="VRT",
        name="Vertiv",
        facts=[
            EvidenceFact(
                id="VRT.metric.return_1d.2026-09-18",
                label="One-day return",
                value=0.02,
                display_value="+2.0%",
                as_of="2026-09-18",
                source="fixture",
            )
        ],
    )


def make_brief(evidence_id: str) -> Brief:
    return Brief(
        headline="Vertiv update",
        what_changed=[Claim(text="Vertiv rose two percent.", evidence_ids=[evidence_id])],
        why_it_matters=[],
        bull_case=[],
        bear_case=[],
        watch_next=[],
        limitations=[],
    )


def test_grounded_brief_returns_without_repair():
    client = FakeClient([make_brief("VRT.metric.return_1d.2026-09-18")])

    result = generate_grounded_brief(client, make_company(), "Plain English")

    assert result.headline == "Vertiv update"
    assert client.calls == 1


def test_invalid_citation_gets_one_repair_attempt():
    client = FakeClient(
        [
            make_brief("VRT.metric.fake.2026-09-18"),
            make_brief("VRT.metric.return_1d.2026-09-18"),
        ]
    )

    generate_grounded_brief(client, make_company(), "Plain English")

    assert client.calls == 2


def test_investment_language_gets_one_repair_attempt():
    unsafe = make_brief("VRT.metric.return_1d.2026-09-18")
    unsafe.what_changed[0].text = "This is an investment opportunity."
    client = FakeClient([unsafe, make_brief("VRT.metric.return_1d.2026-09-18")])

    generate_grounded_brief(client, make_company(), "Plain English")

    assert client.calls == 2
