#!/usr/bin/env bash
set -euo pipefail

# install-cli.sh
# POSIX installer to create a user-local `ai` shim that runs the Jarvis CLI from this repository.
# Usage:
#   ./install-cli.sh            # installs shim to $HOME/bin and prints instructions if $HOME/bin not in PATH
#   ./install-cli.sh --add-path # also appends export PATH to common shell rc files

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/bin"
SHIM_PATH="$BIN_DIR/ai"
BACKUP_SUFFIX=".bak"

python_cmd=""
if command -v python3 >/dev/null 2>&1; then
  python_cmd="python3"
elif command -v python >/dev/null 2>&1; then
  python_cmd="python"
else
  echo "Error: python3 or python is required but not found in PATH." >&2
  exit 1
fi

mkdir -p "$BIN_DIR"

if [ -f "$SHIM_PATH" ]; then
  echo "Existing shim found at $SHIM_PATH -> backing up to ${SHIM_PATH}${BACKUP_SUFFIX}"
  mv "$SHIM_PATH" "${SHIM_PATH}${BACKUP_SUFFIX}"
fi

cat > "$SHIM_PATH" <<'SHIM'
#!/usr/bin/env sh
# ai shim: invokes the Jarvis CLI in its repository directory
REPO_DIR="__REPO_DIR__"
PYTHON_CMD="__PYTHON_CMD__"
exec "$PYTHON_CMD" "$REPO_DIR/jarvis.py" "$@"
SHIM

# Replace tokens with actual values
sed -i "s#__REPO_DIR__#${REPO_DIR}#g" "$SHIM_PATH"
sed -i "s#__PYTHON_CMD__#${python_cmd}#g" "$SHIM_PATH"

chmod +x "$SHIM_PATH"

printf "Installed shim: %s\n" "$SHIM_PATH"

# Check if $BIN_DIR is in PATH
case ":$PATH:" in
  *":$BIN_DIR:"*)
    echo "$BIN_DIR is already in PATH"
    ;;
  *)
    echo
    echo "Note: $BIN_DIR is not in your PATH. To use 'ai' from any directory, add it to your PATH."
    echo "You can add the following line to your shell RC (e.g. ~/.profile or ~/.bashrc):"
    echo
    echo "  export PATH=\"\$HOME/bin:\$PATH\""
    echo
    echo "Run: ./install-cli.sh --add-path to automatically append the export to common rc files."
    ;;
esac

# Optionally append PATH export if user asked for it
if [ "${1-}" = "--add-path" ] || [ "${2-}" = "--add-path" ]; then
  appended=0
  for rc in "$HOME/.profile" "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [ -f "$rc" ]; then
      if ! grep -q "# jarvis ai shim" "$rc" 2>/dev/null; then
        printf "\n# jarvis ai shim\nexport PATH=\"\$HOME/bin:\$PATH\"\n" >> "$rc"
        printf "Appended PATH export to %s\n" "$rc"
        appended=1
      fi
    fi
  done
  if [ "$appended" -eq 0 ]; then
    # No rc files found; create ~/.profile with entry
    printf "# jarvis ai shim\nexport PATH=\"\$HOME/bin:\$PATH\"\n" >> "$HOME/.profile"
    printf "Created %s and added PATH export\n" "$HOME/.profile"
  fi
  echo "You may need to restart your shell or run: source ~/.profile (or the relevant rc file)"
fi

exit 0
