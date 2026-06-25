#!/usr/bin/env bash

# Jarvis-Termux AI Installer (Production Hardened)
# Safe, idempotent, portable

set -euo pipefail

############################################
# Helpers
############################################

info()  { echo "[✓] $1"; }
warn()  { echo "[!] $1"; }
fail()  { echo "[✗] $1" >&2; exit 1; }

############################################
# Detect script directory
############################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

############################################
# Detect environment
############################################

IS_TERMUX=false
if [ -n "${PREFIX:-}" ] && [[ "$PREFIX" == *"com.termux"* ]]; then
  IS_TERMUX=true
fi

############################################
# Dependency checks
############################################

require_command() {
  command -v "$1" >/dev/null 2>&1
}

install_termux_pkg() {
  pkg install -y "$1" || fail "Failed to install package: $1"
}

info "Checking dependencies..."

if ! require_command git; then
  if $IS_TERMUX; then
    info "Installing git..."
    install_termux_pkg git
  else
    fail "Git not found. Install git and re-run installer."
  fi
fi
info "Git found"

if require_command python3; then
  PYTHON_BIN="python3"
elif require_command python; then
  PYTHON_BIN="python"
else
  if $IS_TERMUX; then
    info "Installing python..."
    install_termux_pkg python
    PYTHON_BIN="python"
  else
    fail "Python not found. Install Python 3 and re-run installer."
  fi
fi
info "Python detected: $PYTHON_BIN"

if ! "$PYTHON_BIN" -m pip --version >/dev/null 2>&1; then
  if $IS_TERMUX; then
    info "Installing pip..."
    install_termux_pkg python
  else
    fail "pip not available. Install pip and re-run installer."
  fi
fi
info "pip available"

############################################
# Validate requirements file
############################################

REQ_FILE="$SCRIPT_DIR/requirements.txt"
[ -f "$REQ_FILE" ] || fail "requirements.txt not found in project directory."

############################################
# Install dependencies
############################################

info "Installing Python dependencies..."
"$PYTHON_BIN" -m pip install --upgrade --quiet pip >/dev/null 2>&1 || true
"$PYTHON_BIN" -m pip install -r "$REQ_FILE" || fail "Dependency installation failed."

############################################
# Setup directories
############################################

BASE_DIR="$HOME/.jarvis"

info "Creating directories..."
mkdir -p "$BASE_DIR"/{core,commands,data,projects,cache,logs}

############################################
# Preserve user data
############################################

init_json_if_missing() {
  local file="$1"
  if [ ! -f "$file" ]; then
    echo "{}" > "$file"
  fi
}

init_json_if_missing "$BASE_DIR/data/memory.json"
init_json_if_missing "$BASE_DIR/data/summary.json"
init_json_if_missing "$BASE_DIR/data/history.json"

############################################
# Copy project safely
############################################

info "Copying application files..."
rsync -a --delete \
  --exclude=".git" \
  --exclude=".gitignore" \
  --exclude="__pycache__" \
  --exclude="*.pyc" \
  "$SCRIPT_DIR/" "$BASE_DIR/" || fail "File copy failed."

############################################
# Create executable
############################################

if $IS_TERMUX; then
  BIN_DIR="$PREFIX/bin"
else
  BIN_DIR="/usr/local/bin"
fi

info "Creating ai executable..."
cat > "$BASE_DIR/ai" <<EOF
#!/usr/bin/env bash
exec "$PYTHON_BIN" "$BASE_DIR/jarvis.py" "\$@"
EOF

chmod +x "$BASE_DIR/ai"

if [ -w "$BIN_DIR" ]; then
  ln -sf "$BASE_DIR/ai" "$BIN_DIR/ai"
else
  warn "No permission to write to $BIN_DIR."
  warn "You may need: sudo ln -sf $BASE_DIR/ai $BIN_DIR/ai"
fi

############################################
# Verification
############################################

info "Verifying installation..."

[ -f "$BASE_DIR/jarvis.py" ] || fail "jarvis.py missing after installation."
[ -x "$BASE_DIR/ai" ] || fail "ai executable not created."

if ! "$PYTHON_BIN" -c "import sys" >/dev/null 2>&1; then
  fail "Python execution test failed."
fi

if command -v ai >/dev/null 2>&1; then
  info "ai command available"
else
  warn "ai command not in PATH yet. Restart shell if necessary."
fi

info "Installation successful"
echo "Run: ai hello"
