"""
Router abstraction layer for command dispatching.

Phase 3 (Non-Breaking, Not Yet Activated):
- Additive only
- Not wired into CLI
- Does not modify existing dispatch behavior
"""

from __future__ import annotations

import importlib
from typing import List

from core.intent import detect_and_store_intent
from commands.discovery import discover_commands
from commands.registry import (
    get_command,
    list_commands as registry_list_commands,
    mark_failed,
)


class CommandRouter:
    """
    Router abstraction for command dispatching.

    NOTE:
    - Not instantiated globally
    - Not integrated into jarvis.py
    - Fully non-breaking and additive
    """

    def __init__(self) -> None:
        self._initialized: bool = False

    def initialize(self) -> None:
        """
        Discover and register commands.

        Safe and idempotent.
        """
        if self._initialized:
            return

        discover_commands()
        self._initialized = True

    def dispatch(self, name: str, args: List[str]) -> int:
        """
        Dispatch a command by name.

        Behavior:
        - Lookup command in registry
        - Lazy import module if not yet loaded
        - Execute entrypoint safely
        - Return 0 on success, 1 on failure
        - No exceptions escape
        """
        try:
            self.initialize()

            metadata = get_command(name)
            if metadata is None:
                return 1

            # Lazy load module
            if not getattr(metadata, "loaded", False):
                try:
                    importlib.import_module(metadata.module_path)
                    metadata.loaded = True
                except Exception:
                    mark_failed(name)
                    return 1

            # Resolve entrypoint after import
            entrypoint = getattr(metadata, "entrypoint", None)
            if entrypoint is None:
                return 1

            try:
                # Lightweight intent detection before LLM dispatch
                joined = " ".join(args)
                intent_response = detect_and_store_intent(joined)
                if intent_response:
                    print(intent_response)
                    return 0

                result = entrypoint(args)
                return 0 if result is None or result == 0 else 1
            except Exception:
                return 1

        except Exception:
            return 1

    def list_commands(self) -> List[str]:
        """
        Return list of registered command names.
        """
        self.initialize()
        return registry_list_commands()
