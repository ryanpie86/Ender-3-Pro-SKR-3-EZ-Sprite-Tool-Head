# Config

Klipper and Moonraker files for the build, installed into
`~/printer_data/config` on the Pi as `../docs/04-mainsailos.md` describes.
Before the first start: put your board's serial path in `printer.cfg`
(`[mcu] serial:`), and leave `[include shell.cfg]` commented out until the
`gcode_shell_command` extra is installed.

| File | Content |
|---|---|
| `printer.cfg` | Klipper config |
| `macros.cfg` | START_PRINT, END_PRINT, M600, LEVEL_GANTRY, deferred runout, nozzle and PA buttons, enclosure fan control, PID helpers, BEEP, TEST_SPEED |
| `shell.cfg` | FLASH_MCU and SHAPER_PLOT (gcode_shell_command) |
| `adxl.cfg` | Pico accelerometer MCU; included only while it is plugged in |
| `KAMP_Settings.cfg` | KAMP Smart Park and Line Purge |
| `speed_test.cfg` | CrydTeam speed, acceleration and SCV tests |
| `moonraker.conf` | Moonraker: socket path, object processing, update manager |
| `backup-mainsail.json` | Mainsail UI: macro groups, hidden macros, temperature presets |

## How the special features behave

**Fans.** Three fans on three board headers, each with its own rule:

| Fan | Header | Runs when | Why |
|---|---|---|---|
| Part cooling blower (Sprite "XFan") | FAN0 | At the speed the slicer asks for (`M106`). Off during the first layer if the slicer says so. | Cools the plastic as it is laid down. |
| Hotend heatsink fan (Sprite "Fan") | FAN1 | Whenever the hotend is above 50 °C, until it cools below; full speed. Klipper `heater_fan`. | Stops heat creeping up the heatbreak. On a stock board this fan runs all the time; here the printer is silent when cold. |
| Enclosure fan, 40 mm in the box's front wall | FAN2 | While any motor is enabled or a heater has a target, plus 60 s after that stops; and whenever the board's MCU temperature sensor reads 45 °C or more, until it is back below 40 °C. Full speed. | Keeps the drivers and the MCU cool under load and clears heat that builds up in a closed box even when idle. A small loop in `macros.cfg` checks these conditions every 10 s; Mainsail shows the fan as a slider, but the loop overrides a manual change within 10 s. |

All three run on 24 V through the board's V-FAN jumper. The driver-fan
headers (MFAN) are unused: the enclosure fan covers the drivers.

**Gantry levelling.** Before every print, `Z_TILT_ADJUST` probes a point
above each lead screw and moves the two Z motors independently until the
X gantry is parallel to the bed within 0.025 mm, up to ten rounds. Any
plain `G28` does it too when the gantry has not been levelled since the
motors were last powered. The bed's front-to-back tilt is still the four
knobs; `SCREWS_TILT` probes beside each knob and prints how far to turn it.

**Adaptive mesh.** `START_PRINT` reads the objects' footprint from the
G-code (Moonraker's object processing) and probes only that area, with the
full 5 × 5 density over a full bed. KAMP then parks the head beside the
print area while the nozzle heats and purges a line just in front of it.

**Runout.** The sensor sits at the top of the frame, a tube length before
the extruder. On runout the print carries on until that length of filament
has been extruded, then `M600` pauses, parks at the back and retracts, with
the tail still in the extruder gears. Measure your tube once and set
`tail_mm` in `macros.cfg`. A sensor that sees filament again before then is
treated as a false trigger.

**Remembered settings.** The NOZZLE and PA buttons save their choice in a
small file Klipper keeps beside the config, and a start-up macro re-applies
it, so a restart does not forget which nozzle is fitted or that pressure
advance is off for TPU.

**Firmware updates.** Klipper on the Pi updates through Mainsail's update
manager like any MainsailOS install. When the board's firmware falls behind
it, Mainsail says so, and the FLASH_MCU button rebuilds Klipper for the
board, drops it into the Katapult bootloader, flashes it over the USB cable
and restarts Klipper, all unattended. A bad flash cannot brick the board:
Katapult keeps running and the button can be pressed again.

**Motors and idle.** `END_PRINT` turns the heaters off, presents the bed and
releases all motors. If the printer sits idle for 12 hours with heaters on
or motors held, the heaters go off and the motors release.

**Beeper.** The stock LCD's beeper is wired as a PWM pin named with a
leading underscore so Mainsail does not show it as a slider; the BEEP
button and `M300` drive it.

## Dashboard

The Mainsail backup sets up these macro groups:

| Group | Buttons |
|---|---|
| SETUP HELPERS | BUZZ_X/Y/Z/Z1/E, BUZZ_ALL, BEEP |
| Calibrate | LEVEL_GANTRY, SCREWS_TILT, BED_LEVEL_CHECK, PID_HOTEND, PID_BED, TEST_SPEED, BENCHMARK, the CrydTeam MAX_VELOCITY / MAX_ACCEL / MAX_SCV tests, ADXL_CHECK, SHAPER_X, SHAPER_Y, SHAPER_PLOT |
| Printing Macros | M600, Z_LOCK |
| MAINTENANCE | FLASH_MCU: rebuilds Klipper and flashes the SKR 3 EZ (and the Pico when plugged in) over USB. Press it when Mainsail reports an MCU protocol mismatch after a Klipper update. |
| NOZZLE / FILAMENT | NOZZLE_0_2 … NOZZLE_0_8 size the KAMP purge line for the nozzle fitted; PA_PLA_PETG and PA_OFF_TPU set pressure advance. Both remembered across restarts. |

Temperature presets: bed off / 30 / 60, nozzle off / 190 / 215 / 230.

## Slicer

Start G-code in Cura: `START_PRINT EXTRUDER_TEMP={material_print_temperature_layer_0} BED_TEMP={material_bed_temperature_layer_0}`
(PrusaSlicer, SuperSlicer and Orca: `START_PRINT BED_TEMP=[first_layer_bed_temperature] EXTRUDER_TEMP=[first_layer_temperature]`),
end G-code `END_PRINT`, Marlin flavor, **relative extrusion on**. START_PRINT
heats the bed, homes, levels the gantry, meshes only the print area, then
heats the nozzle and purges a line. Keep the temperature variables in the
start line: Cura reads them and leaves heating to the macro.
