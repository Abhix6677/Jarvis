from typing import List, Dict

from core.config import HISTORY_FILE, CONFIG
from core.storage import safe_load_json, atomic_write_json


class HistoryManager:
    def __init__(self):
        self.file_path = HISTORY_FILE

    def _load(self) -> List[Dict[str, str]]:
        return safe_load_json(self.file_path, [])

    def _save(self, history: List[Dict[str, str]]):
        atomic_write_json(self.file_path, history)

    def add(self, role: str, content: str):
        history = self._load()
        history.append({"role": role, "content": content})

        self._save(history)

    def get_context(self) -> List[Dict[str, str]]:
        history = self._load()
        return history[-CONFIG.history_limit:]

    def total_count(self) -> int:
        return len(self._load())

    def should_summarize(self) -> bool:
        return self.total_count() >= CONFIG.summary_trigger

    def clear(self):
        self._save([])
