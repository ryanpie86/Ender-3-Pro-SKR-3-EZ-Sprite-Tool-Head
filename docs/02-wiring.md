# 02 · Wiring: Ender 3 Pro harness → SKR 3 EZ

Source for pin names: BIGTREETECH's `SKR 3 EZ V1.0-PIN.pdf` and the Klipper
project's `generic-bigtreetech-skr-3.cfg`. Everything below matches
`config/printer.cfg`.

Orientation used throughout: the board as printed on the silkscreen, with
the five driver sockets along the **top** edge, screw terminals down the
**left** edge, USB / SD / thermistors along the **bottom** edge, EXP1 / EXP2
on the **right** edge.

## Before plugging anything in: jumpers and switches

Source: BTT's *SKR 3 EZ user manual* §3.1–3.13 (jumper photos) and the
V1.0 pin diagram. Board held as on the silkscreen (drivers along the top).
Every jumper the board has is listed; nothing else on it is a jumper.

| # | What | Where | This build |
|---|---|---|---|
| 1 | **USB / CAN switch** | Push switch just left of the USB-B socket, labelled USB / CAN | **Popped up = USB.** Pressed in is CAN FD and the Pi will never see the board. |
| 2 | **VUSB** (2-pin) | Under the VIN 2×4 header, left of the micro-SD slot | **Open.** Closed feeds the Pi's 5 V into the board; only for bench flashing without the PSU (`docs/03`), and open it again before the board goes in. |
| 3 | **Motor voltage, one 3-pin header per driver** (×5) | Diagonal header between each driver socket and its tall electrolytic capacitor | **Cap on the upper pair, nearest the motor connector**, on all five = drivers fed from DCIN (manual §3.2.1). The lower pair feeds them from the separate 12–48 V *Motor Power* terminal (§3.2.2), which stays empty here. A driver on the wrong pair has no motor voltage: that motor simply will not buzz in `docs/05`. |
| 4 | **DIAG jumpers** (2-pin, ×5) | Small 2-pin header at the upper-left corner of each driver socket | **All off.** Only for sensorless homing (§3.3.3); this build keeps the mechanical endstops. |
| 5 | **V-FAN** (3-pin, VIN \| VOT) | Next to HE1, top-left of the MCU | **Cap on the VIN pair** so FAN0/FAN1/FAN2 output DCIN = 24 V for the stock fans (§3.5). The two 2×4 headers **VOT** and **VIN** beside it are for the SKR 3 DC-MODE module: leave them empty. |
| 6 | **HE0 and HE1 output jumpers** (2-pin each, silkscreen PB3 / PB4) | Beside the HE0 and HE1 MOSFETs, left of the V-FAN header | **Both fitted** (they ship fitted). They connect the heater pins to the MOSFETs; pulled only for driving a laser from the IO (§3.13). HE0 missing = hotend never heats. |
| 7 | **PT1000 jumpers** (2-pin, TH0 and TH1) | Bottom right, silkscreen "PT1000" between the PS-ON and TH0/TH1 headers | **Both open** = 4.7 kΩ pull-up for the stock 100 K NTC thermistors (§3.6). Closed is 2.2 kΩ for PT1000. TB has no jumper. |
| 8 | **EZ2209 drivers** (×5) | The red EZ sockets at X, Y, Z, E0, E1 | Keyed, one way only. **No UART / SPI mode jumpers exist on the EZ board** (§3.3.2); the drivers set their own mode. |

Also on the board, not jumpers: the **BOOT** button (left of the MCU) and
**RESET** button (below it) used once for the Katapult DFU flash in
`docs/03`; the **SWD**, **WIFI**, **MOT-SPI**, **TFT**, **CAN FD**, **RGB**,
**PS-ON** and **PWR-DET** headers all stay empty; the blade fuse next to
DCIN should be seated. Connectors used by this build: XM, YM, ZAM, E0M,
E1M, FAN0/1/2, HE0, BED, DCIN, X-STOP, Y-STOP, Z-STOP (unused with the
probe), SERVOS + Probe (CR Touch), E0DET (runout sensor), EXP1 (+ EXP2
plug) for the stock LCD, TB, TH0, USB.

## Power

| Wire | SKR 3 EZ terminal | Notes |
|---|---|---|
| PSU 24 V + | **DCIN +** (lower screw) | Ferrule. Check polarity with a meter first. On the Mini E3 the + was the upper screw; here − is upper and + is lower, as the silkscreen `−DCIN+` says. |
| PSU 24 V − | **DCIN −** (upper screw) | |
| (nothing) | Motor power 12–48 V | Leave empty. |

