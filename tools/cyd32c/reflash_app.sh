#!/bin/zsh
# Rewrite only the app (0x20000) on a board that ALREADY runs Blink CYD32C.
# Refuses unless the board's MCUboot matches the release's (verify_flash),
# so a factory board is never half-flashed. Restarts the Blink service after.
#   ./reflash_app.sh [port] [release_dir]
set -u
PORT=${1:-/dev/cu.usbserial-2010}
REL=${2:-$(dirname "$0")/../../release/1.5.0-cyd32c}
ESP=${ESPTOOL:-esptool.py}
AGENT="gui/$(id -u)/com.blink.bridge"
(cd "$REL" && shasum -a 256 -c SHA256SUMS) || exit 1
launchctl bootout "$AGENT" 2>/dev/null; sleep 2
if $ESP --port "$PORT" verify_flash 0x1000 "$REL/mcuboot.bin" >/dev/null 2>&1; then
	$ESP --port "$PORT" --baud 460800 write_flash 0x20000 \
		"$REL/blink-cyd32c-1.5.0.signed.bin"; RC=$?
else
	echo "This board's bootloader is not this release's MCUboot: use flash_new.sh"; RC=1
fi
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.blink.bridge.plist" 2>/dev/null
launchctl kickstart "$AGENT" 2>/dev/null
exit $RC
