from typing import Any, Dict, List


class ResponseParser:
    """
    Extracts only safe, user-visible assistant text from
    provider responses.

    Filters out:
    - tool calls
    - metadata
    - commentary
    - reasoning blocks
    - protocol tokens
    - structured JSON
    """

    @staticmethod
    def extract_text(content: str) -> str:
        if not isinstance(content, str):
            return ""

        lines = content.splitlines()
        cleaned: List[str] = []

        for line in lines:
            stripped = line.strip()

            # Filter internal protocol markers
            if not stripped:
                continue
            if stripped.lower() in {"bio", "commentary", "analysis"}:
                continue
            if stripped.startswith("to="):
                continue
            if stripped.startswith("{") and stripped.endswith("}"):
                continue
            if stripped.startswith("[") and stripped.endswith("]"):
                continue
            if stripped.startswith("json"):
                continue

            cleaned.append(line)

        return "\n".join(cleaned).strip()
