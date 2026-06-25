from typing import Dict

from core.config import MEMORY_FILE
from core.storage import safe_load_json, atomic_write_json


class MemoryManager:
    def __init__(self):
        self.file_path = MEMORY_FILE

    def _load(self) -> Dict:
        return safe_load_json(self.file_path, {})

    def _save(self, data: Dict):
        atomic_write_json(self.file_path, data)

    def remember(self, key: str, value: str):
        data = self._load()
        data[key] = value
        self._save(data)

    def forget(self, key: str):
        data = self._load()
        if key in data:
            del data[key]
            self._save(data)

    def clear(self):
        self._save({})

    def get_all(self) -> Dict:
        return self._load()

    def format_for_prompt(self) -> str:
        data = self._load()
        if not data:
            return ""
        lines = [f"{k}: {v}" for k, v in data.items()]
        return "\n".join(lines)
