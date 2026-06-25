"""
Jarvis CLI entry point.

This module serves as the single authoritative CLI entry point.
It routes known commands to the command router and falls back to
natural language intent detection when no command matches.
"""

from __future__ import annotations

import sys
from typing import List

from commands.router import dispatch
from core.intent import detect_and_store_intent
from core.context import ContextBuilder
from core.api import get_client
from core.response_parser import ResponseParser


FALLBACK_MESSAGE = "No command matched and no intent could be detected."


def main() -> int:
    """
    Primary CLI entrypoint.

    Behavior:
    1. Parse sys.argv[1:]
    2. Attempt to dispatch via command router
    3. If no command matches, treat input as natural language
    4. Return appropriate exit code
    """
    argv: List[str] = sys.argv[1:]

    # No arguments provided
    if not argv:
        print(FALLBACK_MESSAGE)
        return 1

    # Attempt CLI command dispatch first
    try:
        exit_code = dispatch(argv)
        # If a valid command executed successfully, stop here
        if exit_code == 0:
            return exit_code
    except Exception:
        # Router may raise if command is unknown or malformed.
        # In that case, fall back to natural language handling.
        pass

    # Treat entire input as natural language
    text_input = " ".join(argv).strip()
    if not text_input:
        print(FALLBACK_MESSAGE)
        return 1

    # Step 2: Deterministic intent detection (NO LLM)
    intent_result = detect_and_store_intent(text_input)

    if intent_result:
        print(intent_result)
        return 0

    # Step 3: Conversational LLM fallback
    try:
        from core.logger import get_logger
        from core.history import HistoryManager
        from core.summary import SummaryManager
        
        logger = get_logger("jarvis.main")
        logger.info(f"Processing natural language input: {text_input[:50]}...")
        
        context_builder = ContextBuilder()
        messages = context_builder.build(text_input)

        import threading
        import itertools
        import time

        def _spinner(stop_event):
            for ch in itertools.cycle('|/-\\'):
                if stop_event.is_set():
                    break
                # carriage return to keep on the same line
                sys.stdout.write('\rProcessing... ' + ch)
                sys.stdout.flush()
                time.sleep(0.1)
            # clear the line once done
            sys.stdout.write('\r' + ' ' * 40 + '\r')
            sys.stdout.flush()

        stop_event = threading.Event()
        spinner_thread = threading.Thread(target=_spinner, args=(stop_event,), daemon=True)
        spinner_thread.start()

        client = get_client()
        try:
            raw_response = client.chat(messages)
        finally:
            stop_event.set()
            spinner_thread.join()

        clean_text = ResponseParser.extract_text(raw_response)
        print(clean_text)
        
        # Save to history
        history = HistoryManager()
        history.add("user", text_input)
        history.add("assistant", clean_text)
        
        # Check if summary should be updated
        if history.should_summarize():
            logger.info("History limit reached, triggering summary update...")
            summary_manager = SummaryManager()
            history_messages = str(history._load())
            summary_manager.update_summary(history_messages)
            # After summarizing, clear old history
            logger.info("Clearing old history after summarization")
            history.clear()
            history.add("user", text_input)
            history.add("assistant", clean_text)
        
        return 0
    except Exception as exc:
        from core.logger import get_logger
        logger = get_logger("jarvis.main")
        logger.error(f"LLM error: {exc}", exc_info=True)
        print(f"LLM error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
