"""
Intent detection module.

Provides lightweight, regex-based natural language intent detection
with flexible, case-insensitive matching.

Public API:
    detect_and_store_intent(text: str, context: dict | None = None) -> dict | None

Design guarantees:
- No side effects at import time.
- Never raises on non-matching input.
- Returns structured intent dictionaries.
- Case-insensitive matching.
- Flexible polite/leading/trailing phrase handling.
"""

from __future__ import annotations

import re
from typing import Callable, Dict, Optional


# ---------------------------------------------------------------------------
# Regex Pattern Infrastructure
# ---------------------------------------------------------------------------

_POLITE_PREFIX = r"""
    ^\s*
    (?:
        (?:please|kindly|hey|hi|hello)\s+|
        (?:can|could|would|will)\s+you\s+|
        i\s+(?:want|need|would\s+like)\s+(?:you\s+to\s+)?
    )*
"""

_POLITE_SUFFIX = r"""
    (?:
        \s*(?:please)?
    )?\s*$
"""


def _compile(pattern: str) -> re.Pattern:
    """Compile regex with IGNORECASE and VERBOSE flags."""
    return re.compile(pattern, re.IGNORECASE | re.VERBOSE)


# Centralized intent pattern registry
# Each intent maps to a compiled regex with named capture groups.
# Simpler, permissive verb-based patterns (search, not strict prefix match)
_INTENT_PATTERNS: Dict[str, re.Pattern] = {
    "remember": re.compile(
        r"\b(?:remember|store|save|keep\s+track\s+of|yaad\s+rakh(?:o|na|\s+lo)?|yaad\s+rakho)\b\s*(?P<content>.+)?",
        re.IGNORECASE,
    ),
    "forget": re.compile(
        r"\b(?:forget|remove|delete|clear|bhool\s+jao|bhool\s+jaana)\b\s*(?P<content>.+)?",
        re.IGNORECASE,
    ),
    "recall": re.compile(
        r"\b(?:recall|what\s+do\s+you\s+know\s+about|what\s+did\s+i\s+say\s+about|what'?s\s+my|what\s+is\s+my|mera\s+naam\s+kya\s+hai)\b\s*(?P<content>.+)?",
        re.IGNORECASE,
    ),
    "status": re.compile(r"\b(?:status|current\s+status|what'?s\s+the\s+status)\b", re.IGNORECASE),
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect_and_store_intent(
    text: str, context: Optional[dict] = None
) -> Optional[str]:
    """
    Detect intent from natural language input and execute deterministic actions.

    Returns:
        A confirmation string if an intent is executed,
        or None if no intent matches.
    """
    if not isinstance(text, str) or not text.strip():
        return None

    from core.memory import MemoryManager

    normalized = text.strip()

    # Special-case implicit name declarations (English + Hindi)
    # Avoid treating questions like "mera naam kya hai" as save operations
    recall_hi_question = re.search(r"^mera\s+naam\s+kya\s+hai\??$", normalized, re.IGNORECASE)
    if recall_hi_question:
        from core.memory import MemoryManager
        stored = MemoryManager().format_for_prompt()
        return stored or "No stored memory found."

    implicit_name_en = re.search(r"^(?:my\s+)?name\s+(?:is\s+)?(.+)$", normalized, re.IGNORECASE)
    implicit_name_hi = re.search(r"^(?:mera\s+)?naam\s+(?!kya\b)(.+?)(?:\s+hai)?$", normalized, re.IGNORECASE)

    if implicit_name_en:
        from core.memory import MemoryManager
        value = implicit_name_en.group(1).strip()
        MemoryManager().remember("name", value)
        return f"Saved: name = {value}"

    if implicit_name_hi:
        from core.memory import MemoryManager
        value = implicit_name_hi.group(1).strip()
        MemoryManager().remember("name", value)
        return f"Saved: name = {value}"

    for intent_name, pattern in _INTENT_PATTERNS.items():
        try:
            match = pattern.search(normalized)
        except re.error:
            continue

        if not match:
            continue

        groupdict = match.groupdict()
        content = (groupdict.get("content") or "").strip()

        memory = MemoryManager()

        # ---------------- REMEMBER ----------------
        if intent_name == "remember":
            key = None
            value = None

            # key=value pattern
            if content and "=" in content:
                parts = content.split("=", 1)
                key = parts[0].strip()
                value = parts[1].strip()
            else:
                # English implicit: "my name is X" even without 'remember'
                full_text = normalized
                name_match = re.search(r"(?:my\s+)?name\s+(?:is\s+)?(.+)$", full_text, re.IGNORECASE)
                hindi_match = re.search(r"(?:mera\s+)?naam\s+(.+?)(?:\s+hai)?$", full_text, re.IGNORECASE)

                if name_match:
                    key = "name"
                    value = name_match.group(1).strip()
                elif hindi_match:
                    key = "name"
                    value = hindi_match.group(1).strip()
                elif content:
                    key = "note"
                    value = content

            if key and value:
                memory.remember(key, value)
                return f"Saved: {key} = {value}"

        # ---------------- FORGET ----------------
        if intent_name == "forget" and content:
            key = content.strip()
            memory.forget(key)
            return f"Removed: {key}"

        # ---------------- RECALL ----------------
        if intent_name == "recall" and content:
            stored = memory.format_for_prompt()
            return stored or "No stored memory found."

        # ---------------- STATUS ----------------
        if intent_name == "status":
            return "Jarvis is running."

    return None
