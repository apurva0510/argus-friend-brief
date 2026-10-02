from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class EvidenceFact(BaseModel):
    id: str
    label: str
    value: Any = None
    display_value: str
    as_of: str | None = None
    source: str
    url: str | None = None


class CompanySnapshot(BaseModel):
    symbol: str
    name: str
    sector: str | None = None
    industry: str | None = None
    facts: list[EvidenceFact]


class Snapshot(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    generated_at: datetime
    source_label: str = "Argus read-only export"
    companies: list[CompanySnapshot]


class Claim(BaseModel):
    text: str = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1, max_length=3)


class Brief(BaseModel):
    headline: str = Field(min_length=1)
    what_changed: list[Claim]
    why_it_matters: list[Claim]
    bull_case: list[Claim]
    bear_case: list[Claim]
    watch_next: list[Claim]
    limitations: list[str]


class CitationIssue(BaseModel):
    section: str
    claim: str
    invalid_evidence_ids: list[str]
