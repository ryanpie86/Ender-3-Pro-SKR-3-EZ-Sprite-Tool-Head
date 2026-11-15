#!/usr/bin/env python3
"""Geometry twin of Cap/Cap.py: STL, fit check against a rail end with its bores, render."""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "Cap"))
sys.path.insert(0, os.path.join(HERE, "Foot"))
sys.path.insert(0, HERE)
import Cap as P  # noqa: E402
import Foot as FT  # noqa: E402
from generate_stl import box, render_view, slot_void, to_trimesh  # noqa: E402


def build_cap(L):
    """Print orientation: plate on the bed, pegs up."""
    x0, y0, x1, y1 = L["plate"]
    cap = box(x0, y0, 0, x1, y1, P.PLATE_T)
    for (px, py) in L["pegs"]:
        cap += cross_z(px, py, P.PLATE_T, P.PLATE_T + P.PEG_L - P.PEG_TIP, P.PEG_SPAN, P.PEG_ARM)
        cap += cross_z(px, py, P.PLATE_T + P.PEG_L - P.PEG_TIP - 0.01, P.PLATE_T + P.PEG_L, P.PEG_SPAN - P.PEG_TIP_SHRINK, P.PEG_ARM - P.PEG_TIP_SHRINK)
    return cap


def cross_z(cx, cy, z0, z1, span, arm):
    """A + prism along Z: two bars span long and arm wide crossing at (cx, cy)."""
    return (box(cx - span / 2, cy - arm / 2, z0, cx + span / 2, cy + arm / 2, z1)
            + box(cx - arm / 2, cy - span / 2, z0, cx + arm / 2, cy + span / 2, z1))


def cross_y(y0, y1, cx, cz, span, arm):
    """The same + as a void along Y (the rail's cavity)."""
    return (box(cx - span / 2, y0, cz - arm / 2, cx + span / 2, y1, cz + arm / 2)
            + box(cx - arm / 2, y0, cz - span / 2, cx + arm / 2, y1, cz + span / 2))


def installed(cap, H):
    """Stand the cap on the rail's front end in the foot frame (rail outer face at X = 0,
    rail underside at Z = H, rail running +Y from Y = 0): print Z -> +Y (pegs into the
    rail), print Y -> Z with the skirt below the rail. The part is X-symmetric, so a
    rotation about Y after the tilt is as good as the mirror this would otherwise need."""
    m = cap.rotate([-90, 0, 0])            # (x, y, z) -> (x, z, -y): pegs along +Y, plate height along -Z
    m = m.rotate([0, 180, 0])              # (x, y, z) -> (-x, y, -z): height back to +Z, X mirrored
    return m.translate([P.RAIL_W, -P.PLATE_T, H - P.CAP_SKIRT])   # plate occupies Y = -PLATE_T..0


def rail_end(L, H, length=60.0):
    """A rail end: 4040 from Y = 0 back, with its four + shaped corner cavities and the two bottom slots."""
    r = box(0, 0, H, P.RAIL_W, length, H + P.RAIL_W)
    for (bx, by) in P.BORE_XY:
        r -= cross_y(-1, length + 1, bx, H + by, P.CAV_SPAN, P.CAV_ARM)
    for sx in P.ENC.SLOT_X:
        r -= slot_void(P.RAIL_W - sx, H, -1, length + 1)
    return r


def check(L, cap):
    rep = []
    t = to_trimesh(cap)
    bodies = len(cap.decompose())
    rep.append("cap: watertight={} bodies={} extents={} volume={:.0f} mm3".format(t.is_watertight, bodies, np.round(t.bounds[1] - t.bounds[0], 2), cap.volume()))
    assert t.is_watertight and bodies == 1
    H = FT.layout()["foot_h"]
    up = installed(cap, H)
    r = rail_end(L, H)
    v = (up ^ r).volume()
    rep.append("interference cap vs rail end (pegs must sit in the bores) {:.4f} mm3".format(v))
    assert v < 1e-6
    # every peg is inside the rail's envelope (so inside a bore), and the skirt covers the foot's front
    for (bx, by) in P.BORE_XY:
        peg = cross_y(0.0, P.PEG_L, bx, H + by, P.PEG_SPAN, P.PEG_ARM)
        assert (peg - box(0, 0, H, P.RAIL_W, 60, H + P.RAIL_W)).volume() < 1e-6
    foot = box(0, 0, H - FT.layout()["foot_h"], P.RAIL_W, FT.FOOT_L, H)
    assert (up ^ foot).volume() < 1e-6
    skirt = box(0, -P.PLATE_T, H - P.CAP_SKIRT, P.RAIL_W, 0, H)
    assert abs((up ^ skirt).volume() - skirt.volume()) < 1e-6, "skirt does not cover the foot's front face"
    return rep


def main():
    L = P.layout()
    cap = build_cap(L)
    stl_dir, ren_dir = os.path.join(HERE, "stl"), os.path.join(HERE, "renders")
    os.makedirs(stl_dir, exist_ok=True)
    os.makedirs(ren_dir, exist_ok=True)
    for line in check(L, cap):
        print(line)
    to_trimesh(cap).export(os.path.join(stl_dir, "cap.stl"))
    print("wrote", os.path.join(stl_dir, "cap.stl"), "(print orientation: plate down, pegs up)")
    if "--no-render" not in sys.argv:
        H = FT.layout()["foot_h"]
        print("rendered", render_view("cap.png", [(to_trimesh(installed(cap, H)), "#4a90d9", 1), (to_trimesh(rail_end(L, H)), "#777777", 0.45)], 25, -125,
                                      "End cap on the foot rail's front end: pegs in the four bores, skirt hanging over the foot", ren_dir))
    print()
    print(P.summary(L))


if __name__ == "__main__":
    main()
