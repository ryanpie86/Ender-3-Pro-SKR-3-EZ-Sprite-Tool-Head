# Ender 3 Pro · SKR 3 EZ · Sprite Pro · Klipper

A complete, working Klipper build for a Creality Ender 3 Pro on a BIGTREETECH
SKR 3 EZ mainboard, with a Creality Sprite Pro direct-drive toolhead, CR Touch,
dual Z motors, a filament runout sensor and MainsailOS on a Raspberry Pi 4.
Everything needed to reproduce it is here: wiring, firmware, configs, the
Mainsail dashboard, and the printed hardware (board enclosure and a cable
mast) as Fusion 360 scripts and ready STLs.

Firmware updates need no SD card: Katapult is flashed to the board once, and
after that a dashboard button rebuilds and flashes Klipper over USB.

![The build on the frame](docs/renders/assembled-machine.png)

*Blue box with orange lid: the board enclosure under the left foot rail. Dark
blue: TPU feet on the rail ends. Red: the rail end cap. Sand: the cable mast on
the top bar, with the retractable reel and the roller shackle carrying the
Sprite's flat cable. The frame itself is drawn as plain boxes; the printed
parts are the real geometry. `docs/renders/render_machine.py` regenerates it.*

## Hardware

| Item | Choice |
|---|---|
| Printer | Creality Ender 3 Pro, 24 V |
| Mainboard | BIGTREETECH SKR 3 EZ. Many ship with an **STM32H723** although BTT advertises an H743; read the chip before building firmware. |
| Drivers | 5 × BTT EZ2209 in UART mode: X, Y, Z left, Z right (E1 socket), extruder |
| Bootloader | Katapult, flashed once over DFU; Klipper updates from the Pi over USB |
| Host | Raspberry Pi 4, MainsailOS (Klipper + Moonraker + Mainsail), mounted under the stock screen in a printed enclosure ([Thingiverse thing 4586351](https://www.thingiverse.com/thing:4586351)), one USB cable to the board |
| Toolhead | Creality Sprite Pro direct drive, 0.8 mm nozzle, CR Touch on its bracket |
| Z axis | Two motors, two drivers, `[z_tilt]` on the two lead-screw lines, levelled before every print |
| Filament sensor | Mechanical runout switch at the top of the frame; the print continues until the filament in the tube is used, then pauses |
| Display | Stock Creality 12864 LCD with beeper on EXP1 |
| Accelerometer | ADXL345 on a Raspberry Pi Pico over USB, a second Klipper MCU, for input shaper calibration |

## Build procedure

Each step points at the document with the detail.

0. **Print first.** While the printer still runs stock, print everything in `enclosure/stl` and the three small parts of `cable_mast/out`; the mast itself needs a 310 mm bed. The TPU feet are the hardest print on a Bowden machine, so do them last or borrow a direct-drive printer.
1. **Parts.** `docs/01-bom.md`. The fifth EZ2209 and the long right-Z motor cable are the easy ones to miss.
2. **Board prep.** Jumpers, switches and drivers: `docs/02-wiring.md`, first section.
3. **Pi.** Image MainsailOS and clone this repository on the Pi: `docs/04-mainsailos.md` §1–2. The bench flash needs the Pi running.
4. **Bench flash.** Katapult over DFU, then build Klipper and flash it over USB: `docs/03-firmware-flash.md` §1–4. Note the `/dev/serial/by-id/` path and put it in `config/printer.cfg`. Then finish `docs/04`: config files, Moonraker settings, KAMP, the `gcode_shell_command` extra, the Mainsail backup.
5. **Enclosure.** Print the base, lid, four TPU feet, filler and cap; fit the board and fan; hang the box under the left foot rail: `enclosure/README.md`.
6. **Wiring.** Every harness to its SKR 3 EZ port: `docs/02-wiring.md`, with the pictorial pages `docs/mini-e3-to-skr3ez-cables.pdf`, `docs/cr-touch-repin.pdf` and the printable board diagram `docs/skr3ez-connections.pdf`.
7. **Commissioning.** Cold checks, motor directions, endstops, probe, homing, gantry level, PID, first print: `docs/05-first-power-on.md`.
8. **Tuning.** Input shaper with the Pico accelerometer, then pressure advance and retraction: `docs/06-tuning.md`.
9. **Cable mast.** Mast, shackle, pin and roller for the Sprite's flat cable, two M5 T-nuts into the 2020 top bar, a retractable badge reel through the tip: `cable_mast/README.md`. The one-piece mast is 302 mm long and needs a printer with a bed of at least 310 mm.

## Where to look

| Folder | What is there | Start with |
|---|---|---|
| `docs/` | The build guides: BOM, wiring with pictorial pages, firmware, Pi setup, commissioning, tuning. Also what this build adds over a stock Ender 3 Pro, the reference build's measured values and the list of things that bite. | `docs/README.md` |
| `config/` | Klipper and Moonraker configs, macros, the Mainsail dashboard backup, and an explanation of how the fans, levelling, runout and dashboard buttons behave. | `config/README.md` |
| `tools/` | The flash script behind FLASH_MCU, the shaper plot script, the config lint. | `tools/README.md` |
| `enclosure/` | Board enclosure, feet, filler and cap: Fusion 360 scripts, STLs, renders, fit checks, 3D viewer. | `enclosure/README.md` |
| `cable_mast/` | Cable mast, reel shackle, snap pin and roller: parameters, Fusion script, STLs, viewer. | `cable_mast/README.md` |
| `.github/workflows/` | CI: config lint, Fusion mock runs, geometry fit checks, STLs and viewers current. | |

## License

GPL-3.0, see `LICENSE`. Pin mappings borrow from Klipper's
`generic-bigtreetech-skr-3.cfg` and `printer-creality-ender3-2018.cfg`
examples (also GPL-3.0). The cable mast is derived from the Kobra Max
harness mast in [Kobra-Max-Improvements](https://github.com/ryanpie86/Kobra-Max-Improvements).
