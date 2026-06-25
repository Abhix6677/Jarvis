from typing import Dict, List, Any
from pathlib import Path
import time
import uuid

from core.config import MEMORY_FILE
from core.storage import safe_load_json, atomic_write_json


class MemoryManager:
    """Persistent key-value memory with a simple error registry.

    Errors are stored under the reserved key "__errors__" as a list of
    dictionaries with fields: id, timestamp, file, line, stack, summary.
    """

    def __init__(self):
        self.file_path = MEMORY_FILE

    def _load(self) -> Dict[str, Any]:
        return safe_load_json(self.file_path, {})

    def _save(self, data: Dict[str, Any]):
        atomic_write_json(self.file_path, data)

    # Basic KV operations
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

    def get_all(self) -> Dict[str, Any]:
        return self._load()

    def format_for_prompt(self) -> str:
        data = self._load()
        # Exclude internal error registry from formatted prompt
        display = {k: v for k, v in data.items() if k != "__errors__"}
        if not display:
            return ""
        lines = [f"{k}: {v}" for k, v in display.items()]
        return "\n".join(lines)

    # Error registry helpers
    def remember_error(self, file: str, line: int, stack: str, summary: str | None = None) -> str:
        """Record an error with metadata and return the generated error id."""
        data = self._load()
        errors: List[Dict[str, Any]] = data.get("__errors__", [])
        eid = f"err-{int(time.time())}-{uuid.uuid4().hex[:6]}"
        entry: Dict[str, Any] = {
            "id": eid,
            "timestamp": int(time.time()),
            "file": file,
            "line": int(line) if line is not None else None,
            "stack": stack,
            "summary": summary or "",
        }
        errors.append(entry)
        data["__errors__"] = errors
        self._save(data)
        return eid

    def list_errors(self) -> List[Dict[str, Any]]:
        data = self._load()
        return data.get("__errors__", [])

    def get_error(self, error_id: str) -> Dict[str, Any] | None:
        for e in self.list_errors():
            if e.get("id") == error_id:
                return e
        return None

    def clear_errors(self) -> None:
        data = self._load()
        if "__errors__" in data:
            data["__errors__"] = []
            self._save(data)
