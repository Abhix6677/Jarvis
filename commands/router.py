"""
Authoritative command routing layer.

This module provides a single public entrypoint:

    dispatch(argv: list[str]) -> int

Responsibilities:
- Lazily discover commands exactly once
- Parse CLI arguments
- Resolve command handlers via registry
- Execute handlers safely
- Return integer exit codes
- Provide clear error/help output

No side effects occur at import time.
"""

from typing import List

from commands.registry import get_command, list_commands
from commands.discovery import discover_commands


_DISCOVERED: bool = False


def _ensure_discovered() -> None:
    """Ensure command discovery runs exactly once."""
    global _DISCOVERED

    if not _DISCOVERED:
        discover_commands()
        _DISCOVERED = True


def _print_available_commands() -> None:
    """Print available registered commands."""
    commands = sorted(list_commands())

    if not commands:
        print("No commands available.")
        return

    print("Available commands:")
    for name in commands:
        print(f"  {name}")


def dispatch(argv: List[str]) -> int:
    """
    Dispatch a CLI invocation.

    Args:
        argv: List of CLI arguments excluding the program name.

    Returns:
        Integer exit code.
    """
    _ensure_discovered()

    # No command provided
    if not argv:
        _print_available_commands()
        return 1

    command_name = argv[0]
    args = argv[1:]

    meta = get_command(command_name)

    # Unknown command (silent fallback)
    if meta is None:
        return 1

    handler = meta.handler

    try:
        result = handler(args)
    except Exception as exc:
        print(f"Error while executing '{command_name}': {exc}")
        return 1

    # Normalize return value to int exit code
    if isinstance(result, int):
        return result

    # If handler returns None or non-int, treat as success
    return 0
