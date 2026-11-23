#!/bin/zsh
# Flash a NEW ESP32-2432S032C (factory firmware) with Blink CYD32C:
# erase, MCUboot at 0x1000, signed app at 0x20000. Stops the Blink service
# while it holds the port and does NOT restart it (unplug the board first).
#   ./flash_new.sh [port] [release_dir]
set -u
PORT=${1:-}
REL=${2:-$(dirname "$0")/../../release/1.5.0-cyd32c}
ESP=${ESPTOOL:-esptool.py}
EFUSE=${ESPEFUSE:-espefuse.py}
if [ -z "$PORT" ]; then PORT=$(ls /dev/cu.usbserial-* 2>/dev/null | head -1); fi
[ -n "$PORT" ] || { echo "No board found (use a USB-A to USB-C data cable)"; exit 1; }
(cd "$REL" && shasum -a 256 -c SHA256SUMS) || exit 1
launchctl bootout "gui/$(id -u)/com.blink.bridge" 2>/dev/null; sleep 2
CNT=$($EFUSE --port "$PORT" summary 2>/dev/null | grep FLASH_CRYPT_CNT | grep -o '(0b[01]*)')
[ "$CNT" = "(0b0000000)" ] || { echo "Flash encryption on or unreadable ($CNT): stopping."; exit 1; }
$ESP --port "$PORT" --baud 460800 erase_flash || exit 1
$ESP --port "$PORT" --baud 460800 write_flash \
	0x1000 "$REL/mcuboot.bin" 0x20000 "$REL/blink-cyd32c-1.5.0.signed.bin" || exit 1
echo "Done. Unplug the board, then: launchctl kickstart gui/$(id -u)/com.blink.bridge"
