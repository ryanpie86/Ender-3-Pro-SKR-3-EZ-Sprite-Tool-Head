#!/usr/bin/env python3
"""Geometry twin of KeyFiller/KeyFiller.py: STL, fit check in the rail's slots, render."""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "KeyFiller"))
sys.path.insert(0, HERE)
import KeyFiller as P  # noqa: E402
from generate_stl import box, key_prism, render_view, slot_void, to_trimesh  # noqa: E402


def build_filler(L):
    """As modelled: base on the bed, keys up (the rail's underside is at Z = BASE_T)."""
    n = L["length"]
    f = box(0, 0, 0, P.RAIL_W, n, P.BASE_T)
    for kx in L["key_x"]:
        f += key_prism(kx, L["key_z0"], 0.0, n)
    return f


def rail(L):
    n = L["length"]
    r = box(0, -10, P.BASE_T, P.RAIL_W, n + 10, P.BASE_T + P.RAIL_W)
    for kx in L["key_x"]:
        r -= slot_void(kx, P.BASE_T, -11, n + 11)
    return r


def check(L, f):
    rep = []
    t = to_trimesh(f)
    bodies = len(f.decompose())
    rep.append("filler: watertight={} bodies={} extents={} volume={:.0f} mm3".format(t.is_watertight, bodies, np.round(t.bounds[1] - t.bounds[0], 2), f.volume()))
    assert t.is_watertight and bodies == 1
    v = (f ^ rail(L)).volume()
    rep.append("interference filler vs rail {:.4f} mm3".format(v))
    assert v < 1e-6
    for kx in L["key_x"]:
        key = key_prism(kx, L["key_z0"], 0.0, L["length"])
        assert (key - slot_void(kx, P.BASE_T, -1, L["length"] + 1)).volume() < 1e-6
    return rep


def main():
    L = P.layout()
    f = build_filler(L)
    stl_dir, ren_dir = os.path.join(HERE, "stl"), os.path.join(HERE, "renders")
    os.makedirs(stl_dir, exist_ok=True)
    os.makedirs(ren_dir, exist_ok=True)
    for line in check(L, f):
        print(line)
    to_trimesh(f).export(os.path.join(stl_dir, "key_filler.stl"))
    print("wrote", os.path.join(stl_dir, "key_filler.stl"))
    if "--no-render" not in sys.argv:
        print("rendered", render_view("key_filler.png", [(to_trimesh(f), "#4a90d9", 1), (to_trimesh(rail(L)), "#777777", 0.45)], 25, -55,
                                      "Key filler in the rail's bottom slots (set FILLER_L to the measured gap)", ren_dir))
    print()
    print(P.summary(L))


if __name__ == "__main__":
    main()
