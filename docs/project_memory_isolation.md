# Project Memory Detection and Isolation Strategy

## 1. Problem Statement

Jarvis-Termux AI currently maintains:

- Global persistent memory via `core/memory.py`
- Project memory loaded inside `core/context.py`
- History via `core/history.py`
- JSON storage utilities via `core/storage.py`

Current project detection in `ContextBuilder._detect_project()` is implemented as a simple `Path.cwd().name`, which:

- Fails for nested repositories
- Is not stable across symlinks
- Does not differentiate unrelated folders with same name
- Does not support configuration override

Project memory is stored as:

```
PROJECTS_DIR / f"{project_name}.json"
```

This is name-based and not collision-safe.

We must introduce a robust, deterministic, production-safe project isolation strategy without:

- Rewriting architecture
- Changing install.sh
- Breaking existing memory layout
- Losing any user data

Only additive and minimal structural refactors are permitted.

---

## 2. Constraints

1. Production-safe incremental refactor
2. No rewrites of existing modules
3. Backward compatible with:
   - Existing global memory file from `core/config.py`
   - Existing project JSON files in PROJECTS_DIR
4. Zero data loss
5. Deterministic behavior
6. No changes to CLI command surface

---

## 3. Proposed Project Detection Algorithm

Detection must be deterministic and hierarchical.

### 3.1 Resolution Order (Strict Priority)

1. Config Override
2. Git Root Detection
3. CWD Fingerprint

### 3.2 Algorithm Specification

Step 1: Config Override

If `CONFIG.project_override` exists and is non-empty:
- Use it directly as logical project identifier.
- Skip auto detection.

Step 2: Git Root Detection

Traverse upward from `Path.cwd()` until:
- A `.git` directory is found
- OR filesystem root is reached

If `.git` is found:
- Project root = directory containing `.git`
- Canonical path = resolved absolute path

Step 3: Fallback to CWD

If no git root:
- Project root = `Path.cwd().resolve()`

### 3.3 Stable Project Identifier

Identifier is computed as:

- Canonical absolute path
- Normalized path separators
- SHA256 hash of canonical path
- Use first 16 hex characters as project_id

Example:

```
/home/user/app -> 3f9a1c88ab72de19
```

This ensures:

- No name collision
- Stable per path
- Independent of directory name

---

## 4. Proposed Storage Layout

### 4.1 Current Layout (Preserved)

```
data/memory.json
PROJECTS_DIR/<project_name>.json
```

### 4.2 New Deterministic Layout

```
data/
  memory.json
  projects/
    <project_id>/
      memory.json
      metadata.json
```

Where:

- project_id = deterministic hash
- memory.json = project-scoped key/value store
- metadata.json =
  {
    "canonical_path": "...",
    "detected_via": "git|cwd|override",
    "created_at": timestamp
  }

### 4.3 Backward Compatibility Rule

If legacy file exists:

```
PROJECTS_DIR/<project_name>.json
```

It is treated as legacy format and loaded first.

On first write under new system:

- Migrate into new hashed directory
- Preserve original file as backup

---

## 5. Isolation Rules

1. Global memory remains untouched.
2. Project memory is resolved strictly via project_id.
3. No cross-project reads allowed.
4. History remains global unless future enhancement.
5. ContextBuilder must:
   - Load global memory
   - Load project-scoped memory via resolver

Isolation Guarantee:

Project A memory directory never overlaps Project B because identifier is path-hash based.

---

## 6. Migration Strategy (Zero Data Loss)

Migration is lazy and additive.

### 6.1 Detection of Legacy Layout

When loading project memory:

If:

```
PROJECTS_DIR/<project_name>.json exists
AND
new hashed directory does not exist
```

Then:

1. Load legacy JSON
2. Create hashed directory
3. Write memory.json
4. Create metadata.json
5. Rename original file to:
   <project_name>.legacy.bak

No deletion occurs.

### 6.2 Rollback Safety

Because original file is preserved:

- User can manually restore
- No destructive mutation occurs

---

## 7. Integration Plan

No rewrites. Only extensions.

### 7.1 New Utility Module

Create:

`core/project_resolver.py`

Responsibilities:

- detect_project_root()
- compute_project_id()
- resolve_project_directory()
- resolve_project_memory_file()
- migrate_legacy_if_needed()

### 7.2 Minimal Changes

Extend only:

1. `ContextBuilder._detect_project()` in `core/context.py`
   - Replace name-based detection with resolver call

2. `ContextBuilder._load_project_memory()` in `core/context.py`
   - Replace direct PROJECTS_DIR usage
   - Use resolver to get correct path

3. `MemoryManager` remains unchanged for global memory.

No changes required to:

- `core/storage.py`
- `core/history.py`
- CLI command interfaces

---

## 8. Risk Analysis

### 8.1 Hash Collision Risk

Using 16 hex chars from SHA256 yields extremely low collision probability.

Mitigation:

- metadata.json stores canonical path
- On load, verify canonical path matches

### 8.2 Git Root Mis-detection

If nested git repos exist:
- Nearest ancestor `.git` wins
- This matches developer expectation

### 8.3 Performance Impact

- Hash computation negligible
- Single directory traversal negligible

### 8.4 Migration Failure

If migration partially fails:
- Original legacy file remains intact
- System falls back safely

---

## 9. Validation Plan

### 9.1 Unit-Level Validation

Test cases:

1. Git repository project
2. Non-git directory project
3. Same folder name in different paths
4. Legacy project file present
5. Corrupted legacy file

### 9.2 Integration Validation

Verify:

- Global memory still loads
- Project memory isolation works
- CLI commands remember/forget operate correctly
- No modification required in command layer

### 9.3 Manual Validation Scenarios

Scenario A:
- Two git repos with same name in different parent paths
- Ensure memory does not overlap

Scenario B:
- Rename project directory
- New project_id generated
- Old memory remains intact

---

## 10. Summary of Architecture Change

We introduce:

- Deterministic project identification via canonical path hashing
- Hash-based directory isolation
- Lazy migration from legacy name-based files
- Zero destructive operations
- No rewrites
- Fully backward compatible

All changes are additive and localized to project resolution logic.

Global memory and existing architecture remain intact.
