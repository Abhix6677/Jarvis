from typing import Dict

from core.config import SUMMARY_FILE, CONFIG
from core.api import get_client
from core.storage import safe_load_json, atomic_write_json


class SummaryManager:
    def __init__(self):
        self.file_path = SUMMARY_FILE
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = get_client()
        return self._client

    def _load(self) -> Dict:
        return safe_load_json(self.file_path, {"summary": ""})

    def _save(self, data: Dict):
        atomic_write_json(self.file_path, data)

    def update_summary(self, history_messages):
        data = self._load()
        previous_summary = data.get("summary", "")

        prompt = [
            {
                "role": "system",
                "content": (
                    "You are maintaining a long-term evolving summary for an AI assistant. "
                    "Merge the previous summary with the new conversation. "
                    "Compress redundancies. Preserve important project details, stack, "
                    "environment, decisions, and unresolved issues."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Previous summary:\n{previous_summary}\n\n"
                    f"New conversation:\n{history_messages}"
                ),
            },
        ]

        summary_text = self.client.chat(
            prompt,
            temperature=CONFIG.summary_temperature,
        )

        data["summary"] = summary_text
        self._save(data)

        return summary_text

    def get_summary(self) -> str:
        data = self._load()
        return data.get("summary", "")
