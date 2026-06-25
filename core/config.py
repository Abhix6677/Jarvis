import os
import json
from pathlib import Path
from dataclasses import dataclass

BASE_DIR = Path.home() / ".jarvis"
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = BASE_DIR / "cache"
LOG_DIR = BASE_DIR / "logs"
PROJECTS_DIR = DATA_DIR / "projects"

HISTORY_FILE = DATA_DIR / "history.json"
MEMORY_FILE = DATA_DIR / "memory.json"
SUMMARY_FILE = DATA_DIR / "summary.json"
PROJECTS_FILE = DATA_DIR / "projects.json"
LOG_FILE = LOG_DIR / "jarvis.log"

API_URL = "https://api.bluesminds.com/v1"
MODEL = "glm-4.6"


@dataclass(frozen=True)
class RuntimeConfig:
    history_limit: int = 20
    summary_trigger: int = 50
    chat_temperature: float = 0.3
    summary_temperature: float = 0.2
    api_timeout: int = 60
    api_retries: int = 2
    system_prompt: str = (
        "You are Jarvis, a local AI assistant running inside Termux. "
        "Reply only in plain natural Hinglish or English conversational text. "
        "Never output tokens like 'to=', 'commentary', 'analysis', 'bio', "
        "JSON/tool-call syntax, or any internal protocol. "
        "You have NO tools available. Never attempt to call any tool."
    )


CONFIG = RuntimeConfig()


def ensure_directories():
    """Ensure required directories and files exist."""
    for directory in [BASE_DIR, DATA_DIR, CACHE_DIR, LOG_DIR, PROJECTS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    for file_path, default in [
        (HISTORY_FILE, []),
        (MEMORY_FILE, {}),
        (SUMMARY_FILE, {"summary": ""}),
        (PROJECTS_FILE, {}),
    ]:
        if not file_path.exists():
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(default, f)


def get_api_key() -> str:
    key = os.getenv("BLUESMINDS_API_KEY")
    if not key:
        raise EnvironmentError(
            "BLUESMINDS_API_KEY environment variable not set."
        )
    return key
