import subprocess


def run(args: list):
    try:
        confirm = input("Push to remote? (y/N): ").strip().lower()
        if confirm != "y":
            print("Push cancelled.")
            return

        result = subprocess.run(
            ["git", "push"],
            capture_output=True,
            text=True
        )

        print(result.stdout)
        if result.stderr:
            print(result.stderr)

    except Exception as e:
        print(f"Git push error: {e}")
