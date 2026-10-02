from __future__ import annotations

from friend_brief.data import evidence_catalog
from friend_brief.models import Brief, CompanySnapshot

SYSTEM_PROMPT = """You are a careful research translator for a family stock-research workflow.
Use only the supplied evidence catalog. Do not use outside knowledge.
Every factual claim must cite one or more exact evidence IDs from the catalog.
Never invent a value, date, event, citation, price target, or recommendation.
Do not tell the reader to buy, sell, hold, or size a position.
Do not call a company or stock an investment opportunity.
An Argus "opportunity score" is only the name of an internal research-ranking signal;
do not interpret it as an expected return or an investment recommendation.
Do not mention evidence IDs in the prose because the interface renders them separately.
Check that every number and label in a claim matches its cited evidence exactly.
Use at most three evidence IDs per claim.
Explain uncertainty, stale data, and missing data plainly.
Balance positive and negative evidence.
Return only JSON matching the requested schema.
"""


def build_user_prompt(company: CompanySnapshot, explanation_level: str) -> str:
    schema = Brief.model_json_schema()
    return f"""Create a briefing for {company.name} ({company.symbol}).
Explanation level: {explanation_level}.

Focus on what changed, why it matters, the bull case, the bear case, and what evidence
the reader should monitor next. A change must compare matching evidence labels from
different dates; do not describe a current value by itself as a change.
If the catalog does not support a section, return an empty list and explain why in limitations.

Required JSON schema:
{schema}

Evidence catalog:
{evidence_catalog(company)}
"""


def build_repair_prompt(invalid_ids: list[str]) -> str:
    joined = ", ".join(sorted(set(invalid_ids)))
    return f"""Your response used evidence IDs that are not in the catalog: {joined}.
Return the complete JSON response again. Remove or replace every unsupported claim.
Use only exact evidence IDs from the supplied catalog. Return JSON only.
"""


def build_safety_repair_prompt(unsafe_phrases: list[str]) -> str:
    joined = ", ".join(sorted(set(unsafe_phrases)))
    return f"""Your response used disallowed investment-direction language: {joined}.
Return the complete JSON response again without recommendations, calls to action,
price targets, expected returns, or descriptions of the stock as an investment opportunity.
Describe only the supplied research evidence. Return JSON only.
"""
