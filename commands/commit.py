import subprocess
from core.api import get_client


def run(args: list):
    try:
        diff = subprocess.run(
            ["git", "diff", "--cached"],
            capture_output=True,
            text=True
        ).stdout

        if not diff.strip():
            print("No staged changes to commit.")
            return

        prompt = [
            {"role": "system", "content": "Generate a concise, professional Git commit message."},
            {"role": "user", "content": diff},
        ]

        client = get_client()
        message = client.chat(prompt, temperature=0.2)

        print(f"Suggested commit message:\n{message}\n")

        confirm = input("Commit with this message? (y/N): ").strip().lower()
        if confirm != "y":
            print("Commit cancelled.")
            return

        subprocess.run(["git", "commit", "-m", message])
        print("Commit created.")

    except Exception as e:
        print(f"Git commit error: {e}")
