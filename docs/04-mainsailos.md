# 04 · MainsailOS on the Raspberry Pi 4

MainsailOS is a Raspberry Pi OS Lite image with Klipper, Moonraker, Mainsail
and Crowsnest (webcam) preinstalled. Nothing has to be compiled on the host
except the MCU firmware in `docs/03-firmware-flash.md`.

## 1. Image the card

1. Install **Raspberry Pi Imager**.
2. **Choose Device** → Raspberry Pi 4.
3. **Choose OS** → *Other specific-purpose OS* → *3D printing* →
   *MainsailOS* → the 64-bit Lite build.
4. **Choose Storage** → your microSD.
5. **Next** → *Edit Settings*:
   - Hostname: `mainsailos` (or `ender3`)
   - Username / password: pick a user. Nothing in this repo depends on the
     name: every path is written as `~/...` and resolves to that user's home.
   - Wi-Fi SSID/password + country (or use Ethernet; wired is more reliable
     for a printer).
   - Services tab: **enable SSH** with password auth.
6. Write.

## 2. First boot

Insert the card, power the Pi from its own 5 V supply, wait ~2 minutes.
Open <http://mainsailos.local> (or the IP from your router). Mainsail loads
with Klipper reporting an error about a missing `printer.cfg`, which is
expected. Then SSH in and clone this repository into the folder name the
scripts expect:

```bash
cd ~ && git clone https://github.com/ryanpie86/Ender-3-Pro-SKR-3-EZ-Sprite-Tool-Head.git Ender-3-Pro-SKR-3-EZ-Sprite-Tool-Head
```

## 3. Drop in the config

In Mainsail → **Machine** tab (the folder icon):

1. With this repo cloned on the Pi (§2), copy the Klipper files straight in (Mainsail's upload button does the same):

   ```bash
   cp ~/Ender-3-Pro-SKR-3-EZ-Sprite-Tool-Head/config/{printer.cfg,macros.cfg,speed_test.cfg,KAMP_Settings.cfg,adxl.cfg,shell.cfg} ~/printer_data/config/
   ```

   `moonraker.conf`: if MainsailOS's copy is still there, add
   `enable_object_processing: True` under `[file_manager]` and the KAMP
   update-manager block from `config/moonraker.conf`. If it is missing
   (Mainsail then shows *Cannot connect to Moonraker* and
   `systemctl status moonraker` loops on *Configuration File Not Found*),
   copy the repo's file in whole; it is complete, MainsailOS entries
   included:

   ```bash
   cp ~/Ender-3-Pro-SKR-3-EZ-Sprite-Tool-Head/config/moonraker.conf ~/printer_data/config/moonraker.conf
   ```

   Moonraker restarts itself within a few seconds.
2. In `printer.cfg`, replace `<serial>` in `[mcu] serial:` with the full
   path from `ls /dev/serial/by-id/` (`docs/03-firmware-flash.md` §4). The
   same goes for `adxl.cfg` when the accelerometer is used.
3. `[include shell.cfg]` ships commented out: leave it so until the
   `gcode_shell_command` extra is installed (`docs/03` §5b), or Klipper
   stops with *Section 'gcode_shell_command' is not a valid config section*.
4. In Mainsail, **Save & Restart** (or `RESTART` from the console).
   Until KAMP is installed (§4b) Klipper will stop on the missing
   `KAMP/Smart_Park.cfg` include; that is the next step, not a fault.

Klipper should come up with the board connected. If it says
`mcu 'mcu': Unable to connect`, the board is unpowered, the serial path is
wrong, or the firmware didn't take.

If Mainsail instead says *Moonraker can't connect to Klipper* while
`systemctl status klipper` is happily running, Moonraker is looking for
Klipper's socket in the wrong place (its built-in default is
`/tmp/klippy_uds`; MainsailOS puts the socket in `~/printer_data/comms/`).
`curl -s localhost:7125/server/config` shows the `klippy_uds_address` it
is using. The repo's `moonraker.conf` sets it; on an older copy add it:

```bash
sed -i "/^\[server\]/a klippy_uds_address: $HOME/printer_data/comms/klippy.sock" ~/printer_data/config/moonraker.conf && sudo systemctl restart moonraker
```

## 4. Per-print-area bed mesh (adaptive mesh)

`START_PRINT` probes only the area the current print covers. Two things
outside `printer.cfg` make that work:

