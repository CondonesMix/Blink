#!/bin/zsh
# Run the Blink Mac service from this fork (it sends the Fable "models" line).
# Needs the official app installed first (blink install). Keeps the official
# binary as ~/.blink/bin/blink.release; to go back: mv it over ~/.blink/bin/blink.
set -eu
REPO=$(cd "$(dirname "$0")/../.." && pwd)
PY=${PYTHON:-python3}
"$PY" -m venv "$REPO/.venv"
"$REPO/.venv/bin/pip" install -q -r "$REPO/pc/requirements.txt"
launchctl bootout "gui/$(id -u)/com.blink.bridge" 2>/dev/null || true
sleep 2
cd "$HOME/.blink/bin"
[ -f blink.release ] || mv blink blink.release
cat > blink <<W
#!/bin/sh
exec "$REPO/.venv/bin/python" "$REPO/blink_main.py" "\$@"
W
chmod +x blink
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.blink.bridge.plist" 2>/dev/null || true
launchctl kickstart "gui/$(id -u)/com.blink.bridge" || true
"$HOME/.blink/bin/blink" status | head -4
