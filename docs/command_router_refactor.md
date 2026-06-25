# Command Router Refactor Design

## 1. Current Architecture Analysis

### CLI Entry Point
Primary entrypoint: [`main()`](../jarvis.py:48)

Flow:

```
ai <args>
  -> main()
     -> ensure_directories()
     -> argparse parse
     -> chat(user_input)
```

Current behavior in [`jarvis.py`](../jarvis.py):
- No dynamic command routing.
- Single freeform AI chat pathway.
- Commands likely invoked externally or through separate mechanism (existing modules inside [`commands/`](../commands)).

### Commands Package Structure

Existing command modules:

- [`commands/remember.py`](../commands/remember.py)
- [`commands/forget.py`](../commands/forget.py)
- [`commands/memory.py`](../commands/memory.py)
- [`commands/shell.py`](../commands/shell.py)
- [`commands/doctor.py`](../commands/doctor.py)
- [`commands/status.py`](../commands/status.py)
- [`commands/diff.py`](../commands/diff.py)
- [`commands/commit.py`](../commands/commit.py)
- [`commands/push.py`](../commands/push.py)

Observed pattern (example: [`run()`](../commands/remember.py:4)):

```
def run(args: list):
    ...
```

Invariant Constraints:
- Command entrypoint function is `run(args: list)`.
- Each module is self-contained.
- No shared registry exists.
- No metadata definition standard.

---

## 2. Target Architecture Overview

### High-Level Goals

- Remove hardcoded routing
- Commands self-register
- Auto-discover modules
- Safe failure isolation
- Backward-compatible invocation
- Lazy-load ready

---

## 3. Target Architecture Diagram

```
+-------------------+
|       jarvis      |
|  CLI Entrypoint   |
+---------+---------+
          |
          v
+-------------------+
|  Command Router   |
|  dispatch(name)   |
+---------+---------+
          |
          v
+----------------------------+
|      Command Registry      |
|  name -> CommandMetadata   |
+----------------------------+
          |
          v
+----------------------------+
|   commands package loader  |
|  dynamic discovery import  |
+----------------------------+
          |
          v
+----------------------------+
|  Individual Command Module |
|  run(args)                 |
+----------------------------+
```

---

## 4. Registration Mechanism Design

### Core Concept

Introduce a central registry module (future file):

`commands/registry.py`

### Command Metadata Model

Proposed structure:

```
class CommandMetadata:
    name: str
    description: str
    module_path: str
    entrypoint: Callable
    aliases: list[str]
```

### Decorator-Based Registration

Command modules optionally define:

```
@command(
    name="remember",
    description="Store a key-value memory",
    aliases=[]
)
def run(args: list):
    ...
```

Decorator behavior:
- Validate signature
- Register metadata in global registry
- Store lazy import reference

Backward compatibility:
- If decorator missing, fallback to implicit registration by filename.

---

## 5. Automatic Discovery Strategy

### Discovery Mechanism

At startup:

1. Scan `commands/` directory
2. Ignore:
   - `__init__.py`
   - `registry.py`
3. Collect `*.py` modules
4. Import modules safely

Implementation Strategy (future):

- Use `importlib`
- Wrap each import in try/except
- On failure:
  - Log error
  - Skip module
  - Continue boot

### Safe Import Wrapper

```
try:
    import module
except Exception:
    logger.error
    registry.mark_failed
```

Failure does not stop CLI.

---

## 6. Backward Compatibility Layer

### Requirement

Existing invocation must work unchanged.

### Compatibility Rules

1. If registry exists → use registry dispatch
2. If registry empty → fallback to legacy dispatch
3. Command invocation contract remains:

```
run(args: list)
```

4. No modification to existing command modules required.

### Filename-Based Implicit Registration

If module has no decorator:

- Command name = filename
- Entrypoint = `run`
- Description = None

This preserves all existing behavior.

---

## 7. Failure Isolation Strategy

### Import-Time Isolation

Each command module imported independently.

Failure policy:
- Catch all exceptions
- Log stack trace
- Continue loading remaining modules

### Runtime Isolation

When executing command:

```
try:
    command.entrypoint(args)
except Exception:
    log
    print user-safe error
```

Failure of one command:
- Must not crash router
- Must not crash CLI process

---

## 8. Lazy Loading Hook Points

### Current Design Preparation

Registry stores:

- module path (string)
- not module object

Future optimization:

Instead of importing all modules at startup:

1. Registry stores module path only
2. On first dispatch:
   - Dynamically import
   - Cache module

Lazy-ready abstraction:

```
def get_entrypoint(command_name):
    if not loaded:
        import module
    return run
```

Design ensures no structural rewrite required later.

---

## 9. Incremental Migration Plan

### Phase 1 – Introduce Registry (No Behavior Change)

- Create `commands/registry.py`
- Add registry data structure
- No CLI integration

### Phase 2 – Add Discovery Layer

- Implement safe discovery
- Log loaded commands
- Do not replace routing yet

### Phase 3 – Integrate Router Behind Feature Flag

- Add router module
- Keep legacy routing
- Switch based on flag

### Phase 4 – Enable Decorator Registration

- Optional metadata decorator
- Existing commands untouched

### Phase 5 – Default to Dynamic Dispatch

- Remove legacy hardcoded table
- Keep compatibility fallback

### Phase 6 – Lazy Loading Optimization

- Convert eager imports to deferred imports

Each phase independently deployable.

---

## 10. Validation Checklist

### Structural

- [ ] All existing commands execute unchanged
- [ ] CLI arguments preserved
- [ ] No signature changes

### Safety

- [ ] Broken command does not stop CLI
- [ ] Import errors logged
- [ ] Runtime errors isolated

### Compatibility

- [ ] Commands without decorator auto-register
- [ ] Aliases resolve correctly

### Performance

- [ ] Startup time not increased significantly
- [ ] Lazy-loading hook verified

---

## 11. Final Architecture Summary

The new command system introduces:

- A centralized registry abstraction
- Decorator-based optional metadata
- Automatic safe discovery
- Filename fallback registration
- Import-time and runtime failure isolation
- Lazy-loading-ready dispatch layer

This refactor:

- Preserves all existing command modules
- Preserves `run(args: list)` signature
- Avoids rewrites
- Enables future performance and plugin expansion
- Allows production-safe incremental rollout

This document is the authoritative reference for implementing the modular command router refactor.