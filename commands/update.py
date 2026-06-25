"""
Update command implementation per Phase 2A specification.
"""

import subprocess
from typing import Tuple

from core.logger import get_logger


EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_NOT_GIT = 2

logger = get_logger(__name__)


def _run_git(args) -> Tuple[int, str, str]:
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        logger.exception("Git subprocess execution failed")
        return 1, "", str(e)


def _is_git_repo() -> bool:
    code, out, _ = _run_git(["rev-parse", "--is-inside-work-tree"])
    return code == 0 and out.lower() == "true"


def _has_local_changes() -> bool:
    code, out, _ = _run_git(["status", "--porcelain"])
    return code == 0 and bool(out.strip())


def _is_detached_head() -> bool:
    code, _, _ = _run_git(["symbolic-ref", "--quiet", "HEAD"])
    return code != 0


def _current_short_hash() -> str:
    code, out, _ = _run_git(["rev-parse", "--short", "HEAD"])
    if code == 0:
        return out
    return "unknown"


def _fetch() -> bool:
    code, _, err = _run_git(["fetch", "--all", "--prune"])
    if code != 0:
        logger.error(f"Git fetch failed: {err}")
        return False
    return True


def _fast_forward_pull() -> bool:
    code, _, err = _run_git(["pull", "--ff-only"])
    if code != 0:
        logger.error(f"Git pull --ff-only failed: {err}")
        return False
    return True


def run(args: list):
    logger.info("Starting update command")

    check_mode = "--check" in args

    if not _is_git_repo():
        logger.warning("Not a git repository")
        print("Not a git repository.")
        return EXIT_NOT_GIT

    if _is_detached_head():
        logger.error("Detached HEAD state detected")
        print("Detached HEAD state. Aborting update.")
        return EXIT_FAILURE

    if _has_local_changes():
        logger.error("Local changes detected. Aborting update.")
        print("Local changes detected. Commit or stash before updating.")
        return EXIT_FAILURE

    current_hash = _current_short_hash()

    if not _fetch():
        return EXIT_FAILURE

    if check_mode:
        code, out, _ = _run_git(["rev-parse", "--short", "@{u}"])
        remote_hash = out if code == 0 else "unknown"
        print(f"Current: {current_hash}")
        print(f"Remote:  {remote_hash}")
        logger.info("Update check completed")
        return EXIT_OK

    if not _fast_forward_pull():
        return EXIT_FAILURE

    new_hash = _current_short_hash()

    print(f"Updated: {current_hash} -> {new_hash}")
    logger.info("Update completed successfully")
    return EXIT_OK
