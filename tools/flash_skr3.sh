#!/usr/bin/env bash
# Rebuild Klipper and flash the SKR 3 EZ over USB from the Pi, via Katapult; then the Pi's
# host MCU when that service exists (this build has none), and the ADXL345's Pico when present. Run it when Mainsail reports an MCU protocol
# mismatch after a Klipper update. One-time setup and menuconfig: docs/03-firmware-flash.md.
#
#   ~/Ender-3-Pro-SKR-3-EZ-Sprite-Tool-Head/tools/flash_skr3.sh            # build + flash
#   ~/Ender-3-Pro-SKR-3-EZ-Sprite-Tool-Head/tools/flash_skr3.sh --no-build # flash the existing out/klipper.bin
#   DEV=/dev/serial/by-id/usb-katapult_stm32h723xx_...-if00 tools/flash_skr3.sh   # board already in Katapult
set -euo pipefail

KLIPPER=${KLIPPER:-$HOME/klipper}
KATAPULT=${KATAPULT:-$HOME/katapult}
CFG=${CFG:-config.skr3}          # board build options (docs/03 section 3); .config is the host MCU's
DEV=${DEV:-}
BUILD=1
[ "${1:-}" = "--no-build" ] && BUILD=0

if [ -z "$DEV" ]; then
    # Klipper running -> usb-Klipper_stm32h7..., sitting in the bootloader -> usb-katapult_stm32h7...
    DEV=$(ls /dev/serial/by-id/ 2>/dev/null | grep -iE '^usb-(Klipper|katapult)_stm32h7' | head -n1 || true)
    [ -n "$DEV" ] || { echo "No SKR 3 on USB (nothing in /dev/serial/by-id/ matching stm32h7). Is Klipper or Katapult running on it? Double-tap RESET enters Katapult."; exit 1; }
    DEV=/dev/serial/by-id/$DEV
fi

if [ "$BUILD" = 1 ]; then
    [ -f "$KLIPPER/$CFG" ] || { echo "No $KLIPPER/$CFG: run 'make KCONFIG_CONFIG=$CFG menuconfig' once (docs/03, section 3)"; exit 1; }
    grep -q 'CONFIG_MACH_STM32H7' "$KLIPPER/$CFG" || { echo "$KLIPPER/$CFG is not an STM32H7 build; check menuconfig"; exit 1; }
    echo "== building Klipper for the SKR 3 ($CFG)"
    make -C "$KLIPPER" KCONFIG_CONFIG="$CFG" clean >/dev/null
    make -C "$KLIPPER" KCONFIG_CONFIG="$CFG" -j"$(nproc)"
fi
[ -f "$KLIPPER/out/klipper.bin" ] || { echo "No $KLIPPER/out/klipper.bin to flash"; exit 1; }
# out/ holds whatever was built last (the Pico build lands there too). Refuse anything
# that is not an STM32H7 image, so --no-build can never send the Pico's binary to the SKR 3.
grep -q '^#define CONFIG_MACH_STM32H7 1' "$KLIPPER/out/autoconf.h" 2>/dev/null \
    || { echo "$KLIPPER/out/klipper.bin was not built for the STM32H7 (last build was another MCU). Run without --no-build."; exit 1; }

echo "== stopping Klipper"
sudo service klipper stop
trap 'echo "== starting Klipper"; sudo service klipper start' EXIT

echo "== flashing $DEV"
python3 "$KATAPULT/scripts/flashtool.py" -d "$DEV" -f "$KLIPPER/out/klipper.bin"

sleep 2
echo "== board now shows as:"
ls /dev/serial/by-id/ | grep -iE 'stm32h7' || true

# The ADXL345's Pico (docs/06): rebuilt and flashed over its Klipper USB path when config.pico
# exists and the Pico is plugged in. First-time flash needs BOOTSEL by hand (docs/06).
PICO=$(ls /dev/serial/by-id/ 2>/dev/null | grep -i '^usb-Klipper_rp2040' | head -n1 || true)
if [ "$BUILD" = 1 ] && [ -f "$KLIPPER/config.pico" ] && [ -n "$PICO" ]; then
    echo "== building and flashing the Pico ($PICO)"
    make -C "$KLIPPER" KCONFIG_CONFIG=config.pico clean >/dev/null
    make -C "$KLIPPER" KCONFIG_CONFIG=config.pico -j"$(nproc)"
    make -C "$KLIPPER" KCONFIG_CONFIG=config.pico flash FLASH_DEVICE="/dev/serial/by-id/$PICO"
    # the SKR 3 build is restored into out/ so --no-build keeps working next time
    make -C "$KLIPPER" KCONFIG_CONFIG="$CFG" clean >/dev/null
    make -C "$KLIPPER" KCONFIG_CONFIG="$CFG" -j"$(nproc)" >/dev/null
fi

# Linux host MCU: only when such a service was set up (not in this build), and only with a build.
if [ "$BUILD" = 1 ] && systemctl list-unit-files klipper-mcu.service >/dev/null 2>&1 \
   && grep -q 'CONFIG_MACH_LINUX=y' "$KLIPPER/.config" 2>/dev/null; then
    echo "== rebuilding and flashing the Pi host MCU (.config, Linux process)"
    make -C "$KLIPPER" clean >/dev/null
    make -C "$KLIPPER" -j"$(nproc)"
    sudo service klipper-mcu stop
    sudo make -C "$KLIPPER" flash
    sudo service klipper-mcu start
fi
