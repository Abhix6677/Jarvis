from core.memory import MemoryManager


def run(args: list):
    memory = MemoryManager()
    data = memory.get_all()

    if not data:
        print("No stored memory.")
        return

    for k, v in data.items():
        print(f"{k} = {v}")
