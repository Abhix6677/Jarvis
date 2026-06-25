from typing import List, Dict
from pathlib import Path

from core.config import CONFIG, PROJECTS_DIR
from core.history import HistoryManager
from core.summary import SummaryManager
from core.memory import MemoryManager
from core.storage import safe_load_json
from core.project_resolver import (
    detect_project_root,
    compute_project_id,
    resolve_project_directory,
    resolve_project_memory_file,
    migrate_legacy_if_needed,
)


class ContextBuilder:
    """Builds structured context for every AI request."""

    def __init__(self):
        self._history = None
        self._summary = None
        self._memory = None

    @property
    def history(self) -> HistoryManager:
        if self._history is None:
            try:
                self._history = HistoryManager()
            except Exception:
                self._history = HistoryManager()
        return self._history

    @property
    def summary(self) -> SummaryManager:
        if self._summary is None:
            try:
                self._summary = SummaryManager()
            except Exception:
                self._summary = SummaryManager()
        return self._summary

    @property
    def memory(self) -> MemoryManager:
        if self._memory is None:
            try:
                self._memory = MemoryManager()
            except Exception:
                self._memory = MemoryManager()
        return self._memory

    def _detect_project(self) -> str:
        try:
            root, _ = detect_project_root()
            return compute_project_id(root)
        except Exception:
            # Exceptional safeguard only
            return Path.cwd().name

    def _load_project_memory(self, project_id: str) -> str:
        try:
            project_dir = resolve_project_directory()
            migrate_legacy_if_needed(project_id, project_dir)
            project_file = resolve_project_memory_file()
        except Exception:
            # Exceptional safeguard only
            project_file = PROJECTS_DIR / f"{project_id}.json"

        data = safe_load_json(project_file, {})
        if not data:
            return ""
        return "\n".join(f"{k}: {v}" for k, v in data.items())

    def build(self, user_input: str) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = []

        # 1. System Prompt
        system_content = CONFIG.system_prompt

        # Enforce authoritative memory usage
        system_content += (
            "\n\nIMPORTANT: Persistent memory below contains authoritative facts about the user. "
            "If a fact (e.g., user's name) exists in persistent memory, you MUST use it "
            "unless the user explicitly changes it. Do not ignore stored identity facts."
        )

        # 2. Long-term summary
        long_summary = self.summary.get_summary()
        if long_summary:
            system_content += f"\n\nLong-term summary:\n{long_summary}"

        # 3. Persistent memory
        memory_block = self.memory.format_for_prompt()
        if memory_block:
            system_content += f"\n\nPersistent memory:\n{memory_block}"

        # 4. Project memory
        project_name = self._detect_project()
        project_memory = self._load_project_memory(project_name)
        if project_memory:
            system_content += f"\n\nProject memory ({project_name}):\n{project_memory}"

        messages.append({"role": "system", "content": system_content})

        # 5. Recent history
        messages.extend(self.history.get_context())

        # 6. Current prompt
        messages.append({"role": "user", "content": user_input})

        return messages
