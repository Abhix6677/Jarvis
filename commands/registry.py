"""
Authoritative command registry for Jarvis CLI.

This module provides a singleton-backed registry with a clean,
consistent API surface. It is intentionally self-contained to avoid
circular imports and side effects at import time.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Callable, Dict


@dataclass(frozen=True)
class CommandMeta:
    """Metadata container for a registered command."""

    name: str
    handler: Callable
    description: str = ""


class _CommandRegistry:
    """
    Internal singleton registry implementation.

    This class should not be used directly outside this module.
    Use the module-level helper functions instead.
    """

    def __init__(self) -> None:
        self._commands: Dict[str, CommandMeta] = {}
        self._lock = RLock()

    @staticmethod
    def _normalize(name: str) -> str:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Command name must be a non-empty string.")
        return name.strip().lower()

    def register_command(
        self,
        name: str,
        handler: Callable,
        description: str = "",
    ) -> None:
        key = self._normalize(name)

        if not callable(handler):
            raise ValueError(f"Handler for command '{name}' must be callable.")

        with self._lock:
            if key in self._commands:
                raise ValueError(f"Command '{name}' is already registered.")

            self._commands[key] = CommandMeta(
                name=key,
                handler=handler,
                description=description or "",
            )

    def get_command(self, name: str) -> CommandMeta | None:
        key = self._normalize(name)
        with self._lock:
            return self._commands.get(key)

    def list_commands(self) -> Dict[str, CommandMeta]:
        with self._lock:
            # Return a shallow copy to prevent external mutation
            return dict(self._commands)


# --- Singleton instance (module-internal) ---

_registry = _CommandRegistry()


# --- Public module-level API ---


def register_command(name: str, handler: Callable, description: str = "") -> None:
    """
    Register a command with the global registry.

    :param name: Command name (case-insensitive).
    :param handler: Callable that executes the command.
    :param description: Optional human-readable description.
    :raises ValueError: If the command already exists or inputs are invalid.
    """
    _registry.register_command(name=name, handler=handler, description=description)


def get_command(name: str) -> CommandMeta | None:
    """
    Retrieve a command by name (case-insensitive).

    :param name: Command name.
    :return: CommandMeta if found, else None.
    """
    return _registry.get_command(name)


def list_commands() -> Dict[str, CommandMeta]:
    """
    List all registered commands.

    :return: Dictionary mapping normalized command names to CommandMeta.
    """
    return _registry.list_commands()
