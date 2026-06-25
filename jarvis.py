#!/usr/bin/env python3
import sys
import argparse

from core.config import ensure_directories
from commands.router import dispatch


# Context building moved to ContextBuilder


from core.logger import get_logger

logger = get_logger("jarvis.main")

# Chat logic handled by router default command


def main():
    ensure_directories()
    logger.info("Jarvis startup complete.")

    parser = argparse.ArgumentParser(prog="ai")
    parser.add_argument("command", nargs="*", help="Command or message")

    args = parser.parse_args()

    # Interactive mode
    if not args.command:
        print("Jarvis v1.0")
        while True:
            try:
                user_input = input("> ").strip()
                if user_input.lower() in {"exit", "quit"}:
                    break
                if user_input:
                    dispatch(user_input.split())
            except KeyboardInterrupt:
                print()
                break
        sys.exit(0)

    dispatch(args.command)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted.")
        sys.exit(130)
    except Exception as e:
        message = str(e).strip() or "Unexpected failure"
        print(f"Error: {message}")
        sys.exit(1)
