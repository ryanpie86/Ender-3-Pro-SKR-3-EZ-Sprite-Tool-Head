#!/usr/bin/env bash
# Render Klipper's latest SHAPER_CALIBRATE data to PNGs that Mainsail can download.
# For each axis with a /tmp/calibration_data_<axis>_*.csv, the newest file is plotted with
# Klipper's own calibrate_shaper.py to ~/printer_data/config/shaper_<axis>.png.
# Run from the SHAPER_PLOT button (config/shell.cfg) or by hand.
#
# Needs matplotlib for the Python that runs it: the first of klippy-env or the system python3
# that can import it is used. One-time install: sudo apt install -y python3-matplotlib
set -uo pipefail
KLIPPER=${KLIPPER:-$HOME/klipper}
OUT=${OUT:-$HOME/printer_data/config}
SCRIPT="$KLIPPER/scripts/calibrate_shaper.py"
[ -f "$SCRIPT" ] || { echo "No $SCRIPT (is Klipper at $KLIPPER?)"; exit 1; }

PY=""
for cand in "$HOME/klippy-env/bin/python" python3; do
    if "$cand" -c 'import matplotlib, numpy' >/dev/null 2>&1; then PY=$cand; break; fi
done
[ -n "$PY" ] || { echo "No Python with matplotlib found. Once: sudo apt install -y python3-matplotlib"; exit 1; }

done_any=0
for axis in x y; do
    csv=$(ls -t /tmp/calibration_data_${axis}_*.csv 2>/dev/null | head -n1 || true)
    if [ -z "$csv" ]; then echo "$axis: no calibration data in /tmp (run SHAPER_$(echo $axis | tr a-z A-Z) first)"; continue; fi
    echo "$axis: plotting $(basename "$csv")"
    if "$PY" "$SCRIPT" "$csv" -o "$OUT/shaper_${axis}.png" >/dev/null 2>&1; then
        echo "$axis: wrote shaper_${axis}.png (Mainsail -> Machine, download it)"
        done_any=1
    else
        echo "$axis: calibrate_shaper.py failed; run it by hand to see why: $PY $SCRIPT $csv -o $OUT/shaper_${axis}.png"
    fi
done
[ "$done_any" = 1 ] || exit 1
