import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Tuple

from core.config import PROJECTS_DIR, CONFIG

# Invocation-scoped memoization cache (Phase 3)
_cached_project_root = None
_cached_project_id = None
_cached_project_dir = None


def detect_project_root() -> Tuple[Path, str]:
    """
    Detect project root using strict priority:
    1) Config override
    2) Git root detection
    3) Fallback to CWD

    Returns:
        (canonical_root_path, detected_via)
    """

    global _cached_project_root

    if _cached_project_root is not None:
        return _cached_project_root

    # Step 1: Config Override
    override = getattr(CONFIG, "project_override", None)
    if override:
        root = Path(override).expanduser().resolve()
        _cached_project_root = (root, "override")
        return _cached_project_root

    # Step 2: Git Root Detection
    current = Path.cwd().resolve()

    for parent in [current] + list(current.parents):
        git_dir = parent / ".git"
        if git_dir.exists() and git_dir.is_dir():
            resolved = parent.resolve()
            _cached_project_root = (resolved, "git")
            return _cached_project_root

    # Step 3: Fallback to CWD
    _cached_project_root = (current, "cwd")
    return _cached_project_root


def compute_project_id(path: Path) -> str:
    """
    Compute deterministic project ID using SHA256 hash of
    canonical absolute path (normalized).
    Returns first 16 hex characters.
    """
    global _cached_project_root, _cached_project_id

    canonical = path.resolve()

    # Reuse cached project_id only when path matches detected root
    if (
        _cached_project_root is not None
        and _cached_project_id is not None
        and canonical == _cached_project_root[0]
    ):
        return _cached_project_id

    normalized = str(canonical).replace("\\", "/")
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    project_id = digest[:16]

    # Cache only if this corresponds to detected root
    if _cached_project_root is not None and canonical == _cached_project_root[0]:
        _cached_project_id = project_id

    return project_id


def resolve_project_directory() -> Path:
    """
    Resolve the deterministic hashed project directory path.
    Ensures base directory exists safely.
    """
    global _cached_project_dir

    if _cached_project_dir is not None:
        return _cached_project_dir

    root, _ = detect_project_root()
    project_id = compute_project_id(root)

    project_dir = PROJECTS_DIR / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    _cached_project_dir = project_dir
    return project_dir


def resolve_project_memory_file() -> Path:
    """
    Resolve path to project-scoped memory.json inside
    deterministic project directory.
    """
    project_dir = resolve_project_directory()
    return project_dir / "memory.json"


def migrate_legacy_if_needed(project_id: str, project_dir: Path) -> None:
    """
    Lazy non-destructive migration from legacy layout:

    If legacy file exists at:
        PROJECTS_DIR/<project_name>.json
    AND
        hashed directory does not exist

    Then:
        - Create hashed directory
        - Move content into memory.json
        - Create metadata.json
        - Rename legacy file to .legacy.bak

    Never deletes files. Idempotent.
    """

    # Determine legacy file based on current directory name
    cwd_name = Path.cwd().name
    legacy_file = PROJECTS_DIR / f"{cwd_name}.json"

    # If no legacy file, nothing to migrate
    if not legacy_file.exists() or not legacy_file.is_file():
        return

    # If new directory already initialized (memory.json exists), do nothing
    memory_file = project_dir / "memory.json"
    metadata_file = project_dir / "metadata.json"

    if memory_file.exists():
        return

    # Load legacy content safely
    try:
        with open(legacy_file, "r", encoding="utf-8") as f:
            legacy_data = json.load(f)
    except Exception:
        # If corrupted, do not modify anything
        return

    # Ensure project directory exists
    project_dir.mkdir(parents=True, exist_ok=True)

    # Write new memory.json
    with open(memory_file, "w", encoding="utf-8") as f:
        json.dump(legacy_data, f, indent=2)

    # Create metadata.json
    canonical_root, detected_via = detect_project_root()
    metadata = {
        "canonical_path": str(canonical_root.resolve()),
        "detected_via": detected_via,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }

    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    # Rename legacy file to backup
    backup_path = legacy_file.with_suffix(".legacy.bak")
    try:
        legacy_file.rename(backup_path)
    except Exception:
        # If rename fails, do not delete original
        pass
