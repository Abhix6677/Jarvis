import subprocess
import shlex


DEFAULT_TIMEOUT_SECONDS = 30
MAX_OUTPUT_BYTES = 100 * 1024  # 100 KB


SUSPICIOUS_OPERATORS = ["&&", "||", ";", "|"]
DESTRUCTIVE_PATTERNS = [
    "rm -rf /",
    "shutdown",
    "format",
]


def _log_risk_warnings(command: str) -> None:
    lowered = command.lower()

    detected = []

    for op in SUSPICIOUS_OPERATORS:
        if op in command:
            detected.append(f"operator '{op}'")

    for pattern in DESTRUCTIVE_PATTERNS:
        if pattern in lowered:
            detected.append(f"pattern '{pattern}'")

    if detected:
        print("[Shell Hardening - Phase 1] Potentially risky command detected:")
        for item in detected:
            print(f"  - Detected {item}")
        print("Execution will continue (Phase 1 is observability-only).")


def _truncate_output(stdout: str, stderr: str) -> tuple[str, str]:
    combined = (stdout or "") + (stderr or "")

    if len(combined.encode("utf-8")) <= MAX_OUTPUT_BYTES:
        return stdout, stderr

    encoded = combined.encode("utf-8")[:MAX_OUTPUT_BYTES]
    truncated_text = encoded.decode("utf-8", errors="ignore")

    notice = "\n[Output truncated to 100KB by shell hardening]\n"

    return truncated_text + notice, ""


def run(args: list):
    if not args:
        print("Usage: ai run \"command\"")
        return

    raw_command = " ".join(args)

    print(f"About to execute: {raw_command}")

    # Phase 1: Risk detection (non-blocking)
    _log_risk_warnings(raw_command)

    confirm = input("Proceed? (y/N): ").strip().lower()

    if confirm != "y":
        print("Execution cancelled.")
        return

    try:
        result = subprocess.run(
            shlex.split(raw_command),
            capture_output=True,
            text=True,
            timeout=DEFAULT_TIMEOUT_SECONDS,
            shell=False,  # Explicitly enforce no shell invocation
        )

        stdout = result.stdout or ""
        stderr = result.stderr or ""

        stdout, stderr = _truncate_output(stdout, stderr)

        if stdout:
            print(stdout)
        if stderr:
            print(stderr)

        if result.returncode != 0:
            return result.returncode

    except subprocess.TimeoutExpired as e:
        print(
            f"Command timed out after {DEFAULT_TIMEOUT_SECONDS} seconds. Process terminated."
        )
        try:
            if e.process:
                e.process.kill()
        except Exception:
            pass
        return 1

    except Exception as e:
        print(f"Execution error: {e}")
        return 1
