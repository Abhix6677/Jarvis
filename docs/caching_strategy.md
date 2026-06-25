# Safe In-Memory Caching Strategy

Authoritative design document for introducing safe, invocation-scoped caching without altering persistence semantics.

Strict Scope:
- No rewrites.
- No cross-session persistent caches.
- Disk remains source of truth.
- No Python implementation in this phase.

---

# 1. Current IO and API Call Flow Analysis

## 1.1 GPT API Flow

Entry point: GPT usage via `GPTClient` in core/api.py.

See: [`GPTClient`](../core/api.py:9)

Flow:
1. `GPTClient()` instantiated.
2. API key loaded via config.
3. `chat()` performs HTTP POST using `requests.post()`.
4. Retries handled inside `chat()` loop.

Characteristics:
- No session reuse.
- No connection pooling.
- New client typically created per command.
- No in-memory reuse boundary defined.

IO Type:
- Network IO.

Risk:
- Redundant instantiation overhead within same CLI invocation.

---

## 1.2 Context Build Flow

Entry point: [`ContextBuilder`](../core/context.py:18)

Method: [`ContextBuilder.build()`](../core/context.py:76)

Flow inside build():
1. Load system prompt from CONFIG.
2. `summary.get_summary()` → disk read.
3. `memory.format_for_prompt()` → disk read.
4. `_detect_project()` → filesystem traversal.
5. `_load_project_memory()` → JSON disk read.
6. `history.get_context()` → disk read.

IO Types:
- Multiple disk reads.
- JSON parsing.
- Filesystem traversal.

Characteristics:
- Each call re-reads disk.
- No per-build caching.
- No invocation-level memoization.

---

## 1.3 Memory and History Managers

Referenced from:
- [`core/history.py`](../core/history.py)
- [`core/memory.py`](../core/memory.py)

Observed Pattern:
- Managers encapsulate disk operations.
- No internal memoization boundary.
- Each call may re-read file.

---

## 1.4 Project Resolution

Functions used in:
- [`core/context.py`](../core/context.py:9)

Project detection path:
- detect_project_root
- compute_project_id
- resolve_project_directory
- resolve_project_memory_file

These perform:
- Filesystem traversal
- Hash/id computation
- Path resolution

Currently:
- No memoization per invocation.

---

# 2. Safe In-Memory Cache Boundaries

All caches MUST be:
- In-memory only
- Process-scoped
- Cleared on process exit
- Not serialized to disk

## 2.1 Invocation Boundary Definition

Invocation = single CLI execution process.

All caches live strictly inside process memory.
No global module-level mutable state that survives interpreter reuse (future-safe constraint).

---

## 2.2 GPTClient Reuse (Per Invocation)

Safe Boundary:
- One `GPTClient` instance per CLI invocation.

Scope:
- Shared within command execution chain.
- Not reused across subprocesses.

Reasoning:
- Stateless client except config and logger.
- Does not cache response content.
- Safe to reuse within same process.

Not Allowed:
- Response-level caching.
- Cross-session reuse.

---

## 2.3 History Cache (Per Context Build Cycle)

Boundary:
- Cache `history.get_context()` result during single `ContextBuilder.build()` call.

Scope:
- Valid only within single build execution.
- Invalidated immediately after build() returns.

Reasoning:
- Prevent duplicate disk reads if referenced multiple times.
- No risk of stale data within same build.

---

## 2.4 Memory Cache (Per Invocation)

Boundary:
- Cache formatted persistent memory string during invocation.

Rules:
- Cache only read operations.
- Any write must invalidate in-memory copy.

Reasoning:
- Disk remains authoritative.
- Writes immediately refresh cache.

---

## 2.5 Project Resolution Cache (Per Invocation)

Boundary:
- Cache mapping:
  cwd → project_id
  project_id → project_memory_file

Reasoning:
- Project identity stable during invocation.
- Eliminates repeated filesystem traversal.

Invalidation:
- None required within invocation.

---

# 3. Cache Invalidation Rules

Golden Rule:
Disk is always source of truth.

## 3.1 Invocation End

All caches destroyed when process exits.

## 3.2 Write Operations

Any command that writes to:
- memory
- history
- project memory

Must:
- Immediately invalidate corresponding in-memory cache.
- Never rely on stale snapshot.

## 3.3 No TTL

No time-based invalidation.
No background refresh.
No soft-expiry.

Strict lifecycle-based invalidation only.

---

# 4. Anti-Patterns to Avoid

❌ Global module-level dictionaries that persist across runs.
❌ Disk snapshots stored in `cache/` directory.
❌ Response caching of GPT outputs.
❌ Partial invalidation logic.
❌ Hidden implicit cache mutation.
❌ Lazy write-behind buffers.
❌ Multi-command shared static state.

Design Principle:
Deterministic behavior identical to no-cache mode.

---

# 5. Thread and Process Safety Considerations

Current System:
- Single-process CLI.
- No multi-threaded architecture.

Future-Safe Constraints:

## 5.1 Thread Safety

If threads introduced:
- Caches must be confined to invocation-scoped objects.
- Avoid module-level mutation.
- Prefer instance-level state.

## 5.2 Process Safety

Each CLI execution is separate OS process.

Guarantee:
- No shared memory between processes.
- No file locks altered.
- No new concurrency model introduced.

---

# 6. Incremental Rollout Plan

Phase 1 – GPTClient Reuse
- Introduce invocation-scoped singleton inside entrypoint.
- No behavioral change.

Phase 2 – Project Resolution Memoization
- Cache cwd → project_id mapping.
- Validate identical output.

Phase 3 – Memory Read Cache
- Cache formatted prompt string.
- Add invalidation on write.

Phase 4 – History Build Cache
- Cache history.get_context() within build().

After each phase:
- Validate deterministic output.
- Confirm no persistence semantic changes.

Rollback Strategy:
- Each phase isolated.
- Can disable cache via feature flag.

---

# 7. Verification Checklist

Before enabling caching by default:

Functional Verification:
- Identical prompts before/after caching.
- Identical disk writes.
- Identical GPT request payloads.

Safety Verification:
- No stale memory after write.
- No stale history after append.
- No project mis-resolution.

Failure Injection Tests:
- Simulate memory write mid-invocation.
- Simulate repeated context builds.
- Simulate different working directories.

Regression Guard:
- Run full CLI test suite with cache disabled and enabled.
- Diff outputs.

---

# 8. Architectural Summary

We introduce strictly bounded, invocation-scoped in-memory caches.

Properties:
- Zero persistence changes.
- Disk remains authoritative.
- Deterministic behavior.
- Incremental rollout.
- Fully reversible.

This design preserves the disk-as-source-of-truth model while reducing redundant IO and API object creation safely.
