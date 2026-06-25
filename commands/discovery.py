"""
Command discovery module.

Responsible for dynamically importing command modules within the
`commands` package and invoking their `register()` function if present.

This module does NOT perform discovery at import time. Discovery must be
explicitly triggered by calling `discover_commands()`.
"""

import importlib
import pkgutil
from types import ModuleType
from typing import Callable


# Modules that must NOT be auto-imported during discovery
_EXCLUDED_MODULES = {
    "__init__",
    "registry",
    "router",
    "discovery",
}


def _import_module(module_name: str) -> ModuleType:
    """
    Import a module from the commands package using an absolute import.

    Args:
        module_name: The short module name (without package prefix).

    Returns:
        The imported module.

    Raises:
        ImportError: If the module cannot be imported.
    """
    full_module_path = f"commands.{module_name}"

    try:
        return importlib.import_module(full_module_path)
    except Exception as exc:
        raise ImportError(
            f"Failed to import command module '{full_module_path}': {exc}"
        ) from exc


def _call_register(module: ModuleType) -> None:
    """
    Call the `register()` function of a module if it exists.

    Args:
        module: The imported module.

    Raises:
        RuntimeError: If `register` exists but is not callable.
        Exception: Propagates any exception raised by register().
    """
    register: Callable | None = getattr(module, "register", None)

    if register is None:
        return

    if not callable(register):
        raise RuntimeError(
            f"Module '{module.__name__}' has a 'register' attribute that is not callable."
        )

    try:
        register()
    except Exception as exc:
        raise RuntimeError(
            f"Error while registering commands from module '{module.__name__}': {exc}"
        ) from exc


def discover_commands() -> None:
    """
    Discover and register all command modules in the `commands` package.

    This function:
        - Iterates over modules in the commands package directory.
        - Skips internal modules (registry, router, discovery, __init__).
        - Dynamically imports each command module.
        - Calls its `register()` function if exposed.

    This function must be called explicitly. No discovery occurs at import time.
    """
    package_name = "commands"

    try:
        package = importlib.import_module(package_name)
    except Exception as exc:
        raise ImportError(
            f"Unable to import '{package_name}' package during discovery: {exc}"
        ) from exc

    if not hasattr(package, "__path__"):
        raise RuntimeError(
            f"Package '{package_name}' does not have a valid __path__ for module discovery."
        )

    for module_info in pkgutil.iter_modules(package.__path__):
        module_name = module_info.name

        if module_name in _EXCLUDED_MODULES:
            continue

        try:
            module = _import_module(module_name)
        except Exception as exc:
            print(f"[WARN] Skipping command module '{module_name}' due to import error: {exc}")
            continue

        try:
            _call_register(module)
        except Exception as exc:
            print(f"[WARN] Skipping registration for module '{module_name}': {exc}")
            continue
