from __future__ import annotations

import sentry_sdk

from friend_brief.citations import validate_citations
from friend_brief.models import Brief, CompanySnapshot
from friend_brief.ollama_client import OllamaClient, OllamaError
from friend_brief.prompts import (
    SYSTEM_PROMPT,
    build_repair_prompt,
    build_safety_repair_prompt,
    build_user_prompt,
)
from friend_brief.safety import disallowed_language


def generate_grounded_brief(
    client: OllamaClient,
    company: CompanySnapshot,
    explanation_level: str,
) -> Brief:
    with sentry_sdk.start_transaction(op="ai.pipeline", name="generate grounded brief") as trace:
        trace.set_data("argus.explanation_level", explanation_level)
        trace.set_data("argus.evidence_count", len(company.facts))
        trace.set_data("gen_ai.request.model", getattr(client, "model", "unknown"))

        user_prompt = build_user_prompt(company, explanation_level)
        brief = client.generate(SYSTEM_PROMPT, user_prompt)
        with sentry_sdk.start_span(op="ai.guardrail", name="validate generated brief") as span:
            issues = validate_citations(brief, company)
            unsafe_phrases = disallowed_language(brief)
            span.set_data("argus.invalid_citation_count", len(issues))
            span.set_data("argus.unsafe_phrase_count", len(unsafe_phrases))
        if not issues and not unsafe_phrases:
            trace.set_data("argus.repair_attempted", False)
            trace.set_status("ok")
            return brief

        trace.set_data("argus.repair_attempted", True)
        invalid_ids = [
            evidence_id for issue in issues for evidence_id in issue.invalid_evidence_ids
        ]
        repair_instructions = []
        if invalid_ids:
            repair_instructions.append(build_repair_prompt(invalid_ids))
        if unsafe_phrases:
            repair_instructions.append(build_safety_repair_prompt(unsafe_phrases))
        repaired = client.generate(
            SYSTEM_PROMPT, f"{user_prompt}\n\n{' '.join(repair_instructions)}"
        )
        with sentry_sdk.start_span(op="ai.guardrail", name="validate repaired brief") as span:
            remaining = validate_citations(repaired, company)
            remaining_unsafe = disallowed_language(repaired)
            span.set_data("argus.invalid_citation_count", len(remaining))
            span.set_data("argus.unsafe_phrase_count", len(remaining_unsafe))
        if remaining or remaining_unsafe:
            trace.set_status("internal_error")
            raise OllamaError(
                "The model returned unsupported citations or investment-direction language "
                "after one repair attempt."
            )
        trace.set_status("ok")
        return repaired
