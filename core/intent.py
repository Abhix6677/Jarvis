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

# Additional question patterns for recall that should NOT trigger saving
_RECALL_ONLY_PATTERNS = [
    re.compile(r"^what\s+is\s+my\s+(\w+)\??$", re.IGNORECASE),
    re.compile(r"^what'?s\s+my\s+(\w+)\??$", re.IGNORECASE),
    re.compile(r"^mera\s+([a-z]+)\s+kya\s+hai\??$", re.IGNORECASE),
]

# Question words that indicate we should NOT save
_QUESTION_WORDS = {"kya", "what", "which", "how", "why", "who", "where", "when", "?", "???"}


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
    memory = MemoryManager()

    normalized = text.strip()

    # Check if this is a recall-only question (should NOT trigger save)
    for pattern in _RECALL_ONLY_PATTERNS:
        if pattern.search(normalized):
            key_match = pattern.search(normalized)
            key = key_match.group(1).lower()
            data = memory.get_all()
            value = data.get(key)
            if value:
                return f"{key}: {value}"
            stored = memory.format_for_prompt()
            return stored or f"I don't have your {key} saved."

    # Generic key-value patterns - works WITHOUT "remember" keyword
    # Pattern: "my X is Y" or "my X name is Y" or "my X's name is Y"
    
    # Remove conversational prefixes (both English and Hindi)
    # Check name-specific patterns FIRST (highest priority)
    implicit_name_en = re.search(r"^(?:my\s+)?name\s+(?:is\s+)?(.+)$", normalized, re.IGNORECASE)
    implicit_name_hi = re.search(r"^(?:mera\s+)?naam\s+(?!kya\b)(.+?)(?:\s+hai)?$", normalized, re.IGNORECASE)

    if implicit_name_en:
        value = implicit_name_en.group(1).strip()
        memory.remember("name", value)
        return f"Saved: name = {value}"

    if implicit_name_hi:
        value = implicit_name_hi.group(1).strip()
        memory.remember("name", value)
        return f"Saved: name = {value}"

    cleaned = re.sub(r"^(?:okay\s+listen|listen|actually|also|btw|aur|ya|toh|accha|sun)\s*", "", normalized, flags=re.IGNORECASE)
    
    key = None
    value = None
    
    # Try English patterns
    # Pattern 1: "my X is Y" (simple like "my profession is student")
    kv_match = re.search(r"my\s+(\w+)\s+is\s+(.+)$", cleaned, re.IGNORECASE)
    if not kv_match:
        # Pattern 2: "my X name is Y" or "my X's name is Y" (like "my sister name is kiara")
        kv_match = re.search(r"my\s+(\w+)(?:'s)?\s+name\s+is\s+(.+)$", cleaned, re.IGNORECASE)
    
    if kv_match:
        key = kv_match.group(1).strip().lower()
        value = kv_match.group(2).strip()
    
    # Try Hindi patterns (generic only, not name)
    if not key:
        # Pattern: "mera X Y hai" or "meri X Y hai" (like "mera profession student hai")
        hindi_match = re.search(r"mer(?:a|i)\s+(?!naam\b)(\w+)\s+(.+?)(?:\s+hai\b)?$", cleaned, re.IGNORECASE)
        if hindi_match:
            key = hindi_match.group(1).strip().lower()
            value = hindi_match.group(2).strip()
    
    # Save if we found a valid key-value pair and it's not a question
    if key and value:
        first_word = value.lower().split()[0] if value.split() else ""
        if first_word not in _QUESTION_WORDS and "?" not in value:
            memory.remember(key, value)
            return f"Saved: {key} = {value}"

    # Process intent patterns (skip "remember" since we already handled it above)
    for intent_name, pattern in _INTENT_PATTERNS.items():
        # Skip remember intent - already handled by generic patterns above
        if intent_name == "remember":
            continue

        try:
            match = pattern.search(normalized)
        except re.error:
            continue

        if not match:
            continue

        groupdict = match.groupdict()
        content = (groupdict.get("content") or "").strip()

        # Re-instantiate memory for safety
        # ---------------- FORGET ----------------
        if intent_name == "forget" and content:
            key = content.strip()
            memory.forget(key)
            return f"Removed: {key}"

        # ---------------- RECALL ----------------
        if intent_name == "recall":
            # Try to extract specific key from question
            key_match = re.search(r"(?:my|mera)\s+(\w+)", normalized, re.IGNORECASE)
            if key_match:
                key = key_match.group(1).lower()
                data = memory.get_all()
                value = data.get(key)
                if value:
                    return f"{key}: {value}"
            stored = memory.format_for_prompt()
            return stored or "No stored memory found."

        # ---------------- STATUS ----------------
        if intent_name == "status":
            return "Jarvis is running."

    # ---------------- AUTO-FIX / PATCH REQUEST ----------------
    # Recognize user requests like "fix error", "auto-fix", "patch error <id>", or "fix last error"
    fix_match = re.search(r"\b(?:fix|auto-?fix|patch)\b(?:\s+error\s+(?P<id>err-[\w-]+|last))?", normalized, re.IGNORECASE)
    if fix_match:
        # Use the error registry in MemoryManager
        try:
            # Note: MemoryManager provides list_errors() and get_error()
            eid = (fix_match.group("id") or "last").strip()
            errors = memory.list_errors()
            if not errors:
                return "No recorded errors to fix."

            if eid == "last":
                entry = errors[-1]
            else:
                entry = memory.get_error(eid)
                if entry is None:
                    return f"No error found with id {eid}."

            # Build a concise prompt for the LLM to propose a minimal patch
            prompt = (
                f"You are a coding assistant. Propose a minimal patch (unified diff) and a short explanation to fix the following error.\n"
                f"File: {entry.get('file')}\n"
                f"Line: {entry.get('line')}\n"
                f"Stack/Trace:\n{entry.get('stack')}\n\n"
                "If you cannot determine a safe patch, explain why and suggest the next diagnostic steps."
            )

            from core.api import get_client

            client = get_client()
            try:
                suggestion = client.chat([{"role": "user", "content": prompt}], temperature=0.2)
            except Exception as e:
                return f"Auto-fix attempt failed while contacting LLM: {e}"

            # Save suggestion keyed by error id for later review/apply
            memory.remember(f"auto_fix:{entry.get('id')}", suggestion)
            return f"Auto-fix suggestion saved under key: auto_fix:{entry.get('id')}"
        except Exception as exc:
            return f"Auto-fix flow failed: {exc}"

    return None
