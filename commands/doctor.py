import subprocess
from core.api import get_client


def collect_output(command: str) -> str:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )
        return result.stdout + "\n" + result.stderr
    except Exception as e:
        return f"Error running {command}: {e}"


def run(args: list):
    print("Collecting project diagnostics...\n")

    diagnostics = {}

    diagnostics["git_status"] = collect_output("git status")
    diagnostics["composer_json"] = collect_output("type composer.json")
    diagnostics["package_json"] = collect_output("type package.json")

    prompt = [
        {"role": "system", "content": "You are an expert Laravel and DevOps AI doctor. Diagnose issues and provide concise technical guidance."},
        {"role": "user", "content": str(diagnostics)},
    ]

    client = get_client()
    response = client.chat(prompt, temperature=0.2)

    print("\nAI Diagnosis:\n")
    print(response)
