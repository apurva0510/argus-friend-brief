from __future__ import annotations

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
    user_prompt = build_user_prompt(company, explanation_level)
    brief = client.generate(SYSTEM_PROMPT, user_prompt)
    issues = validate_citations(brief, company)
    unsafe_phrases = disallowed_language(brief)
    if not issues and not unsafe_phrases:
        return brief

    invalid_ids = [evidence_id for issue in issues for evidence_id in issue.invalid_evidence_ids]
    repair_instructions = []
    if invalid_ids:
        repair_instructions.append(build_repair_prompt(invalid_ids))
    if unsafe_phrases:
        repair_instructions.append(build_safety_repair_prompt(unsafe_phrases))
    repaired = client.generate(SYSTEM_PROMPT, f"{user_prompt}\n\n{' '.join(repair_instructions)}")
    remaining = validate_citations(repaired, company)
    remaining_unsafe = disallowed_language(repaired)
    if remaining or remaining_unsafe:
        raise OllamaError(
            "The model returned unsupported citations or investment-direction language "
            "after one repair attempt."
        )
    return repaired
