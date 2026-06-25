# Jarvis-Termux AI v1.0

Jarvis-Termux AI is a lightweight, local-first AI command assistant designed for Termux and standard Python environments. It provides structured command routing, memory management, shell execution, update capabilities, and self-diagnostics while keeping project memory isolated and secure.

---

## Features

- Modular command architecture
- Local project-scoped memory
- Command routing system
- Secure shell execution (`shell` command)
- Built-in self diagnostics (`self-test`)
- Update mechanism (`update`)
- Caching and storage isolation
- Minimal external dependencies

---

## Python Requirement

- Python **3.9+** recommended

---

## Installation

### Termux Installation

```bash
pkg update && pkg upgrade
pkg install python git

git clone <your-repo-url>
cd Jarvis
pip install -r requirements.txt
```

Run:

```bash
python jarvis.py
```

---

### Generic Python Installation (Windows/Linux/macOS)

```bash
git clone <your-repo-url>
cd Jarvis
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/macOS

pip install -r requirements.txt
python jarvis.py
```

---

## Usage

Run Jarvis:

```bash
python jarvis.py
```

Commands are routed through the internal command registry.

### `self-test`

Runs internal diagnostics to validate:
- Storage access
- Cache integrity
- Memory system health
- Configuration loading

Use when:
- Setting up for the first time
- Verifying environment consistency
- Debugging unexpected behavior

---

### `update`

Handles project update logic.

Intended for:
- Pulling latest repository changes
- Applying safe update routines
- Maintaining consistent local installation

This command does not modify core architecture at runtime.

---

### `shell`

Executes controlled shell commands through a secured interface.

Security considerations:
- Designed for controlled execution
- Follows shell hardening strategy documented in `docs/shell_security_hardening.md`
- Avoid running destructive system commands

---

## Storage Locations

Jarvis uses structured local storage:

- `data/` – Persistent project memory
- `cache/` – Temporary cached data
- `core/` – Core engine modules
- `commands/` – Command implementations

`.gitkeep` files are used to ensure required directories remain tracked in version control.

---

## Safety Notes

- Designed for local execution only
- Avoid exposing shell command execution to remote interfaces
- Do not commit sensitive `.env` files
- Review update behavior before using in production environments

---

## Versioning

Current version: **1.0.0**

Version is defined inside:

```
core/__init__.py
```

---

Jarvis-Termux AI v1.0 is designed to remain minimal, modular, and production-ready while maintaining strict project memory isolation.
