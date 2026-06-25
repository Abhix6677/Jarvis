"""
Self-test command implementation per Phase 2A specification.
"""

import json
import os
import sys
import tempfile
import traceback
from typing import Any, Dict

from core.api import get_client
from core.memory import MemoryManager
from core.project_resolver import detect_project_root, compute_project_id
from commands.router import list_commands
from core.storage import safe_load_json, atomic_write_json
from core.logger import get_logger
from pathlib import Path


EXIT_OK = 0
EXIT_FAILURE = 1

logger = get_logger(__name__)


def _api_test() -> bool:
    try:
        # Test API connectivity with minimal request
        client = get_client()
        test_msg = [{"role": "user", "content": "test"}]
        response = client.chat(test_msg)
        return isinstance(response, str) and len(response) > 0
    except Exception:
        logger.exception("API connectivity test failed")
        return False


def _storage_test() -> bool:
    try:
        import tempfile
        # Test storage with temporary file
        test_dir = Path(tempfile.gettempdir())
        test_file = test_dir / "self_test_temp.json"
        test_value = {"status": "ok", "key": "value"}

        atomic_write_json(test_file, test_value)
        loaded = safe_load_json(test_file, None)
        test_file.unlink(missing_ok=True)

        return loaded == test_value
    except Exception:
        logger.exception("Storage test failed")
        return False


def _memory_test() -> bool:
    try:
        # Test memory operations
        mm = MemoryManager()
        test_key = "__self_test_temp__"
        test_value = "ping"

        mm.remember(test_key, test_value)
        loaded = mm.get_all().get(test_key)
        mm.forget(test_key)

        return loaded == test_value
    except Exception:
        logger.exception("Memory test failed")
        return False


def _router_test() -> bool:
    try:
        from commands.router import _ensure_discovered
        _ensure_discovered()
        commands = list_commands()
        return isinstance(commands, dict)
    except Exception:
        logger.exception("Router discoverability test failed")
        return False


def _project_resolver_test() -> bool:
    try:
        root, _ = detect_project_root()
        project_id = compute_project_id(root)
        return project_id is not None and len(project_id) > 0
    except Exception:
        logger.exception("Project resolver test failed")
        return False


def _run_all() -> Dict[str, bool]:
    return {
        "api": _api_test(),
        "storage": _storage_test(),
        "memory": _memory_test(),
        "router": _router_test(),
        "project_resolver": _project_resolver_test(),
    }


def run(args: list):
    logger.info("Starting self-test")

    json_mode = "--json" in args
    quiet_mode = "--quiet" in args

    results = _run_all()
    success = all(results.values())

    if json_mode:
        output = {
            "status": "ok" if success else "failure",
            "results": results,
        }
        print(json.dumps(output, sort_keys=True))
    elif not quiet_mode:
        for name in sorted(results.keys()):
            status = "OK" if results[name] else "FAIL"
            print(f"{name}: {status}")

        print("\nOverall:", "OK" if success else "FAIL")

    if success:
        logger.info("Self-test completed successfully")
        return EXIT_OK
    else:
        logger.error("Self-test failed")
        return EXIT_FAILURE
