#!/usr/bin/env python3
"""Writes viewer.html: a self-contained interactive 3D viewer of the printed parts.

Embeds the STLs from stl/ as base64 and the layout numbers from the Fusion
scripts, so the page needs nothing but three.js from a CDN.

    python3 build_viewer.py      # after generate_stl.py / generate_foot_stl.py
"""
import base64
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "SKR3EZ_Enclosure"))
sys.path.insert(0, os.path.join(HERE, "Foot"))
sys.path.insert(0, HERE)
import SKR3EZ_Enclosure as E  # noqa: E402
import Foot as FT  # noqa: E402
import generate_stl as G  # noqa: E402
import generate_foot_stl as GF  # noqa: E402
import generate_cap_stl as GC  # noqa: E402
import generate_filler_stl as GK  # noqa: E402
sys.path.insert(0, os.path.join(HERE, "Cap"))
sys.path.insert(0, os.path.join(HERE, "KeyFiller"))
import Cap as CP  # noqa: E402
import KeyFiller as KF  # noqa: E402

L = E.layout()
LF = FT.layout()


def b64(name):
    with open(os.path.join(HERE, "stl", name), "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def b64_manifold(m):
    """Context geometry (rails with their true V-slot profile) straight from the twin, not from stl/."""
    return base64.b64encode(G.to_trimesh(m).export(file_type="stl")).decode("ascii")


def bx(x0, y0, z0, x1, y1, z1, kind):
    return {"min": [x0, y0, z0], "max": [x1, y1, z1], "kind": kind}


th = L["total_h"]
ry0, ry1 = L["rail_y"]
frame = G.frame_parts(L)
enc_frame = [{"model": "foot_rail", "kind": "rail"}, {"model": "y_rail", "kind": "yrail"}]
for (fy0, fy1) in L["feet_y"]:
    enc_frame.append(bx(-E.RAIL_W, fy0, th - L["foot_h"], 0, fy1, th, "foot"))
cy0, cy1 = L["cross_y"]
enc_frame.append(bx(0, cy0, th, 250, cy1, th + 40, "yrail"))
bzp = L["board_z0"]
px0, py0, px1, py1 = L["pcb_rect"]
enc_board = bx(px0, py0, bzp, px1, py1, bzp + E.BOARD_T, "pcb")
dx0, dy0, dx1, dy1 = L["driver_rect"]
enc_drivers = bx(dx0, dy0, L["board_top"], dx1, dy1, L["driver_top"], "drivers")
fan = bx(*L["fan_block"], "fan")
H = LF["foot_h"]
foot_rail = [{"model": "foot_rail_end", "kind": "rail"}]
foot_up = GF.installed(LF, GF.build_foot(LF))
# the front-end stack on the left rail: cap, foot, filler, then the hanger bar's front end
LC, LK = CP.layout(), KF.layout()
cap_up = GC.installed(GC.build_cap(LC), H)
gap = E.FOOT_GAP
filler_up = GK.build_filler(LK).translate([0, FT.FOOT_L + (gap - LK["length"]) / 2.0, H - KF.BASE_T])
bar_y0 = FT.FOOT_L + gap
bar_stub = G.box(0, bar_y0, H - E.BAR_T, FT.FOOT_W, 60, H)
for kx in LF["key_x"]:
    bar_stub += G.key_prism(kx, H, bar_y0, 60)
stack_ctx = [{"model": "rail_end_bores", "kind": "rail"}, {"model": "bar_stub", "kind": "yrail"}]

models = {
    "base": {"label": "Enclosure base (installed frame)", "stl": b64_manifold(G.build_base(L)), "color": "#3f7fc4"},
    "base_print": {"label": "Enclosure base (as printed)", "stl": b64("skr3ez_enclosure_base.stl"), "color": "#3f7fc4"},
    "lid": {"label": "Enclosure lid (as printed)", "stl": b64("skr3ez_enclosure_lid.stl"), "color": "#d9772f"},
    "foot": {"label": "Foot (as printed)", "stl": b64("foot.stl"), "color": "#3f7fc4"},
    "foot_installed": {"label": "Foot under the rail", "stl": b64_manifold(foot_up), "color": "#3f7fc4"},
    "foot_rail": {"label": "Left foot rail (V-slot profile from Creality's STEP)", "stl": b64_manifold(frame["foot_rail"]), "color": "#7d8792"},
    "y_rail": {"label": "Y rail, bottom slots", "stl": b64_manifold(frame["y_rail"]), "color": "#9aa4ae"},
    "foot_rail_end": {"label": "Foot rail end", "stl": b64_manifold(GF.rail(LF)), "color": "#7d8792"},
    "rail_end_bores": {"label": "Foot rail front end with bores", "stl": b64_manifold(GC.rail_end(LC, H)), "color": "#7d8792"},
    "cap": {"label": "End cap (as printed)", "stl": b64("cap.stl"), "color": "#3f7fc4"},
    "cap_installed": {"label": "End cap on the rail", "stl": b64_manifold(cap_up), "color": "#c0504d"},
    "filler": {"label": "Key filler (as printed)", "stl": b64("key_filler.stl"), "color": "#3f7fc4"},
    "filler_installed": {"label": "Key filler on the rail", "stl": b64_manifold(filler_up), "color": "#2e8b57"},
    "bar_stub": {"label": "Hanger bar front end", "stl": b64_manifold(bar_stub), "color": "#9aa4ae"},
}
views = [
    {"id": "hung", "label": "Hanging under the rail", "parts": [["base", None], ["lid", "installed"]], "context": enc_frame, "refs": [enc_board, enc_drivers, fan]},
    {"id": "open", "label": "Base with board", "parts": [["base", None]], "context": [], "refs": [enc_board, enc_drivers, fan]},
    {"id": "lid", "label": "Lid, print orientation", "parts": [["lid", None]], "context": [], "refs": []},
    {"id": "baseprint", "label": "Base, print orientation", "parts": [["base_print", None]], "context": [], "refs": []},
    {"id": "foot", "label": "TPU foot under a rail end", "parts": [["foot_installed", None]], "context": foot_rail, "refs": []},
    {"id": "footprint", "label": "Foot, print orientation", "parts": [["foot", None]], "context": [], "refs": []},
    {"id": "stack", "label": "Rail front end: cap, foot, filler", "parts": [["cap_installed", None], ["foot_installed", None], ["filler_installed", None]], "context": stack_ctx, "refs": []},
    {"id": "cap", "label": "End cap, print orientation", "parts": [["cap", None]], "context": [], "refs": []},
]
facts = {
    "hung": [("Outside", "{:.1f} × {:.1f} × {:.1f} mm + {:.1f} lid, hanger bar {:.0f} wide".format(L["outer_x"], L["outer_y"], L["wall_top"], E.LID_T, E.RAIL_W)),
             ("Below the frame", "{:.0f} mm (whole box); feet {:.0f} mm tall leave {:.0f} mm to the table".format(L["box_drop"], L["foot_h"], E.GROUND_CLEARANCE)),
             ("Mount", "left: two slot keys slid into the foot rail's bottom slots; right: a bracket strip with the same key along its full length up into the Y rail's slot. No bolts anywhere"),
             ("Position on the rail", "protrudes {:.0f} mm in front of the frame, ends {:.0f} mm before the cross brace; the hanger bar is recessed {:.0f} mm so the front foot slides on after the box; mounts are flush with the rail ends".format(-E.BOX_Y_ON_RAIL, L["cross_y"][0] - L["outer_y"], E.FOOT_L + E.FOOT_GAP)),
             ("Driver top to lid", "{:.1f} mm (EZ2209 measured 24 mm)".format(L["driver_lid_gap"]))],
    "open": [("Board orientation", "USB / SD edge to the right (screen side), terminals front, drivers along the rail"),
             ("Channels", "{:.0f} mm left (motor cables), {:.0f} mm front (power leads), {:.0f} mm right".format(E.CLR_LEFT, E.CLR_FRONT, E.CLR_RIGHT)),
             ("Cable entry", "rear notch {:.0f} mm up to the top, {:.0f} mm wide".format(E.REAR_NOTCH_Z, L["outer_x"] - 2 * E.REAR_NOTCH_MARGIN)),
             ("Fan", "40 mm in the front wall, blowing in; Ø{:.0f} opening".format(E.FAN_HOLE_D)),
             ("Standoffs", "Ø{:.0f}, {:.0f} tall, pattern {:.2f} × {:.2f}".format(E.STANDOFF_D, E.STANDOFF_H, E.HOLE_DX, E.HOLE_DY_RIGHT))],
    "baseprint": [("Orientation", "{} wall on the bed (PRINT_ORIENTATION): the hanger bar, its keys and the bracket strip all stand on the bed".format(E.PRINT_ORIENTATION)),
                  ("Support", "one small support under the hanger bar's front end (it starts 77 mm up, behind the foot's recess); the rear wall as the top face is still open"),
                  ("STL", "stl/skr3ez_enclosure_base.stl is written in this orientation; the Fusion script rotates the body as its last feature")],
    "lid": [("Plate / lip", "{:.1f} / {:.1f} mm, solid (nothing falls in)".format(E.LID_T, E.LID_LIP_H)),
            ("Screws", "4 × M3, Ø{:.1f} counterbore".format(E.LID_CBORE_D))],
    "foot": [("Size", "{:.0f} × {:.0f} × {:.0f} mm block, print 4 in TPU".format(FT.FOOT_W, FT.FOOT_L, H)),
             ("Fixing", "two full-length V-slot keys slide into the rail's bottom slots from the rail end; no bolts"),
             ("Key", "neck {:.1f} through the 6.0 throat, {:.1f} wide head behind the lips, {:.1f} tall; {:.1f} mm clearance, no flare into the V".format(E.SLOT_THROAT_W - 2 * FT.KEY_CLR, FT.KEY_W, FT.KEY_H, FT.KEY_CLR))],
    "stack": [("What it shows", "the left rail's front end: red cap on the end face with pegs in the bores and a skirt over the foot, blue foot, green key filler behind it, then the hanger bar's front end (grey)"),
              ("Lock", "cap stops the foot sliding forward; filler fills the gap to the hanger bar; the bar cannot pass the foot. Nothing on the rail moves"),
              ("Filler length", "{:.1f} mm = FOOT_GAP {:.1f} less {:.1f} fit; set FILLER_L in KeyFiller.py to the measured gap".format(LK["length"], E.FOOT_GAP, KF.KEY_FIT))],
    "cap": [("Size", "{:.0f} × {:.0f} plate, {:.0f} thick; {:.0f} mm skirt below the rail".format(CP.RAIL_W, CP.CAP_SKIRT + CP.RAIL_W, CP.PLATE_T, CP.CAP_SKIRT)),
            ("Pegs", "four + shaped, {:.1f} mm across with {:.1f} mm arms, {:.0f} long, into the rail's corner cavities at 10 and 30 mm from each edge".format(CP.PEG_SPAN, CP.PEG_ARM, CP.PEG_L)),
            ("Print", "flat on the plate, pegs up; PETG")],
    "footprint": [("Orientation", "on its end face, keys vertical: every layer is the same section, no overhangs, no support"),
                  ("Print", "TPU 95A, 100 % infill, slow; {:.0f} mm tall".format(FT.FOOT_L)),
                  ("STL", "stl/foot.stl is already in this orientation")],
}
views.append({"id": "section", "label": "Cross-section", "parts": [], "context": [], "refs": [], "image": True})
facts["section"] = [("What it shows", "a true cut across the box: keys in the foot rail's bottom V-slots (slot profile traced from Creality's STEP), hanger bar flush with the frame plane, bracket strip and key in the Y rail's slot"),
                    ("Cut position", "Y = {:.0f} mm from the box front".format((L["columns"][0][0] + L["columns"][0][1]) / 2.0)),
                    ("Live clip", "in any 3D view, drag the Clip slider to cut the parts at any Y and orbit the cut face")]
with open(os.path.join(HERE, "renders", "section_mount.png"), "rb") as f:
    section_png = base64.b64encode(f.read()).decode("ascii")
payload = {"models": models, "views": views, "facts": {k: [list(x) for x in v] for k, v in facts.items()}, "lid_total_h": L["total_h"],
           "section_png": section_png, "clip_range": [-80.0, L["outer_y"] + 80.0]}

html = open(os.path.join(HERE, "viewer_template.html")).read().replace("__DATA__", json.dumps(payload))
out = os.path.join(HERE, "viewer.html")
with open(out, "w") as f:
    f.write(html)
print("wrote", out, os.path.getsize(out), "bytes")
