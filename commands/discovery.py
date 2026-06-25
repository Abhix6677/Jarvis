"""
Command auto-discovery module.

This module provides a safe, isolated discovery mechanism for command
modules located in the `commands/` package. It does NOT modify CLI
dispatch behavior and must be invoked manually.
"""

from __future__ import annotations

import importlib
import pkgutil
from types import ModuleType
from typing import Optional

from commands.registry import CommandRegistry, CommandMetadata


# Files that must never be auto-discovered
_EXCLUDED_MODULES = {
    "__init__",
    "registry",
    "discovery",
}


def _safe_import(module_path: str) -> Optional[ModuleType]:
    """
    Safely import a module by path.

    Returns the imported module if successful, otherwise None.
    No exceptions are allowed to escape.
    """
    try:
        return importlib.import_module(module_path)
    except Exception:
        return None


def discover_commands() -> None:
    """
    Discover command modules inside the `commands` package and register
    them into the CommandRegistry.

    Behavior:
    - Scans the commands/ directory.
    - Ignores excluded modules.
    - Safely imports each module.
    - If module defines `run`, registers CommandMetadata.
    - If import fails, marks command as failed.
    - Idempotent: avoids duplicate registrations.
    - Never raises exceptions.

    NOTE: This function must be called manually. It is NOT executed at
    import time to preserve backward compatibility.
    """
    try:
        package = importlib.import_module("commands")

        for module_info in pkgutil.iter_modules(package.__path__):
            name = module_info.name

            if name in _EXCLUDED_MODULES:
                continue

            module_path = f"commands.{name}"

            # Idempotency check: skip if already registered
            if CommandRegistry.get(name) is not None:
                continue

            module = _safe_import(module_path)

            if module is None:
                try:
                    CommandRegistry.mark_failed(name, "Import failed")
                except Exception:
                    pass
                continue

            # Only register if module defines a callable `run`
            run_attr = getattr(module, "run", None)
            if callable(run_attr):
                metadata = CommandMetadata(
                    name=name,
                    module_path=module_path,
                    entrypoint="run",
                    description=getattr(module, "__doc__", None),
                    aliases=[],
                )

                try:
                    CommandRegistry.register(metadata)
                except Exception:
                    # Prevent any registry-level failure from escaping
                    pass
    except Exception:
        # Absolute safety: no exception may escape
        return
