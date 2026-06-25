import subprocess
from commands.registry import register_command


def run(args: list):
    try:
        result = subprocess.run(
            ["git", "status"],
            capture_output=True,
            text=True
        )

        print(result.stdout)
        if result.stderr:
            print(result.stderr)

    except Exception as e:
        print(f"Git status error: {e}")


def register():
    register_command("status", run, "Show git repository status")
