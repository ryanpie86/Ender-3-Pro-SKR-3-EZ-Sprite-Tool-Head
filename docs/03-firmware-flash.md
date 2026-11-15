# 03 · Build and flash Klipper on the SKR 3 EZ, updates from the Pi

The SKR 3 EZ ships with BTT's bootloader, which only updates from a
`firmware.bin` on the micro-SD card. This guide replaces that bootloader
with **Katapult** (Klipper's own) in one bench session; from then on every
Klipper firmware update is one command on the Pi over the USB cable, no
card and no buttons. There is no brick risk in the swap: the STM32's
built-in DFU mode (a button on the board) is always there to put either
bootloader back.

If you would rather keep BTT's bootloader, section 7 has the SD-card
method; it works with the same Klipper build.

## 1. Identify the MCU

BTT advertises the SKR 3 EZ with an STM32H743, but many boards (this one
included) ship with an **STM32H723**. Read the big square chip in the
middle of the board before building anything:

- `STM32H723VGT6` → **STM32H723** in both menuconfigs below (this build)
- `STM32H743VIT6` → **STM32H743**

Nothing else changes between the two. A build for the wrong chip is
harmless: Katapult or Klipper simply never shows up on USB, and you rebuild.

## 2. One-time: flash Katapult over DFU

On the Pi, with the board connected by USB and powered (24 V from the PSU,
or USB with the VUSB jumper closed for bench work; the USB/CAN switch next
to the port in the **USB** position):

```bash
sudo apt install -y dfu-util python3-serial
```

```bash
cd ~ && git clone https://github.com/Arksine/katapult.git && cd ~/katapult && make menuconfig
```

Set:

```
    Micro-controller Architecture         (STMicroelectronics STM32)
    Processor model                       (STM32H723)   ← STM32H743 if the chip says so
    Build Katapult deployment application (Do not build)
    Clock Reference                       (25 MHz crystal)
    Communication interface               (USB (on PA11/PA12))
    Application start offset              (128KiB offset)
    USB ids                               (leave default)
[*] Support bootloader entry on rapid double click of reset button
```

`Q`, `Y` to save, then `make`. Now put the board in DFU mode: hold
**BOOT0**, tap **RESET**, release BOOT0. Check it shows up:

```bash
lsusb | grep -i dfu
```

(`0483:df11 STMicroelectronics STM Device in DFU Mode`). Flash Katapult
to the start of flash with a full erase; this is what removes BTT's
bootloader:

```bash
sudo dfu-util -a 0 -D ~/katapult/out/katapult.bin --dfuse-address 0x08000000:force:mass-erase:leave -d 0483:df11
```

dfu-util ends with `Submitting leave request...` and then `Error during
download get_status`: that is normal, the board has already reset into
Katapult before answering. Tap RESET if it has not:

```bash
ls /dev/serial/by-id/
```

shows `usb-katapult_stm32h723xx_<serial>-if00` (`h743` on that chip).

## 3. Build Klipper

The board's build options live in their own file, `config.skr3`, so the
optional Linux host-MCU build (which would use Klipper's
default `.config`) never overwrites them:

```bash
cd ~/klipper && make KCONFIG_CONFIG=config.skr3 menuconfig
```

The same build as with BTT's bootloader, because Katapult sits in the same
128 KiB:

```
[*] Enable extra low-level configuration options
    Micro-controller Architecture  (STMicroelectronics STM32)
    Processor model                (STM32H723)   ← STM32H743 if the chip says so
    Bootloader offset              (128KiB bootloader)
    Clock Reference                (25 MHz crystal)
    Communication interface        (USB (on PA11/PA12))
    USB ids                        (leave default)
```

`Q`, `Y`, then:

```bash
make KCONFIG_CONFIG=config.skr3 clean && make KCONFIG_CONFIG=config.skr3 -j4
```

## 4. Flash Klipper from the Pi

```bash
sudo service klipper stop
```

```bash
python3 ~/katapult/scripts/flashtool.py -d /dev/serial/by-id/usb-katapult_stm32h723xx_<serial>-if00 -f ~/klipper/out/klipper.bin
```

```bash
sudo service klipper start
```

Then `ls /dev/serial/by-id/` shows `usb-Klipper_stm32h723xx_<serial>-if00`:
that full path goes into `[mcu] serial:` in `config/printer.cfg`. The
serial number is the chip's and does not change between Katapult and
Klipper, only the prefix does.

If you closed the VUSB jumper for bench power, open it now, before the PSU
is ever connected to DCIN: the Pi must never be fed from the board.

## 5. Every update after that

Mainsail's update manager updates the **host** side of Klipper (the Python
code on the Pi) only. It never flashes an MCU, with any bootloader; that
is a Klipper/Moonraker limitation, not a Katapult one. What Katapult buys
is that the MCU half becomes one command instead of a card shuffle:

