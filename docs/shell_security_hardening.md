# Shell Execution Hardening Strategy

Authoritative reference for hardening [`commands/shell.py`](../commands/shell.py)
Scope: Design only. No implementation changes in this document.

---

# 1. Current Execution Flow Analysis

Reference implementation: [`run()`](../commands/shell.py:5)

## 1.1 Flow Summary

1. CLI passes `args: list` into `run()`.
2. Args are joined into a single string:
   - `raw_command = " ".join(args)`
3. User confirmation prompt:
   - `About to execute: <raw_command>`
   - Requires explicit `y` confirmation.
4. Execution performed via:
   - `subprocess.run(shlex.split(raw_command), capture_output=True, text=True)`
5. STDOUT and STDERR printed directly.
6. Exceptions caught and printed.

## 1.2 Important Observations

- Uses `shell=False` implicitly because argument list is passed.
- Uses `shlex.split()` which performs POSIX-style parsing.
- No timeout enforcement.
- No command classification or validation.
- No output size limits.
- Full inherited environment.
- No process group isolation.
- No working directory restriction.

## 1.3 Security Posture Today

Strengths:
- No direct shell=True injection surface.
- Explicit confirmation step.

Weaknesses:
- Arbitrary command execution allowed.
- No timeout.
- No resource limits.
- No denylist.
- No output bounds.
- No environment sanitization.

---

# 2. Threat Analysis

Threat model categories:

## 2.1 Arbitrary Command Injection

Vector:
- User passes destructive command intentionally or indirectly.

Impact:
- Data loss
- System compromise

Current Mitigation:
- Manual confirmation only

---

## 2.2 Shell Chaining and Control Operators

Examples:
- `cmd1 && cmd2`
- `cmd1 ; cmd2`
- `cmd1 | cmd2`

Observation:
- With `shell=False`, operators are treated as arguments unless explicitly invoked via `bash -c` or `cmd /c`.

Residual Risk:
- Indirect shell invocation.

---

## 2.3 Dangerous Commands

Examples:
- `rm -rf /`
- `del /s /q C:\`
- `format`
- `shutdown`
- `curl | sh`

Impact:
- Catastrophic data/system damage.

---

## 2.4 Background Execution Abuse

Examples:
- Long-running servers
- Infinite loops
- Detached processes

Impact:
- Resource exhaustion
- Zombie processes

---

## 2.5 Hanging Processes

Examples:
- Waiting on input
- Blocking network calls

Impact:
- CLI freeze

---

## 2.6 Environment Variable Leakage

Risk:
- Subprocess inherits full environment
- Secrets exposed via child process behavior

---

# 3. Proposed Layered Hardening Strategy

Design principle: Defense in depth. Each layer independently reduces risk.

---

## 3.1 Input Sanitization Layer

### Goals
- Prevent obvious injection attempts
- Preserve legitimate developer workflows

### Strategy

1. Reject empty or whitespace-only commands.
2. Reject embedded null bytes.
3. Detect suspicious control tokens BEFORE parsing:
   - `&&`
   - `||`
   - `;`
   - `|`
   - `>`
   - `<`

Policy:
- Phase 1: Warn-only mode
- Phase 2: Block unless explicitly allowed via config

---

## 3.2 Command Parsing Rules

Current:
- `shlex.split()`

Hardening:

1. Continue using `shell=False`.
2. Disallow execution of known shell binaries unless explicitly enabled:
   - `bash`
   - `sh`
   - `cmd`
   - `powershell`

Rationale:
Prevents bypass via `bash -c`.

---

## 3.3 Whitelist / Denylist Strategy

### Denylist (High Confidence Dangerous)

Categories:
- Filesystem destruction
- Disk formatting
- System shutdown
- User management

Examples:
- `rm`
- `del`
- `rmdir`
- `format`
- `shutdown`
- `reboot`

Mode:
- Soft block first (warn + require typed override)
- Hard block configurable

### Optional Allowlist Mode

Enterprise deployment option:
- Only allow specific safe commands
- Disabled by default

---

## 3.4 Timeout Enforcement

Add:
- Configurable timeout (default 30s)

Behavior:
- On timeout:
  - Kill process
  - Return controlled error

Prevents:
- Hanging
- Infinite loops

---

## 3.5 Subprocess Invocation Mode

Mandate:
- Always `shell=False`
- Always pass argument list

Enhancement:
- Use `start_new_session=True` to isolate process group

Prevents:
- Signal propagation issues
- Detached background escape

---

## 3.6 Output Truncation Safeguards

Risk:
- Extremely large output floods CLI

Mitigation:
- Capture output
- Truncate after configurable size (e.g., 100KB)
- Append `[output truncated]`

---

## 3.7 Environment Sanitization

Current:
- Inherits full environment

Hardening:

Option A: Minimal safe environment
Option B: Pass-through with secret filtering

Recommended Phase 1:
- Strip known sensitive keys:
  - `AWS_SECRET_ACCESS_KEY`
  - `OPENAI_API_KEY`
  - `GITHUB_TOKEN`

---

# 4. Compatibility Impact Analysis

## 4.1 Must Preserve

- CLI signature
- Confirmation prompt
- Standard command execution
- Developer workflows like:
  - `git status`
  - `pip install`
  - `pytest`

## 4.2 Potentially Impacted

- Chained commands
- Redirect operators
- Direct shell invocation

Mitigation:
- Phased enforcement
- Feature flags
- Explicit override mode

---

# 5. Incremental Rollout Plan

## Phase 0: Logging Only
- Detect risky patterns
- Log warnings
- No blocking

## Phase 1: Soft Enforcement
- Warning prompts for risky commands
- Timeout active
- Output truncation active

## Phase 2: Default Deny High-Risk Commands
- Block confirmed destructive patterns
- Require explicit override flag

## Phase 3: Enterprise Strict Mode
- Optional allowlist enforcement

Feature flags stored in config.

---

# 6. Safe Fallback Behavior

If command blocked:

1. Print structured error:
   - Reason category
   - Detected risk pattern
2. Provide override guidance (if allowed)
3. Never partially execute

If timeout occurs:
- Kill process
- Print timeout message
- Return non-zero code

If output truncated:
- Explicit truncation notice

---

# 7. Test Matrix

## 7.1 Normal Workflow Tests

- `git status`
- `python --version`
- `pip list`
- `pytest`

Expected: unchanged behavior.

---

## 7.2 Dangerous Command Detection

- `rm -rf /`
- `shutdown now`
- `format C:`

Expected:
- Warning or block depending on phase.

---

## 7.3 Chaining Attempts

- `echo hi && rm file`
- `ls | grep test`

Expected:
- Detection and warn/block.

---

## 7.4 Timeout Tests

- `sleep 120`

Expected:
- Terminated at timeout.

---

## 7.5 Output Flood Tests

- Generate >1MB output

Expected:
- Truncated safely.

---

## 7.6 Environment Leakage Tests

- Print environment

Expected:
- Sensitive keys absent.

---

# Hardened Execution Architecture Summary

Final architecture (conceptual):

User Input
   -> Pre-Validation Layer
   -> Risk Classification
   -> Policy Engine
   -> Sanitized Subprocess Invocation
   -> Output Guard Layer
   -> Structured Result

This strategy preserves the current command surface and CLI experience while incrementally introducing layered safety controls suitable for production environments.

This document is the authoritative reference for implementation.