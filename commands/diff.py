import subprocess


def run(args: list):
    try:
        result = subprocess.run(
            ["git", "diff"],
            capture_output=True,
            text=True
        )

        print(result.stdout)
        if result.stderr:
            print(result.stderr)

    except Exception as e:
        print(f"Git diff error: {e}")
