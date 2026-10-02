from friend_brief.models import Brief, Claim
from friend_brief.safety import disallowed_language


def make_brief(text: str) -> Brief:
    return Brief(
        headline="Research update",
        what_changed=[Claim(text=text, evidence_ids=["VRT.E001"])],
        why_it_matters=[],
        bull_case=[],
        bear_case=[],
        watch_next=[],
        limitations=[],
    )


def test_neutral_research_language_passes():
    assert disallowed_language(make_brief("The reported return was positive.")) == []


def test_investment_direction_language_is_rejected():
    violations = disallowed_language(make_brief("This is a strong investment opportunity."))

    assert violations == ["invest"]