**Pictorial, cable by cable:** `docs/mini-e3-to-skr3ez-cables.html` (or the
`.pdf`) draws each Mini E3 header next to the SKR 3 EZ header it moves to,
pins dotted and joined, with the verdict per cable. The CR Touch has
`docs/cr-touch-repin.html`. Everything below is the same information as text.

## Steppers (4-pin XH2.54, plug straight in)

| Motor | SKR socket | Klipper section | step / dir / enable | UART |
|---|---|---|---|---|
| X | **XM** | `[stepper_x]` | PD4 / PD3 / PD6 | PD5 |
| Y | **YM** | `[stepper_y]` | PA15 / PA8 / PD1 | PD0 |
| Z left (stock) | **ZAM** | `[stepper_z]` | PE2 / PE3 / PE0 | PE1 |
| Z right | **E1M** | `[stepper_z1]` | PD11 / PD10 / PD13 | PD12 |
| Extruder (Sprite, on the toolhead) | **E0M** | `[extruder]` | PD15 / PD14 / PC7 | PC6 |

**Do not use ZBM.** ZAM and ZBM are wired in parallel on the Z driver. For
independent tilt adjustment the second Z motor must be on its own driver,
which is the E1 socket here.

Coil order: both boards' schematics give the 4-pin header as 2B 2A 1A 1B
(coil B on pins 1-2, coil A on 3-4), so the Creality cables that ran on the
Mini E3 plug straight in. BTT's Mini E3 pin drawing prints 2B 1B 1A 2A; the
schematic is the one to trust.

Motor direction: the `dir_pin` polarities in the config were set by running
each axis on the reference build (X, Y, Z-right and the extruder are
inverted). Kit motors differ: if an axis moves backwards during
`docs/05-first-power-on.md`, flip the `!` on that axis's `dir_pin`. Do this
in the config, not by re-pinning the plug.

## Endstops (3-pin headers: +5 V · GND · Signal)

| Switch | SKR header | Pin | Config |
|---|---|---|---|
| X endstop | **X-STOP**, lower two pins (GND + PC1) | PC1 | `endstop_pin: ^PC1` |
| Y endstop | **Y-STOP**, lower two pins (GND + PC3) | PC3 | `endstop_pin: ^PC3` |
| Z endstop | (not used, probe is the Z endstop) | PC0 | can stay plugged in, ignored |

The stock Creality switches are 2-wire, and on the Mini E3 they sat in 2-pin
headers. On the SKR 3 EZ the same 2-pin housing goes onto the **GND + Signal**
pair of the 3-pin header, the two pins away from +5V (pin 1, at the top). If your cable has a 2-pin housing, re-pin it into a 3-pin
housing (or use the endstop leads BTT packs with the board). Never put a
switch across +5 V and Signal.

## CR Touch (on the Sprite)

| Probe wire | SKR header | Pin |
|---|---|---|
| Brown (GND), Red (+5 V), Yellow/orange (control) | **SERVOS** (3-pin: GND · +5V · PE5) | control = **PE5** |
| Black (GND), White (signal) | **Probe** (2-pin: GND · PC13) | sensor = **PC13** |

Config: `[bltouch] sensor_pin: ^PC13`, `control_pin: PE5`. Klipper drives a
CR Touch exactly like a BLTouch. The Sprite's cable comes off the Mini E3
as one 5-pin plug with all-black wires; `docs/cr-touch-repin.md` is the
pin-by-pin map for splitting it into the 3-pin and 2-pin housings. The offsets in the config (−32, −41)
are the Sprite bracket's; measure yours after the first home.

## Heaters and thermistors

| Item | SKR terminal / header | Pin | Notes |
|---|---|---|---|
| Hotend heater | **HE0** screw terminal | PB3 | Ferrules. Polarity doesn't matter. |
| Bed heater | **HB** screw terminal | PD7 | Ferrules. 24 V bed, ~12 A peak at cold start. The stock bed leads were too short for the enclosure under the left rail and were extended with an XT60 pair in 16 AWG; the PSU leads, thermistors, endstops and motor cables reached without changes. XT60 convention: flat side +, chamfered side −, and the + / − moulded on the housing rule. Polarity only matters for the bed's indicator LED; the heater itself does not care. |
| Hotend thermistor | **TH0** (2-pin) | PA2 | 100 K NTC (EPCOS B57560G104F) |
| Bed thermistor | **TB** (2-pin) | PA1 | 100 K NTC |
| (spare) | TH1 | PA3 | second hotend thermistor |

## Fans (2-pin XH2.54, 24 V via V-FAN = VIN)

