from core.memory import MemoryManager


def run(args: list):
    if not args:
        print("Usage: ai forget <key>")
        return

    key = " ".join(args).strip()

    memory = MemoryManager()
    memory.forget(key)

    print(f"Removed memory: {key}")
