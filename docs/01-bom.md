# 01 · Bill of materials

Prices are deliberately left out; they move too fast. Quantities assume the
stock Ender 3 Pro harness is reused wherever it fits (it mostly does: the SKR
3 EZ uses the same XH2.54 connector family as the Creality board).

## Electronics

| Qty | Item | Notes |
|---|---|---|
| 1 | BIGTREETECH **SKR 3 EZ** | Advertised with an STM32H743VI; many, this one included, ship with an STM32H723VG. Read the chip marking before building firmware. |
| 5 | BIGTREETECH **EZ2209** driver | X, Y, Z-left, Z-right, E. UART, no jumpers to set. Buy a kit of 5 or 4 + 1. |
| 1 | Raspberry Pi 4 (2 GB is plenty) | Host for Klipper / Moonraker / Mainsail. |
| 1 | microSD card ≥ 16 GB, A1/A2 class | For MainsailOS on the Pi. |
| 0–1 | microSD card ≤ 32 GB, FAT32 | Only if you keep BTT's bootloader (`docs/03` §7); with Katapult the board is flashed from the Pi over USB. |
| 1 | 5 V ≥ 3 A supply for the Pi | Official USB-C supply, **or** a 24 V → 5 V buck converter (≥ 5 A rated) fed from the printer PSU. Don't try to run the Pi from the board's USB port. |
| 1 | USB A-to-B cable, ≤ 1 m, with ferrite if possible | Pi → board. The SKR 3 EZ has a USB Type-B (printer-style) port. |
| 1 | Printed Raspberry Pi 4 enclosure that mounts under the stock screen | [Thingiverse thing 4586351](https://www.thingiverse.com/thing:4586351). Keeps the Pi, its supply lead and the USB cable at the screen end of the frame. |
| 1 | Creality Sprite Pro direct-drive extruder kit for the Ender 3 (300 °C all-metal) with CR Touch on its bracket | Replaces the Bowden hotend and extruder. The CR Touch is what `Z_TILT_ADJUST` and the bed mesh probe with; its 5-pin lead splits into the 2-pin + 3-pin board end (`docs/cr-touch-repin.md`). |
| 1 | Dual-Z upgrade kit for the Ender 3: second NEMA17 motor, T8×8 lead screw, coupler, top and bottom brackets, cable | The right-hand screw. Check the motor cable's coil pairing before plugging it in (`docs/02`). |
| 1 | Filament runout sensor (Creality's or any three-wire module) with a mount for the top of the frame | Plugs into E0DET. Its lead may need a 3-pin JST-XH end if it has Creality's own connector. |
| 1 | 4-pin XH2.54 stepper extension, ~1 m | The right-hand Z motor needs to reach the board on its own cable (no Y-splitter: the two Z motors must be on separate drivers). |
| 1 | 40 × 40 × 10 mm 24 V fan | Enclosure fan, in the box's front wall. The stock mainboard case fan can be reused. |
| optional | 2 × 40 mm 24 V fans | Driver fans on the MFAN headers if you push motor currents hard. Not needed at stock currents. |

## Enclosure and feet hardware

| Qty | Item | Notes |
|---|---|---|
| 4 | M3 × 6 mm screws (6–8 fit) | Board to standoffs: self-tapping into Ø2.5 holes that run 7.5 mm through standoff and floor; 6 mm gives 4.4 mm of thread under the 1.6 mm PCB, 8 mm gives 6.4 and still does not poke out. Any head. |
| 4 | M3 × 8 mm pan-head screws (8–12 fit) | Lid to corner posts: 4 mm of lid stack (1 mm under the Ø6.2 × 1.5 counterbore + 3 mm boss), then a Ø2.5 × 10 mm self-tap hole in the post; 8 mm engages 4 mm and holds (as fitted), 12 mm bottoms out. Pan head (≤ Ø6, 2.4 tall) stands 0.9 mm proud, under the 2.5 mm lid-to-rail gap; button heads also fit, socket caps are 1.5 mm proud and tight. |
| 4 | M3 × 16 mm screws + M3 nuts (16–20 fit) | 40 mm fan into the front wall from inside: 2.5 mm wall + 10 mm fan + nut. The fan's own self-tapping screws (Ø3.4 wall holes) work without nuts if yours came with them. |
| 0 | rail / frame bolts | None: the box, feet, filler and cap all key or press into the rails. |
| 2 | M5 × 8 screws + M5 T-nuts (drop-in or sliding) | Cable mast foot into the 2020 top bar's slot (`cable_mast/`). |
| 1 | Retractable badge reel with a carabiner, plus 1–2 one-inch split rings | Hangs from the cable mast's tip and holds the Sprite cable sleeve up through the printed shackle. |
| 1 pair + ~1 m | XT60 male/female, 16 AWG silicone wire (red/black) | Bed heater lead extension to reach the enclosure (`docs/02`, Heaters). |
| ~250 g | TPU 95A filament | Four feet, 100 % infill. |

## Tuning (one-off, borrowable)

| Qty | Item | Notes |
|---|---|---|
| 1 | ADXL345 breakout + Raspberry Pi Pico + a micro-USB lead to the Pi | For `SHAPER_CALIBRATE` (`docs/06-tuning.md`, wiring table there). The Pico is a second Klipper MCU; nothing is wired to the SKR 3 EZ. Borrowable: it is only needed while tuning. |

## Tools and consumables

- Ferrule crimper + 16–18 AWG ferrules for the heater, bed, and DC-in screw
  terminals. The stock Creality wires are tinned; re-terminate with ferrules.
- XH2.54 crimper and a few 2/3/4-pin housings for cables that need re-pinning
  (endstop cables if yours are 2-pin, the Z-right extension if you make your
  own).
- Multimeter. Check 24 V polarity at DCIN before the board goes live.
- Zip ties, cable sleeve.

## What you do NOT need

- No display adapter: the stock Creality display and its beeper plug straight
  into EXP1 on the stock ribbon; Klipper maps the pins (`docs/02-wiring.md`).
- No step-down module for the fans: the stock fans are 24 V and the SKR 3
  EZ's V-FAN jumper selects DC-in (24 V) for FAN0/1/2.
