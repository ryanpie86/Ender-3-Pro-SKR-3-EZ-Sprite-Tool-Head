# 05 · First power-on and commissioning

Work through this in order with the hotend and bed **cold** and your hand on
the power switch. Each step is something that has bitten people doing this
exact swap.

The numbers in the config are the reference build's (same frame, Sprite
Pro and CR Touch): X/Y endstop positions and limits, probe offsets and
`z_offset`, extruder `rotation_distance`, both PIDs, bed-mesh and screw
positions. Expect yours to differ by a little, and treat each step below
as a measurement, not a check. Input shaper is measured in
`docs/06-tuning.md`.

## 0. Bench check (board out of the printer, or at least nothing heating)

With nothing plugged into the board, Klipper connects to the MCU, reads the
whole config and then shuts down with `ADC out of range` and both sensors
at about −99 °C: an open thermistor input reads as that, and `min_temp` is
0. That is the expected result of a bare-board bench test and proves the
USB link, the firmware and the config. To go further on the bench, plug the
hotend thermistor into **TH0** and the bed thermistor into **TB** (or a
100 kΩ resistor into each, which reads as ~25 °C), then `FIRMWARE_RESTART`.
Also expected on USB power alone: empty `tmcuart_response` lines in
`klippy.log`, because the EZ2209s' logic is fed from the motor voltage;
they answer once 24 V is on DCIN.

- [ ] Meter across DCIN: 24 V, correct polarity.
- [ ] Mainsail shows the MCU connected, no config errors.
- [ ] The stock LCD shows Klipper's status screen; the knob scrolls, the
      click selects, and `BEEP` in the console sounds the buzzer. A blank
      screen means the EXP1 mapping in `[display]` is off (docs/02-wiring.md).
- [ ] Mainsail temperatures: hotend and bed read room temperature (±3 °C).
      A reading of ~0 °C or 300+ °C means an open/shorted thermistor or the
      wrong header.

## 1. Motor directions

Press **BUZZ_X**, **BUZZ_Y**, **BUZZ_Z**, **BUZZ_Z1** and **BUZZ_E** on the
Mainsail dashboard one at a time and watch the motor (or **BUZZ_ALL** for
all five in turn with a beep before each). They sit in the **SETUP
HELPERS** group once `config/backup-mainsail.json` is imported
(docs/04-mainsailos.md, section 5). The console equivalent is
`STEPPER_BUZZ STEPPER=stepper_x` and so on.

Each motor moves forward 1 mm then back, ten times. The **first** move must be:

