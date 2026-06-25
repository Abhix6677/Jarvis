from core.memory import MemoryManager


def run(args: list):
    if not args or "=" not in " ".join(args):
        print("Usage: ai remember key=value")
        return

    raw = " ".join(args)
    key, value = raw.split("=", 1)

    key = key.strip()
    value = value.strip()

    memory = MemoryManager()
    memory.remember(key, value)

    print(f"Stored memory: {key}")
