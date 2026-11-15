# Tools

Scripts that run on the Pi. Both shell scripts assume this repository is
cloned at `~/Ender-3-Pro-SKR-3-EZ-Sprite-Tool-Head`; nothing else in the
repo depends on the path.

| Script | Does | Run from |
|---|---|---|
| `flash_skr3.sh` | Rebuilds Klipper from `~/klipper/config.skr3`, stops the Klipper service, flashes the SKR 3 EZ over USB through Katapult, flashes the ADXL Pico the same way when it is plugged in and `config.pico` exists, restarts Klipper. Refuses an image that is not an STM32H7 build. `--no-build` flashes the existing binary. | The FLASH_MCU dashboard button, or SSH (`docs/03-firmware-flash.md` §5) |
| `shaper_plot.sh` | Renders the newest `SHAPER_CALIBRATE` data for each axis to `shaper_x.png` and `shaper_y.png` in the config folder, downloadable from Mainsail's Machine tab. Needs matplotlib: `sudo apt install -y python3-matplotlib` once. | The SHAPER_PLOT dashboard button, or SSH (`docs/06-tuning.md`) |
| `check_klipper_cfg.py` | Static lint for the Klipper config files: section syntax, pin names, duplicate sections. | CI, or `python3 tools/check_klipper_cfg.py config/*.cfg` |

FLASH_MCU stops and starts the Klipper service, so it runs through
`sudo systemd-run` and needs the one-line sudoers entry in
`docs/03-firmware-flash.md` §5b.
