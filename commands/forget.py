from core.memory import MemoryManager
from commands.registry import register_command


def run(args: list):
    if not args:
        print("Usage: ai forget <key>")
        return

    key = " ".join(args).strip()

    memory = MemoryManager()
    memory.forget(key)

    print(f"Removed memory: {key}")


def register():
    register_command("forget", run, "Remove stored memory by key")