1. **Moonraker** must parse the object outlines out of every uploaded file.
   In Mainsail → Machine → `moonraker.conf`, make sure this is present
   (MainsailOS ships it on, check it hasn't been turned off):

   ```ini
   [file_manager]
   enable_object_processing: True
   ```

2. **The slicer** must label objects. PrusaSlicer / SuperSlicer / OrcaSlicer:
   Print Settings → Output options → *Label objects* = **Klipper** (Orca:
   "Exclude objects (Klipper)"). Cura: install the "Klipper Preprocessor" or
   use Moonraker's processing, which also works on plain Cura output.

If a file has no object data, Klipper logs that and falls back to the full
5 × 5 mesh, so nothing breaks.

## 4b. KAMP: Smart Park and Line Purge

The adaptive mesh above is Klipper's own (KAMP's meshing was merged into
Klipper in 2023 and KAMP's README says to use the native one). What
`START_PRINT` takes from KAMP is **Smart Park**, which waits for the hotend
beside the print area instead of across the bed, and **Line Purge**, which
lays the purge line just in front of the print area. Both read the same
object outlines as the mesh, so the two slicer/Moonraker steps above are
all they need. Install once, on the Pi:

```bash
cd ~ && git clone https://github.com/kyleisah/Klipper-Adaptive-Meshing-Purging.git KAMP
```

```bash
ln -s ~/KAMP/Configuration ~/printer_data/config/KAMP
```

Then put this repo's `config/KAMP_Settings.cfg` in `~/printer_data/config/`
(it replaces the default one KAMP's install script would copy; ours
includes only Smart Park and Line Purge, with the purge sized for the 0.8
nozzle). `printer.cfg` already includes it, and `moonraker.conf` has the
update-manager entry so Mainsail keeps KAMP current. `RESTART`, then
`SMART_PARK` and `LINE_PURGE` exist as commands.

## 4c. Keeping your config

Edit the files in Mainsail's Machine tab; `SAVE_CONFIG` appends calibration
results to the bottom of `printer.cfg`. If you keep your own copy of this
repository, copy the cfg files back into it after a change; nothing in the
config depends on where the repository lives except the two shell-command
paths in `shell.cfg`, which assume `~/Ender-3-Pro-SKR-3-EZ-Sprite-Tool-Head`.

## 5. Things worth setting once

- **Dashboard macro groups**: import `config/backup-mainsail.json` once.
  Mainsail → Settings → General → **Backup & Restore → Restore**, pick the
  file, tick *Macros*, *Dashboard*, *Control* and *Presets* (leave the
  rest), Restore. That creates five macro groups on the dashboard: **SETUP HELPERS**
  (BUZZ_X/Y/Z/Z1/E, BUZZ_ALL, BEEP), **Calibrate** (LEVEL_GANTRY,
  SCREWS_TILT, BED_LEVEL_CHECK, PID_HOTEND, PID_BED, TEST_SPEED, BENCHMARK,
  MAX_ACCEL_TEST, MAX_VELOCITY_TEST, MAX_SCV_TEST, ADXL_CHECK, SHAPER_Y,
  SHAPER_X, SHAPER_PLOT), **Printing Macros** (M600, Z_LOCK, also shown
  while paused), **MAINTENANCE** (FLASH_MCU), **NOZZLE / FILAMENT**
  (NOZZLE_0_2 … NOZZLE_0_8, PA_PLA_PETG, PA_OFF_TPU), and hides START_PRINT,
  END_PRINT, G28, M300 and the KAMP internals from the plain macro list. Groups live
  in Mainsail's own settings, which is why they are a backup file and not a
  line in `printer.cfg`. The same file adds **temperature presets** to the
  heater panel's preset menu: Bed off / 30 / 60 and Nozzle off / 190 / 215 /
  230, each setting only its own heater, plus the stock *Cooldown* entry
  (`TURN_OFF_HEATERS`). Edit them under Settings → Presets.
- **Moonraker update manager** is already configured for Klipper, Moonraker
  and Mainsail. Update from Mainsail → Machine → Update Manager. It updates
  the host side only; when Klipper then reports an MCU protocol mismatch,
  run `tools/flash_skr3.sh` on the Pi (`docs/03-firmware-flash.md` §5).
- **Timezone / NTP**: `sudo raspi-config` → Localisation if timestamps look
  odd.
- **Pi temperature in Mainsail**: `printer.cfg` already includes
  `[temperature_sensor raspberry_pi]` and the board MCU sensor.
- **Webcam**: plug a USB webcam in, Crowsnest picks it up at
  `/webcam/?action=stream`, and Mainsail's webcam settings default to that.
- **Power**: an underpowered Pi throws `Timer too close` / USB resets
  under load. A proper 5 V 3 A supply and a short USB cable to the board
  fix most "random disconnect" reports.

## 6. Backups

Mainsail → Machine → the config folder can be downloaded as a zip. Do it
after PID tuning, probe calibration and the shaper run: those results live
in the `#*# <---------------------- SAVE_CONFIG ---->` block that Klipper
appends to `printer.cfg`, and nowhere else.
