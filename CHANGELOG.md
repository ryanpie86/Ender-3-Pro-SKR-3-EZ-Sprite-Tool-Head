# Changelog

## 1.0.0

First public release: a complete, working Klipper build for a Creality Ender 3 Pro on a BIGTREETECH SKR 3 EZ with a Sprite Pro direct-drive toolhead, CR Touch, dual Z with automatic gantry levelling, a filament runout sensor and MainsailOS on a Raspberry Pi 4.

- Firmware route: Katapult once over DFU, then Klipper updates from the Pi over USB with the FLASH_MCU dashboard button; SD-card method documented as the alternative.
- Wiring guide with a jumper table, a pictorial cable-by-cable page, a CR Touch re-pin page and a printable board diagram.
- Klipper and Moonraker configs, Mainsail dashboard backup (macro groups, temperature presets), KAMP adaptive meshing and purge.
- Dual-Z gantry levelling before every print, deferred runout that uses the filament left in the tube, nozzle and pressure-advance buttons remembered across restarts, an enclosure fan that follows motor and heater activity and the MCU temperature.
- Input shaper, speed and acceleration test procedure with the reference build's results.
- Printed hardware as Fusion 360 scripts with ready STLs, fit checks and 3D viewers: a board enclosure that hangs under the left foot rail without bolts, TPU feet, a slot filler and an end cap, and a cable mast with a retractable reel and a printed roller shackle for the Sprite's flat cable.