```bash
~/Ender-3-Pro-SKR-3-EZ-Sprite-Tool-Head/tools/flash_skr3.sh
```

It rebuilds Klipper from `config.skr3`, stops the Klipper service, asks the
running firmware to drop into Katapult, flashes over USB, starts Klipper
again, flashes the accelerometer's Pico as well when it is plugged in
(`docs/06`), and (only if a `klipper-mcu` host-MCU service was ever set
up; this build has none) rebuilds and reflashes that too, so they never
drift apart. By hand it is sections 3 and 4 with the `Klipper_` device
path: `flashtool.py` sees Klipper running, requests the bootloader itself
and waits for Katapult to appear.

When is it needed? Not after every host update. The MCU firmware keeps
working until the host/MCU protocol changes, which happens a few times a
year, and Klipper tells you: Mainsail shows `MCU 'mcu' protocol version
mismatch` (or `Klipper version mismatch`) and refuses to connect until you
run the script. Running it after any update is harmless either way.

If Klipper is wedged and cannot answer, double-tap RESET: the Katapult
build above enters the bootloader on a rapid double click, and `flashtool`
can be pointed at the `katapult_` path (`DEV=/dev/serial/by-id/usb-katapult_... tools/flash_skr3.sh`).

## 5b. Optional: a FLASH_MCU button in Mainsail

Klipper has no built-in way to run a shell script, but the community
`gcode_shell_command` extra adds one, and `config/shell.cfg` uses it for
**FLASH_MCU** (MAINTENANCE group) and **SHAPER_PLOT** (Calibrate group). Install the extra once:

```bash
wget -O ~/klipper/klippy/extras/gcode_shell_command.py https://raw.githubusercontent.com/dw-0/kiauh/master/kiauh/extensions/gcode_shell_cmd/assets/gcode_shell_command.py
```

(or KIAUH → Extensions → G-Code Shell Command, which drops the same file).
Then copy `config/shell.cfg` next to `printer.cfg`, uncomment
`[include shell.cfg]` at the top of `printer.cfg`, and `RESTART`.

Pressing FLASH_MCU launches the script as its own systemd unit, outside
Klipper's process group, so it survives Klipper being stopped and starts
Klipper again at the end. That needs `sudo` without a password for the
MainsailOS user (the flash script also stops and starts the Klipper
service). One line, once, on the Pi:

```bash
echo "$(id -un) ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/010_$(id -un)-nopasswd >/dev/null && sudo chmod 440 /etc/sudoers.d/010_$(id -un)-nopasswd
```

Mainsail shows the printer offline for a minute
or two; progress is in `logs/flash_skr3.log` under Machine. The macro
refuses to run while printing. It works for whatever user you set in
Raspberry Pi Imager (the command resolves the user and home directory at
run time) and assumes this repo at `~/Ender-3-Pro-SKR-3-EZ-Sprite-Tool-Head`;
edit that one path in `shell.cfg` otherwise. Moonraker will mark the
Klipper repo as having an untracked file; that is the extra, and it is
harmless.

## 6. Recovery

Katapult cannot be bricked by a bad Klipper build: a bad application just
means the board sits in Katapult (`katapult_` on USB, status LED blinking)
waiting for the next `flashtool.py`. If even Katapult is gone, BOOT0 +
RESET gives DFU and section 2 can be repeated, or BTT's original
bootloader can be put back the same way from the `SKR-3` GitHub repo.

## 7. Keeping BTT's bootloader instead (SD card)

Skip section 2. Build as in section 3, then put `~/klipper/out/klipper.bin`
on a FAT32 card (≤ 32 GB) in the root, named exactly **`firmware.bin`**.
Board unpowered, card in the board's micro-SD slot, power on, wait
10–15 s while the status LED blinks, power off. On a computer the card now
shows `FIRMWARE.CUR`; if it still says `firmware.bin`, the name, the
bootloader offset or the card format is wrong. Repeat for every update.

To get the file off the Pi without scp: copy it into the config folder
(`cp ~/klipper/out/klipper.bin ~/printer_data/config/firmware.bin`),
download it from Mainsail → Machine, then delete it there.

## If the board does not show up at all

- USB/CAN switch next to the USB port in the **USB** position.
- Another cable, another Pi port; `dmesg | tail` says whether anything
  enumerated.
- Wrong processor model in menuconfig (section 1).
- In doubt, DFU (BOOT0 + RESET) always works and section 2 can be repeated.

Sources: BTT's Klipper README for the SKR 3 (build options), Katapult's
README (`flashtool.py`, double-click entry), and a working SKR 3 EZ
Katapult setup for the DFU address and the 128KiB application offset.
