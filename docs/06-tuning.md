# 6. Tuning: resonance (input shaper) and pressure advance

Do this after `docs/05-first-power-on.md` is complete and a plain test
print comes out clean. Order: resonance first (it changes how fast corners
are taken), then pressure advance and retraction in the slicer's
calibration tools. The final numbers go back into `config/printer.cfg` in
this repo.

## 6.1 Resonance compensation (input shaper)

The accelerometer is an ADXL345 breakout on a Raspberry Pi Pico (RP2040),
plugged into the Pi by USB. The Pico runs its own Klipper firmware and
shows up as a second MCU, so nothing is plugged into the SKR 3 EZ. Wire the
breakout to the Pico as Klipper's own Pico example does (solder, or a short
ribbon):

| ADXL345 | Pico | Pico pin |
|---|---|---|
| VCC / VIN | 3V3 OUT | 36 |
| GND | GND | 38 |
| CS | GP1 | 2 |
| SDO | GP0 | 1 |
| SDA | GP3 | 5 |
| SCL | GP2 | 4 |

The config is `config/adxl.cfg`; put the Pico's serial path in it.

### Pico firmware (once, and again after a Klipper update)

The Pico's firmware must match the Klipper version on the Pi, like the
SKR 3's. Its build options live in their own file, `config.pico`:

```bash
cd ~/klipper && make KCONFIG_CONFIG=config.pico menuconfig
```

```
    Micro-controller Architecture  (Raspberry Pi RP2040/RP2350)
    Processor model                (rp2040)
    Bootloader offset              (No bootloader)
    Communication interface        (USB)
```

`Q`, `Y`, then:

```bash
make KCONFIG_CONFIG=config.pico clean && make KCONFIG_CONFIG=config.pico -j4
```

First flash, or whenever it does not show up on USB: hold the Pico's
BOOTSEL button while plugging it into the Pi, then

```bash
make KCONFIG_CONFIG=config.pico flash FLASH_DEVICE=2e8a:0003
```

Afterwards it appears as `usb-Klipper_rp2040_<serial>-if00` in
`ls /dev/serial/by-id/`; put that path in `[mcu adxl]` in `adxl.cfg`.
Later updates flash straight over that path without BOOTSEL:

```bash
make KCONFIG_CONFIG=config.pico flash FLASH_DEVICE=/dev/serial/by-id/usb-Klipper_rp2040_<serial>-if00
```

`tools/flash_skr3.sh` (and the FLASH_MCU button) does this for the Pico
too whenever `config.pico` exists and the Pico is plugged in, right after
the SKR 3.

Klipper needs numpy on the Pi for the analysis, once:

```bash
~/klippy-env/bin/pip install -v numpy
```

Two mounts hold the sensor board flat with its header edge toward the
front: one on the bed at its centre (Y measurement, the bed is what shakes
on a bed slinger) and one on the Sprite (X). Any rigid clip or a print-in-
place block that the board screws to will do; the mounts are not part of
this repo. `axes_map: x,y,z` in `adxl.cfg` matches that orientation; if
`ACCELEROMETER_QUERY` shows gravity on X or Y instead of Z, the map needs
changing for your mount.

### Calibrate

Buttons in the Calibrate group; the same commands typed work too.

1. Pico plugged into the Pi; `[include adxl.cfg]` is active in `printer.cfg`.
2. **ADXL_CHECK**: `ACCELEROMETER_QUERY` must show about 9800 (plus or
   minus 10 %) on Z and near zero on X and Y; `MEASURE_AXES_NOISE` well
   under 100 on all three. Gravity on another axis means `axes_map` is
   wrong for the mount.
3. Home. With the bed clear, `G28`. With the bed mount in place nothing may
   probe the centre, so instead:

   ```
   SET_KINEMATIC_POSITION Z=<the gantry's current height, roughly>
   G28.1 X Y
   ```

4. Sensor on the bed mount: **SHAPER_Y**. Sensor on the toolhead mount:
   **SHAPER_X**. Each sweeps 5 to 134 Hz in about two minutes and prints
   the fitted shapers with a `suggested max_accel` for each.
5. **SHAPER_PLOT** renders the newest run of each axis to `shaper_x.png`
   and `shaper_y.png` in the config folder (Machine tab, download). Needs
   matplotlib once: `sudo apt install -y python3-matplotlib`.
6. `SAVE_CONFIG` writes `[input_shaper]` into the auto-save block for both
   axes and restarts. Then set `max_accel` in `[printer]` to the smaller of
   the two suggested values, rounded down.

