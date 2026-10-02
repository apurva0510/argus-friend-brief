from __future__ import annotations

from friend_brief.models import Brief, CitationIssue, CompanySnapshot

SECTION_NAMES = (
    "what_changed",
    "why_it_matters",
    "bull_case",
    "bear_case",
    "watch_next",
)


def validate_citations(brief: Brief, company: CompanySnapshot) -> list[CitationIssue]:
    valid_ids = {fact.id for fact in company.facts}
    issues: list[CitationIssue] = []
    for section_name in SECTION_NAMES:
        for claim in getattr(brief, section_name):
            invalid = sorted(set(claim.evidence_ids) - valid_ids)
            if invalid:
                issues.append(
                    CitationIssue(
                        section=section_name,
                        claim=claim.text,
                        invalid_evidence_ids=invalid,
                    )
                )
    return issues


def cited_facts(brief: Brief, company: CompanySnapshot) -> dict[str, object]:
    facts = {fact.id: fact for fact in company.facts}
    cited_ids = {
        evidence_id
        for section_name in SECTION_NAMES
        for claim in getattr(brief, section_name)
        for evidence_id in claim.evidence_ids
    }
    return {evidence_id: facts[evidence_id] for evidence_id in cited_ids if evidence_id in facts}
