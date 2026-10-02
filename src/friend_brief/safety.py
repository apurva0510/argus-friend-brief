from __future__ import annotations

import re

from friend_brief.citations import SECTION_NAMES
from friend_brief.models import Brief

DISALLOWED_PATTERNS = {
    "buy": re.compile(r"\bbuy(?:ing)?\b", re.IGNORECASE),
    "sell": re.compile(r"\bsell(?:ing)?\b", re.IGNORECASE),
    "hold": re.compile(r"\bhold(?:ing)?\b", re.IGNORECASE),
    "invest": re.compile(r"\binvest(?:ment|ing)?\b", re.IGNORECASE),
    "price target": re.compile(r"\bprice target\b", re.IGNORECASE),
    "guaranteed return": re.compile(r"\bguaranteed returns?\b", re.IGNORECASE),
    "position size": re.compile(r"\bposition siz(?:e|ing)\b", re.IGNORECASE),
}


def disallowed_language(brief: Brief) -> list[str]:
    # Limitations may contain explicit disclaimers such as "not an investment
    # recommendation". Guard the substantive briefing instead of the disclaimer.
    text_blocks = [brief.headline]
    for section_name in SECTION_NAMES:
        text_blocks.extend(claim.text for claim in getattr(brief, section_name))
    combined = "\n".join(text_blocks)
    return [name for name, pattern in DISALLOWED_PATTERNS.items() if pattern.search(combined)]
