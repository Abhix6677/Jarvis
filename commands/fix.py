from typing import List

from core.memory import MemoryManager
from commands.registry import register_command


def run(args: List[str]):
    """Interactive error fixer CLI.

    Usage:
      ai fix list                    # list recorded errors
      ai fix show <error_id>         # show detailed error entry
      ai fix show-suggestion <error_id>  # show saved auto-fix suggestion
      ai fix apply <error_id>        # print suggestion (DO NOT apply automatically)

    Notes:
    - This command intentionally DOES NOT write patches to files.
    - 'apply' will only print the saved suggestion for manual review.
    """
    m = MemoryManager()

    if not args:
        print("Usage: ai fix [list|show|show-suggestion|apply] <error_id>")
        return 1

    cmd = args[0]

    if cmd == "list":
        errors = m.list_errors()
        if not errors:
            print("No recorded errors.")
            return 0
        for e in errors:
            print(f"{e['id']}: {e.get('file')}:{e.get('line')} summary={e.get('summary')}")
        return 0

    if cmd == "show":
        if len(args) < 2:
            print("Usage: ai fix show <error_id>")
            return 1
        eid = args[1]
        e = m.get_error(eid)
        if not e:
            print(f"No error with id {eid}")
            return 1
        print(f"ID: {e['id']}")
        print(f"Timestamp: {e['timestamp']}")
        print(f"File: {e['file']}:{e.get('line')}")
        print("Stack:\n")
        print(e.get('stack'))
        print("---")
        return 0

    if cmd == "show-suggestion":
        if len(args) < 2:
            print("Usage: ai fix show-suggestion <error_id>")
            return 1
        key = f"auto_fix:{args[1]}"
        all_mem = m.get_all()
        val = all_mem.get(key)
        if not val:
            print("No saved suggestion for that id.")
            return 1
        # If suggestion looks like a diff, try to pretty-print it; otherwise, print raw
        if isinstance(val, str) and val.strip().startswith("---"):
            # crude unified-diff pretty print: just show as-is
            print(val)
        else:
            print(val)
        return 0

    if cmd == "apply":
        if len(args) < 2:
            print("Usage: ai fix apply <error_id>")
            return 1
        key = f"auto_fix:{args[1]}"
        all_mem = m.get_all()
        val = all_mem.get(key)
        if not val:
            print("No saved suggestion for that id.")
            return 1
        # For safety, we only print the suggestion. Applying automatically is dangerous.
        print("Suggested patch / explanation:\n")
        print(val)
        return 0

    print("Unknown subcommand")
    return 1
