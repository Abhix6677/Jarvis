"""
Self-test command implementation per Phase 2A specification.
"""

import json
import os
import sys
import tempfile
import traceback
from typing import Any, Dict

from core import api
from core import memory
from core import project_resolver
from core import router
from core import storage
from core.logger import get_logger


EXIT_OK = 0
EXIT_FAILURE = 1

logger = get_logger(__name__)


def _api_test() -> bool:
    try:
        # Non-persistent connectivity check
        api.ping()
        return True
    except Exception:
        logger.exception("API connectivity test failed")
        return False


def _storage_test() -> bool:
    try:
        test_key = "self_test_temp_key"
        test_value = {"status": "ok"}

        storage.save_cache(test_key, test_value)
        loaded = storage.load_cache(test_key)
        storage.delete_cache(test_key)

        return loaded == test_value
    except Exception:
        logger.exception("Storage test failed")
        return False


def _memory_test() -> bool:
    try:
        namespace = "__self_test_namespace__"
        test_data = {"ping": "pong"}

        memory.save(namespace, test_data)
        loaded = memory.load(namespace)
        memory.delete(namespace)

        return loaded == test_data
    except Exception:
        logger.exception("Memory test failed")
        return False


def _router_test() -> bool:
    try:
        commands = router.discover_commands()
        return isinstance(commands, dict)
    except Exception:
        logger.exception("Router discoverability test failed")
        return False


def _project_resolver_test() -> bool:
    try:
        path = project_resolver.resolve_project_root(os.getcwd())
        return path is not None
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
