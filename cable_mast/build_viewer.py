#!/usr/bin/env python3
"""Writes out/viewer.html: an interactive 3D view of the mast, reel and D-ring catch, STLs embedded as base64.

    python3 build_viewer.py      # after cable_mast.py
"""
import base64
import json
import os
import sys

from manifold3d import Manifold

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cable_mast as M  # noqa: E402


def b64(m):
    return base64.b64encode(M.to_trimesh(m).export(file_type="stl")).decode("ascii")


models, full, catch_v, print_v = {}, [], [], []


def add(key, m, color, kind, *views):
    models[key] = {"stl": b64(m), "color": color, "kind": kind}
    for v in views:
        v.append(key)


drop = 120.0
z0 = M.catch_installed_z(drop)
add("bar", M.bar(), "#555555", "ctx")
add("mast", M.build_mast(), "#e8e3d6", "part")
add("dring", M.build_dring_local(), "#e8e3d6", "part")
for name, m, color in M.catch_parts_local():
    add(name, m, color, "part")
add("cord", M.cyl_z(M.HANG_X, 0, z0 + M.D_HEIGHT + M.TAB_H, M.REEL_EYE_Z - 40, 1.5), "#222222", "hw")
add("reel", Manifold.cylinder(12, 19, 19, 48).rotate([-90, 0, 0]).translate([M.HANG_X, -6, M.REEL_EYE_Z - 26]), "#333333", "hw")
add("sleeve", M.sleeve_local(), "#1f1f1f", "hw")
add("mast_p", M.mast_print(), "#e8e3d6", "part")
add("dring_p", M.dring_print().translate([125, 20, 0]), "#e8e3d6", "part")
add("roller_p", M.roller_print(), "#d9822b", "part")
add("pin_p", M.pin_print(), "#c9a227", "part")
hang = [M.HANG_X, 0, z0]
full = ["bar", "mast", "cord", "reel", {"key": "dring", "at": hang}, {"key": "pin", "at": hang}, {"key": "roller", "at": hang}, {"key": "sleeve", "at": hang}]
catch_v = ["dring", "pin", "roller", "sleeve"]
print_v = ["mast_p", "dring_p", {"key": "roller_p", "at": [125, 90, 0]}, {"key": "pin_p", "at": [110, 130, 0]}]

I = min(M.COL_X * M.COL_Y ** 3, M.COL_Y * M.COL_X ** 3) / 12.0
A, L = abs(M.TIP_X), M.ARM_Z0
defl = M.TIP_LOAD_N * A ** 3 / (3 * M.E_PETG * I) + (M.TIP_LOAD_N * A * L / (M.E_PETG * I)) * A
views = [
    {"id": "full", "label": "Mast, reel, catch", "parts": full,
     "facts": [["How it works", "the reel at the mast top holds the cable sleeve up through the D-ring; Z up → apex rises ~Z/2 → reel retracts; X moves → sleeve slides over the roller"],
               ["Mast", "one print, street-light shape: one {:.0f} × {:.0f} foot on the arm's side keyed into the 2020's 6 mm slot, {:.0f} × {:.0f} column to {:.0f}, R{:.0f} inside radius into a {:.0f} mm arm along the bar (in the frame's plane); the tip is a {:.0f} mm plate flush with the bed face with a {:.0f} × {:.0f} slot across the bar, {:.0f} up; the clip moves along it".format(M.BASE_L, M.BASE_W, M.COL_X, M.COL_Y, M.ARM_TOP_Z, M.INNER_R, M.ARM_REACH, M.PAD_T, M.HOLE_D, M.HOLE_D + M.SLOT_STRAIGHT, M.EYE_CZ)],
               ["Apex travel", "~{:.0f} mm over {:.0f} mm of Z".format(M.Z_TRAVEL / 2, M.Z_TRAVEL)],
               ["Stiffness", "{:.1f} mm drop at the eye under {:.0f} N straight down (PETG)".format(defl, M.TIP_LOAD_N)],
               ["Hardware", "2 × M5 × 8 + M5 T-nuts in the top bar. Nothing else"]]},
    {"id": "catch", "label": "Shackle", "parts": catch_v,
     "facts": [["Shackle", "one band {:.0f} wide × {:.0f} deep, {:.0f} clear inside for the {:.0f} mm ribbon, {:.0f} from pin axis to arch top; legs and tab end in half-rounds (R{:.0f}) round the Ø{:.1f} pin holes and the Ø{:.0f} tab hole".format(M.HOOP_T, M.HOOP_W, M.RING_IN, M.SLEEVE_W, M.D_HEIGHT, M.LEG_DROP, M.PIN_HOLE, M.TAB_HOLE)],
               ["Snap pin", "Ø{:.0f} shank, {:.1f} long, Ø{:.0f} head; Ø{:.1f} barb on a {:.0f} mm slotted tip clicks past the far leg ({:.1f} mm squeeze per finger, ~{:.1f} % strain)".format(M.PIN_D, M.PIN_L, M.PIN_HEAD_D, M.BARB_D, M.PIN_SLOT_L, (M.BARB_D - M.PIN_HOLE) / 2, 100 * M.PIN_FINGER_STRAIN)],
               ["Roller", "Ø{:.0f} × {:.1f}, bore {:.1f}: loose on the rod".format(M.ROLLER_OD, M.ROLLER_L, M.ROLLER_BORE)],
               ["Fitting the cable", "squeeze the pin's tip and pull it out, lay the cable sleeve in the shackle, push the pin back through leg, roller and leg until it clicks"]]},
    {"id": "print", "label": "Print orientation", "parts": print_v,
     "facts": [["Mast", "flat on its back, {:.0f} mm thick; the tip plate lies on the bed, its slot vertical; no support anywhere".format(M.COL_Y)],
               ["Shackle", "flat slab, {:.0f} thick; the Ø{:.1f} pin holes print horizontally, fine at this size".format(M.HOOP_W, M.PIN_HOLE)],
               ["Snap pin", "lying on its flat with the slot vertical, so the fingers flex along the layers; PETG"],
               ["Roller", "standing on end"]]},
]
from viewer_fill import fill  # noqa: E402

html = fill(models, views, "Harness mast", "Ender 3 Pro · mast, retractable reel and roller catch for the Sprite cable sleeve, generated from cable_mast.py",
            "Interactive 3D view of the Ender 3 Pro Sprite harness slack take-up: one-piece printed mast on the 2020 top bar, retractable reel, printed D-ring catch",
            [("#e8e3d6", "printed mast / D-ring"), ("#c9a227", "printed rod"), ("#d9822b", "printed roller"), ("#333", "reel, cord, sleeve"), ("#555", "top beam")], "mast-view")
out = os.path.join(HERE, "out", "viewer.html")
with open(out, "w") as f:
    f.write(html)
print("wrote", out, os.path.getsize(out), "bytes")
