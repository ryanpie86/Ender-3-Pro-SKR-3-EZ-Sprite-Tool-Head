# Docs

Read in order for a build from scratch; each file stands on its own for a
single job.

| Path | Content |
|---|---|
| `01-bom.md` | Bill of materials |
| `02-wiring.md` | Jumpers, then every harness → SKR 3 EZ port → Klipper pin |
| `03-firmware-flash.md` | Katapult, Klipper build, flashing from the Pi, FLASH_MCU setup, recovery, SD-card alternative |
| `04-mainsailos.md` | Pi image, config install, Moonraker, KAMP, Mainsail backup |
| `05-first-power-on.md` | Commissioning checklist and common faults |
| `06-tuning.md` | Pico firmware, input shaper, speed tests, pressure advance, retraction |
| `mini-e3-to-skr3ez-cables.html` / `.pdf` | Pictorial cable-by-cable guide. The "from" board pictured is an SKR Mini E3 V3; a stock Creality 4.2.x board uses the same JST-XH plugs on the same harnesses, so the SKR 3 EZ side is what matters |
| `cr-touch-repin.md` / `.html` / `.pdf` | CR Touch 5-pin → SERVOS + Probe headers, pin by pin |
| `skr3ez-connections.html` / `.pdf` | Printable board diagram with every cable, pin and jumper |
| `renders/` | The whole-machine render and the script that draws it |

## What this build adds over a stock Ender 3 Pro

**Electronics and firmware**
- 32-bit SKR 3 EZ (STM32H723) in place of the 8-bit Creality board, with five plug-in TMC2209 drivers in UART mode: motor currents set in software, silent stealthChop, and one driver per axis including a fifth for the second Z motor.
- Klipper instead of Marlin, hosted on a Raspberry Pi 4 that sits under the stock screen in a printed enclosure ([Thingiverse thing 4586351](https://www.thingiverse.com/thing:4586351)): the motion planning runs on the Pi, the board only steps. Mainsail web interface from any browser on the network, Moonraker API, G-code upload and print start without an SD card.
- Katapult bootloader: Klipper firmware updates over the USB cable from the Pi, started from a dashboard button (FLASH_MCU). No micro-SD shuffle, no brick risk.
- Stock 12864 LCD and beeper kept and working under Klipper.

**Motion and levelling**
- Dual Z: a second lead screw and motor on the right upright, each on its own driver, and `z_tilt` levelling that squares the X gantry to the bed automatically before every print. No more sagging right side.
- CR Touch probe: probed Z homing at the bed centre, a bed mesh, and a screw-assist routine (SCREWS_TILT) that tells you how far to turn each bed knob.
- Adaptive meshing: each print probes only the area it will cover, so a small part takes seconds to mesh and a full bed gets the full grid.
- Input shaper, calibrated with an ADXL345 accelerometer on a Pico over USB: ringing cancelled, acceleration 3900 mm/s² against the stock firmware's 500, with measured motor-skip ceilings for the velocity limit.
- Pressure advance (direct drive), firmware retraction, arc support, exclude-object (cancel one object of a plate mid-print), pause and resume.

**Toolhead**
- Creality Sprite Pro direct-drive extruder: all-metal hotend to 300 °C, dual-gear drive, 0.8 mm nozzle fitted, short filament path, so flexible filaments work. Replaces the Bowden setup and its PTFE-lined 240 °C hotend.
- Hotend heatsink fan under thermal control (runs when the hotend is above 50 °C) instead of always on.

**Filament handling**
- Filament runout sensor at the top of the frame. The print does not stop at the sensor: it runs until the filament still in the tube is used, then pauses, parks and waits with the heaters on. Load new filament, RESUME.
- M600 filament change from the dashboard or from a slicer "pause at layer".
- Nozzle and material buttons: the KAMP purge line sized for 0.2 / 0.4 / 0.6 / 0.8 nozzles, pressure advance on or off for TPU, both remembered across restarts.

**Printed hardware**
- Board enclosure that hangs under the left foot rail on slot keys, no bolts, with a 40 mm fan that runs when motors or heaters are active and whenever the board's MCU is warm, printed feet that lift the frame, a key filler and a rail end cap.
- Cable mast on the 2020 top bar with a retractable badge reel and a printed roller shackle that keeps the Sprite's flat cable off the bed and takes up the slack as Z moves.

**Dashboard**
- One-button PID tuning for hotend and bed, gantry levelling, bed-screw assist, shaper calibration per axis with graph export, CrydTeam speed, acceleration and corner-velocity tests, motor buzz tests, a beep, temperature presets, and FLASH_MCU.
- Temperature readouts for the Pi and the board's MCU; motors release at the end of a print and after 12 hours idle.

## Measured on the reference build

Starting points, not gospel; the docs say how to measure your own.

- Probe repeatability (CR Touch): range 0.015 mm, standard deviation 0.005. `samples_tolerance` 0.03 and `z_tilt retry_tolerance` 0.025 follow from it.
- Input shaper: X MZV 48.2 Hz, Y MZV 36.2 Hz after tensioning the Y belt (27 Hz before). `max_accel` 3900.
- Motors skip at 340 mm/s on X and 440 on Y; `max_velocity` 255.
- Bed crown 0.04 mm along the centreline, handled by the mesh, which is why `z_tilt` uses two points on the lead-screw lines and not a centre point.

## Things that bite

- Motor header coil order is 2B 2A 1A 1B on the SKR 3 EZ, the same as Creality's and the SKR Mini E3's, so stock cables plug straight in. Some dual-Z kit cables are wired straight through with the coil pairs split; the motor grinds until re-crimped A-A-B-B.
- Sprite Pro fan leads: **XFan is the part-cooling blower, Fan is the heatsink fan.**
- STEPPER_BUZZ cannot show an extruder's direction; check it with filament loaded.
- Klipper's `M84` ignores axis letters and releases every motor.
- Moonraker's default socket path is `/tmp/klippy_uds`; MainsailOS puts it under `~/printer_data/comms/`. `moonraker.conf` sets `klippy_uds_address`.
- Mainsail shows a PWM `output_pin` as a slider unless its name starts with an underscore (`_beeper`).
- Klipper refuses SAVE_CONFIG for an option also set in the main file, so `[input_shaper]` is left empty until you calibrate.
- The 4040 foot rails' end cavities are cross shaped, not round, whatever the CAD says; the end cap's pegs are crosses.