| Stepper | "Forward" means |
|---|---|
| stepper_x | hotend moves **right** |
| stepper_y | bed moves **toward the front** (the nozzle ends up over the back of the bed, which is +Y) |
| stepper_z / stepper_z1 | gantry moves **up** (both sides!) |
| extruder | filament pushed **toward the nozzle** (cold, so watch the Sprite's drive gear through the idler window) |

Wrong direction → toggle the `!` on that stepper's `dir_pin` in
`printer.cfg`, save & restart, buzz again. Both Z motors must go the same way
or `Z_TILT_ADJUST` will twist the gantry.

## 2. Endstops

```
QUERY_ENDSTOPS
```

Expect `x:open y:open z:open`. Press each switch by hand and query again:
that axis should read `TRIGGERED`. If one is always TRIGGERED, the switch is
wired to +5 V instead of GND, or the plug is on the wrong header.

## 3. Probe

```
QUERY_PROBE
```

Expect `probe: open`. Push the pin up with a fingernail → `TRIGGERED`.
Then:

```
BLTOUCH_DEBUG COMMAND=pin_down
BLTOUCH_DEBUG COMMAND=pin_up
BLTOUCH_DEBUG COMMAND=self_test
```

If the pin doesn't move, the SERVOS wiring (PE5) is wrong; if it moves but
never triggers, the Probe header (PC13) wiring is wrong.

### 3b. Filament runout sensor

```
QUERY_FILAMENT_SENSOR SENSOR=runout
```

With filament through the sensor expect `Filament Sensor runout: filament
detected`; pull it out and query again, expect `filament not detected`. If
the two are swapped, change `switch_pin: PC2` to `!PC2` in `printer.cfg`
and `RESTART`. Then measure the filament path from the sensor's switch to
the Sprite's drive gear, along the tube, subtract 30 mm, and put it in
`variable_tail_mm` under `[gcode_macro _RUNOUT]` in `macros.cfg`: on runout
the print continues for that much filament before M600 pauses it. A false
trigger that clears itself is ignored; one that does not ends in that pause,
recoverable with RESUME. To silence the sensor while tuning:

```
SET_FILAMENT_SENSOR SENSOR=runout ENABLE=0
```

## 4. Home — with the finger-on-the-switch test

```
G28
```

(On the very first home the automatic gantry level will also run; keep a
finger ready on the probe for that too.) After it finishes, look at where
the nozzle sits over the bed: the config carries the reference build's
X = 1 and Y = −11 endstop positions, so X=0 / Y=0 should be the bed
corner. If it is off, adjust `position_endstop` and `position_min` on that
axis by the difference.

Watch Z. Be ready to trigger the probe by hand before the nozzle hits the
bed, and to kill power. The config homes Z over the centre of the bed with
the probe (`[safe_z_home]`).

## 5. Probe Z offset

```
PROBE_CALIBRATE
```

Use `TESTZ Z=-.1` / `TESTZ Z=+.1` until a sheet of paper drags lightly,
then `ACCEPT` and `SAVE_CONFIG`. This writes `[bltouch] z_offset` to the
end of `printer.cfg`.

## 6. Dual-Z gantry levelling

```
LEVEL_GANTRY
```

It probes left and right on the lead-screw lines, adjusts the two motors,
repeats until within `retry_tolerance` (0.025 mm), then re-homes Z. If it diverges, one Z motor is
turning the wrong way (back to step 1) or the `z_positions` in `[z_tilt]`
are swapped left/right. (The right-hand kit is mirror-image to the left, so
the positions are not an assumption any more.)

From here on it is automatic: `G28` (a plain home-all) levels the gantry
whenever Klipper has not applied a tilt correction since the Z motors were
last powered down, and `START_PRINT` forces a fresh level every print.

`Z_TILT_ADJUST` only makes the X gantry parallel to the bed. Front-to-back
is the four bed knobs. With the lead screws level, press **SCREWS_TILT** on
the Mainsail dashboard (or type it): it re-levels the gantry, probes beside
each screw and prints a table like `front right : adjust CW 00:20`. Turn the
knobs as told, run it again, until all four read `00:05` or less. The screw
positions are the ones measured on the reference build with the SKR Mini E3, so
they should land on the screws without a `Move out of range`.

## 7. PID tuning

```
PID_CALIBRATE HEATER=extruder TARGET=210
PID_CALIBRATE HEATER=heater_bed TARGET=60
SAVE_CONFIG
```

(Part fan on 100 % for the hotend run if you print with it on.)

## 8. Bed mesh

```
LEVEL_GANTRY
BED_MESH_CALIBRATE
SAVE_CONFIG
```

The `START_PRINT` macro levels the gantry and then probes an adaptive mesh
over just the print area every print (`BED_MESH_CALIBRATE ADAPTIVE=1`), so
a saved full mesh is mostly for inspection. Set up the slicer and Moonraker
side of that per `docs/04-mainsailos.md` §4.

## 9. Extruder rotation distance

Mark filament 120 mm above the Sprite's inlet, heat to 200 °C, run:

```
M83
G1 E100 F60
```

Measure what's left. New `rotation_distance = old × (measured / 100)`.
Repeat until 100 mm commanded = 100 mm fed.

## 10. First print

Something small and flat. Two things first:

- Press the NOZZLE button for the nozzle actually fitted (a new Sprite Pro
  ships with 0.4 mm: NOZZLE_0_4) and set `nozzle_diameter` in `[extruder]`
  to match; the config and the purge defaults are for the reference
  build's 0.8 mm nozzle.
- The limits in `[printer]` are the reference build's tuned values. Until
  your own shaper run, type `SET_VELOCITY_LIMIT ACCEL=1500` before the
  print, or ringing will show on an untuned frame.

Once it prints cleanly, move on to `docs/06-tuning.md`: input shaper
(resonance), pressure advance, retraction.

## Common faults

| Symptom | Likely cause |
|---|---|
| `TMC 'stepper_x' reports error: ... DRV_STATUS` / `Unable to read tmc uart` | Driver not seated, or wrong `uart_pin` for that socket |
| `Move out of range` on Z_TILT_ADJUST | `points` + probe offset put the nozzle outside `position_max`; adjust `points` |
| Mesh looks like a saddle | Gantry not square; run `Z_TILT_ADJUST` first and check the X gantry eccentric nuts |
| `Heater extruder not heating at expected rate` | Thermistor on the wrong header, loose heater ferrule, or PID not tuned |
| MCU disconnects when the bed heats | Bad USB cable / under-powered Pi |
