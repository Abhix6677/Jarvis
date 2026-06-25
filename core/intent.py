import re
from typing import Optional, Tuple
from core.memory import MemoryManager


NAME_PATTERNS = [
    r"mera naam ([A-Za-z]+) hai",
    r"mera naam ([A-Za-z]+) rakho",
    r"my name is ([A-Za-z]+)",
    r"i am ([A-Za-z]+)",
    r"call me ([A-Za-z]+)",
]


def detect_and_store_intent(user_input: str) -> Optional[str]:
    text = user_input.lower()
    for pattern in NAME_PATTERNS:
        match = re.search(pattern, text)
        if match:
            name = match.group(1).strip().capitalize()
            memory = MemoryManager()
            memory.remember("name", name)
            return f"✅ Yaad rakha. Aapka naam {name} hai."
    return None
