from core.memory import MemoryManager
from commands.registry import register_command


def run(args: list):
    raw = " ".join(args).strip()

    # If strict key=value form → handle here
    if raw and "=" in raw:
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip()

        memory = MemoryManager()
        memory.remember(key, value)
        print(f"Stored memory: {key}")
        return 0

    # Otherwise, signal router to fall through to intent detection
    return 1


def register():
    register_command("remember", run, "Store key=value memory")