Measured on the reference build: X peak 47 Hz, MZV 48.2 Hz (0.0 %,
max_accel 6800); Y peak 35 Hz after tensioning the Y belt, MZV 36.2 Hz
(0.0 %, max_accel 3900). `max_accel` is 3900, set by Y. Before the belt
was tensioned Y peaked at 27 Hz and allowed only 1700: a low Y peak means
a slack belt.

Re-run after anything that changes the moving mass or the frame: a new
toolhead, belts, or the printer standing on the TPU feet versus the stock
rubber ones. For the full graphs from the same hardware, Klippain's
Shake&Tune is the usual add-on.

## 6.2 Pressure advance and retraction, in the slicer

Use the slicer's built-in calibration rather than tuning towers. In
OrcaSlicer: **Calibration → Pressure Advance → PA Pattern** (direct drive:
start 0, end 0.08, step 0.005), print, pick the line with the cleanest
corners, and put the value in the filament profile's "Pressure advance"
field. The Sprite lands in the `0.02`–`0.06` range; `printer.cfg` starts
at `0.04` as a default, and the slicer's per-filament value overrides it at
print start.

Then **Calibration → Retraction test** (direct drive: 0 to 1.2 mm, 0.1
steps) and put the result in the filament profile. With
`[firmware_retraction]` enabled in the config, turn on "Use firmware
retraction" in the printer profile so the slicer sends `G10`/`G11` and the
length comes from `retract_length` (start `0.8`), or leave it off and let
the slicer handle retraction itself; pick one, not both.

PA and retraction are per filament. PLA, PETG and TPU each get their own.

## 6.3 Nozzle and filament buttons

The NOZZLE / FILAMENT group on the dashboard remembers two things across
restarts (`variables.cfg`, written by Klipper's `[save_variables]`):

| Button | Sets |
|---|---|
| NOZZLE_0_2 / 0_4 / 0_6 / 0_8 | KAMP purge line for that nozzle: height = nozzle, flow 4 / 8 / 14 / 20 mm³/s, length 15 / 25 / 30 / 40 mm of filament |
| PA_PLA_PETG | pressure advance 0.040, smooth time 0.040 |
| PA_OFF_TPU | pressure advance 0 |

Press the nozzle button after a nozzle change and the filament button
when loading a different material; START_PRINT prints both current values
to the console. `nozzle_diameter` in `[extruder]` is not changed: Klipper
only uses it for extrusion sanity checks, and `max_extrude_cross_section`
is set explicitly. Line widths and speeds come from the slicer profile.

## 6.4 Then raise the limits

With input shaper on, `max_accel` goes to the smaller of the two
`suggested max_accel` values from `SHAPER_CALIBRATE` (3900 on the
reference build, set by Y) and `max_velocity` to 80 % of the lower
motor-skip ceiling from the tests below (255). Slicer speeds, not these
limits, decide how fast it actually prints.

To find the mechanical ceiling, the CrydTeam tests in `config/speed_test.cfg`
(Calibrate group on the dashboard) drive one axis and re-home after each
step; a skipped step stops the test with an error:

1. `MAX_VELOCITY_TEST AXIS=X MIN_VELOCITY=100 MAX_VELOCITY=400 VELOCITY_INCREMENT=50`, then `AXIS=Y`.
2. `MAX_ACCEL_TEST AXIS=X MIN_ACCEL=1000 MAX_ACCEL=10000 ACCEL_INCREMENT=1000 SPEED=200`, then `AXIS=Y`.
3. `MAX_SCV_TEST MIN_SCV=5 MAX_SCV=20 SPEED=150 ACCEL=4000` for `square_corner_velocity`.

Set `[printer]` limits with margin below the last passing step. Measured
at 3900 mm/s²: X passes 320 mm/s and skips at 340, Y passes 420
and skips at 440; `max_velocity` 255 is 80 % of X's ceiling. MAX_ACCEL_TEST
at 150 mm/s: X passes 7000 and skips at 9000, Y passes 9000; the shaper's
3900 is the binding limit, so `max_accel` stays there. The tests
need `[endstop_phase stepper_x]` and `[endstop_phase stepper_y]` in
`printer.cfg`, which are there.

## Checklist back into the repo

- `[input_shaper]` values (from SAVE_CONFIG) → `config/printer.cfg`
- `max_accel` → `[printer]`
- default `pressure_advance` / `retract_length` → `[extruder]` /
  `[firmware_retraction]` (the per-filament values live in the slicer)