| Fan | Sprite harness label | SKR header | Pin | Klipper section |
|---|---|---|---|---|
| Part cooling (blower on the hotend shroud) | **XFan** | **FAN0** | PB7 | `[fan]` |
| Hotend heatsink fan (was always-on 24 V on the Creality board) | **Fan** | **FAN1** | PB6 | `[heater_fan hotend_fan]` runs when hotend > 50 °C |
| Enclosure fan, front wall of the box (the stock mainboard case fan) | – | **FAN2** | PB5 | `[fan_generic enclosure_fan]`, driven by a 10 s loop in macros.cfg: on while steppers/heaters are active (+60 s), and whenever the MCU is 45 °C or more |
| Driver fans (optional) | – | **MFAN** ×3 | – | always-on at motor voltage, no config |

The Sprite Pro's two fan leads are labelled the wrong way round for what you
would guess: **XFan is the part-cooling blower** and **Fan is the heatsink
fan** (confirmed on the reference build: plugged the other way, the blower ran whenever
the hotend was warm and the heatsink fan followed the slicer's fan speed).

Mind polarity on fans: red to **V**, black to **GND** as marked next to the
header.

## Filament runout sensor

The printer's runout switch goes on **E0DET** (3-pin: +5 V · GND · signal =
PC2), the top header of the second column in the endstop block. It came off
the Mini E3's E0-STOP, whose schematic numbers the pins the same way
(1 = +5 V, 2 = GND, 3 = signal), so the keyed plug goes straight in; BTT's
two pin tables only read the other way round because the header is turned
around on the board. The sensor is a three-wire module with its own
driver, so `printer.cfg` configures the pin without a pull-up (`PC2`); a
plain two-wire microswitch would need `^PC2`. Check the polarity on first
power-on with `QUERY_FILAMENT_SENSOR SENSOR=runout` (docs/05, step 3b): if
it reads the wrong way round, invert the pin with `!`. What happens on
runout is described next.

With the sensor at the top of the frame there is a tube's worth of filament
between it and the extruder. The config uses it: on runout the print
continues until `tail_mm` (in `_RUNOUT`, macros.cfg) has been extruded,
then M600 pauses, parks and retracts with the tail still in the drive gear.
Measure once: filament path from the sensor switch to the Sprite's gear,
along the tube, minus 30 mm, into `variable_tail_mm`.

## USB to the Pi

Board USB-B → Pi USB-A. Keep it short, away from the heater and motor wires.
If you have trouble with disconnects, this cable and the Pi's power supply
are the first two suspects.

## Stock Creality 12864 display and its beeper

Plug the display's 10-pin ribbon straight into **EXP1**, pin 1 to pin 1, no
re-pinning. The ribbon is wired in Creality's order rather than the RepRap
order the SKR 3 EZ's header follows, but that only matters to Marlin:
Klipper just needs to know which GPIO each signal lands on, and the
`[display]` block in `printer.cfg` maps them by ribbon position, taken from
the SKR Mini E3 config the reference build ran before (its EXP1 is in Creality's
order). The buzzer is on the display board, driven from ribbon pin 1 =
`PC5`, set up as `[output_pin _beeper]` (the underscore keeps Mainsail from
showing it as a slider); `BEEP` and `M300` macros drive it.
Pins 9 and 10 are GND and 5 V on both headers, so nothing is at risk if
the mapping is off: a wrong guess just shows a blank screen. Verify on
first power-on (docs/05, step 0): status screen, knob, click, `BEEP`.

## Cable routing into the enclosure

The enclosure (see `enclosure/`) hangs under the left foot rail with the
board turned so its USB / SD edge faces the printer's right (the screen).
Every cable enters over the notch in the rear wall and runs forward along a
20 mm channel on either side of the board.

| Opening | Carries |
|---|---|
| Rear wall notch | Everything in: XM / YM / ZAM / E0M / E1M motor cables, endstops, CR Touch, hotend heater, bed heater, PSU leads, thermistors |
| Left channel (rail side) | Motor and endstop cables down to the sockets along the board's driver edge |
| Right channel (screen side) | Hotend / bed / DC-in leads forward to the screw terminals at the front; thermistor leads to TB / TH0 |
| Right wall openings | USB-B to the Pi, micro-SD. Nothing else exits here |
| Front wall | 40 mm fan, blowing in; no cables |
| Lid | Solid |

**Where the Pi lives.** The Pi sits under the stock screen in a printed enclosure, [Thingiverse thing 4586351](https://www.thingiverse.com/thing:4586351), and is powered by its own 5 V USB-C supply or a 24 V to 5 V buck converter off the printer PSU (BOM); it reaches the board through one USB A-to-B cable.
