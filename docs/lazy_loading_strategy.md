# Lazy Loading Strategy for Core Managers

Authoritative design document for safe, incremental lazy loading of heavy internal managers.

Scope: Documentation only. No implementation changes in this phase.

---

# 1. Current Initialization Flow Analysis

## 1.1 Entry Point

Application starts in `jarvis.py` via [`main()`](jarvis.py:48).

Execution path:

1. [`ensure_directories()`](core/config.py:1) (import side-effect already resolved at import time)
2. CLI parsing
3. [`chat()`](jarvis.py:20)

Inside [`chat()`](jarvis.py:20):

- `client = GPTClient()`
- `history = HistoryManager()`
- `summary = SummaryManager()`
- `context_builder = ContextBuilder()`
- `messages = context_builder.build()`
- `client.chat()`

## 1.2 Object Graph During Chat

Current eager construction chain:

- [`GPTClient`](core/api.py:9)
- [`HistoryManager`](core/history.py:7)
- [`SummaryManager`](core/summary.py:8)
    - internally constructs `GPTClient`
- [`ContextBuilder`](core/context.py:18)
    - constructs `HistoryManager`
    - constructs `SummaryManager`
    - constructs `MemoryManager`

This results in:

- Multiple `GPTClient` instances per request
- Multiple file-backed managers instantiated even if not used
- Summary client constructed even if summarization not triggered

---

# 2. Identification of Heavy Objects

## 2.1 API Client

Defined in [`GPTClient`](core/api.py:9)

Heavy characteristics:
- Reads API key
- Builds logger
- Performs network calls
- May retry with timeout logic

Primary cost: network and retry loop.
Construction cost: low–moderate.
Usage frequency: high.

## 2.2 SummaryManager

Defined in [`SummaryManager`](core/summary.py:8)

Heavy characteristics:
- Constructs `GPTClient` eagerly
- Performs LLM call during `update_summary`

Critical issue:
- Client constructed even when summarization is not triggered.

## 2.3 ContextBuilder

Defined in [`ContextBuilder`](core/context.py:18)

Heavy characteristics:
- Constructs 3 managers in `__init__`
- Performs project detection
- Loads project memory from disk
- Loads history
- Loads summary

Construction cost: moderate.
Execution cost: disk IO heavy.

## 2.4 MemoryManager

Defined in [`MemoryManager`](core/memory.py:7)

Heavy characteristics:
- Repeated disk reads per method call.

Construction cost: trivial.
Operational cost: IO per call.

## 2.5 HistoryManager

Defined in [`HistoryManager`](core/history.py:7)

Heavy characteristics:
- Repeated disk IO
- Trigger logic for summarization

Construction cost: trivial.
Operational cost: IO per call.

---

# 3. Lazy Instantiation Pattern Options

We evaluate three patterns.

## 3.1 Property-Based Lazy Initialization

Pattern:

- Object stored as `_instance = None`
- Created inside `@property`
- First access triggers construction

Advantages:
- Minimal architectural change
- Preserves public interface
- No import relocation required
- No circular import risk

Risks:
- Not thread-safe unless guarded

Use Cases:
- ContextBuilder internal managers
- SummaryManager internal client


## 3.2 Factory Wrapper

Pattern:

- Replace direct construction with `get_manager()` factory
- Factory caches instance

Advantages:
- Explicit lifecycle control
- Centralized caching

Risks:
- Changes import expectations
- Harder to retrofit without touching call sites

Rejected for now due to "No rewrites" constraint.


## 3.3 Singleton with Deferred Construction

Pattern:

- Module-level `_instance`
- `get_instance()` constructs on first call

Advantages:
- Eliminates duplicate heavy clients
- Production-safe

Risks:
- Hidden global state
- Test complexity

Use Cases:
- GPTClient (shared)


# 4. Selected Strategy Per Component

## 4.1 GPTClient

Strategy:
- Deferred singleton using module-level cache.
- Instance constructed only when first `chat()` call occurs.

Effect:
- Prevent multiple clients per request.
- Prevent SummaryManager from constructing its own client.

Public interface preserved:
- `GPTClient()` remains callable.

Implementation strategy (future):
- Internally delegate to shared instance.


## 4.2 SummaryManager

Strategy:
- Remove eager client construction.
- Convert `self.client` into lazy property.

Client created only when:
- `update_summary()` is called.

No behavior change externally.


## 4.3 ContextBuilder

Strategy:
- Convert `history`, `summary`, `memory` into lazy properties.

Current:
- Instantiated in `__init__`

Future:
- `self._history = None`
- `@property def history()` constructs lazily.

Heavy project detection remains inside `build()`.


## 4.4 MemoryManager

No constructor laziness required.

Instead:
- Cache loaded memory per build cycle only.
- Do NOT convert to global singleton.

Reason:
- Memory updates must remain consistent across commands.


## 4.5 HistoryManager

No constructor laziness needed.

Optional improvement:
- In-memory cache within single request scope.
- Never persist across processes.


# 5. Thread-Safety Considerations

Current system:
- CLI single-process
- No multi-threading

However design must be safe if future parallelization occurs.

Guidelines:

1. Singleton GPTClient must use:
   - Double-checked locking OR
   - Module import atomicity

2. Lazy properties must:
   - Avoid partial construction states

3. Disk IO remains atomic via [`atomic_write_json()`](core/storage.py:1)

Concurrency assumptions:
- Single-process primary
- No shared memory across processes


# 6. Caching Boundary Definition

## 6.1 Safe to Cache

Within a single request:

- GPTClient instance
- History loaded list
- Memory loaded dict
- Summary text

## 6.2 Must NOT Cache Globally

Across requests:

- History content
- Memory content
- Project memory file

Reason:
- External commands may mutate files.

## 6.3 Summary Cache

Summary file content may be cached within request only.

Never hold in-memory across CLI invocations.


# 7. Rollout Plan (Incremental and Safe)

Phase 1 – SummaryManager Safe Laziness
- Convert client to lazy property.
- No external change.
- Verify summarization trigger path.

Phase 2 – ContextBuilder Internal Laziness
- Convert internal managers to lazy properties.
- Validate identical message output.

Phase 3 – GPTClient Shared Instance
- Introduce deferred singleton internally.
- Ensure backward compatibility.

Phase 4 – Optional Request-Level Caching
- Add internal caching within build().
- Verify no persistence beyond request.

Each phase:
- Independent
- Reversible
- Minimal diff


# 8. Regression Risk Analysis

## 8.1 Circular Import Risk

Mitigation:
- No new imports introduced.
- Lazy logic contained inside classes.

## 8.2 Behavioral Drift

Risk:
- Summary not triggered properly.

Mitigation:
- Validate against [`HistoryManager.should_summarize()`](core/history.py:30)

## 8.3 Hidden Shared State

Risk:
- Singleton misuse across commands.

Mitigation:
- Restrict singleton to stateless API client only.

## 8.4 Disk Consistency

No change to file write semantics.


# 9. Final Architecture Summary

After implementation:

- No manager eagerly constructs heavy dependencies.
- Summary client created only when summarization occurs.
- ContextBuilder builds only required components.
- GPTClient instantiated once per process.
- No public API changes.
- No rewrites.
- No circular imports.
- Production-safe incremental rollout.

This document is the authoritative reference for implementation.