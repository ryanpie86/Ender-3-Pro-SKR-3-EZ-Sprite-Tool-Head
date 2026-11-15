#!/usr/bin/env python3
"""Geometry twin of Foot/Foot.py: STL, fit checks and render (see generate_stl.py).

The foot is modelled in print orientation (on its end face, keys running up
Z). The STL is written exactly like that; the fit check and the render stand
it up under the rail the way it is installed.
"""
import os
import sys

import numpy as np
from manifold3d import CrossSection, Manifold

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "Foot"))
sys.path.insert(0, HERE)
import Foot as P  # noqa: E402
from generate_stl import box, render_view, slot_void, to_trimesh  # noqa: E402


def prism_z(poly_uv, cx, y0, z0, z1):
    """Extrude a (u, v) polygon up +Z: u -> X about cx, v -> Y above y0."""
    pts = [(cx + u, y0 + v) for (u, v) in poly_uv]
    area = sum(xa * yb - xb * ya for (xa, ya), (xb, yb) in zip(pts, pts[1:] + pts[:1]))
    if area < 0:
        pts.reverse()
    return Manifold.extrude(CrossSection([pts]), z1 - z0).translate([0, 0, z0])


def build_foot(L):
    """Print orientation, as the Fusion script models it."""
    foot = box(0, 0, 0, P.FOOT_W, L["foot_h"], L["key_len"])
    for kx in L["key_x"]:
        foot += prism_z(P.key_profile(), kx, L["key_y0"], 0.0, L["key_len"])
    return foot


def installed(L, foot):
    """Stand the printed foot up under the rail: print +Y -> up, print +Z -> along the rail."""
    return foot.rotate([90, 0, 0]).translate([0, L["key_len"], 0])


def rail(L):
    """A rail end above the installed foot, true V-slot profile, 20 mm past each end of the foot."""
    H = L["foot_h"]
    r = box(0, -20, H, P.FOOT_W, L["key_len"] + 20, H + P.RAIL_W)
    for x in L["slot_x"]:
        r -= slot_void(x, H, -21, L["key_len"] + 21)
    return r


def check(L, foot):
    rep = []
    t = to_trimesh(foot)
    bodies = len(foot.decompose())
    rep.append("foot: watertight={} bodies={} extents={} volume={:.0f} mm3".format(t.is_watertight, bodies, np.round(t.bounds[1] - t.bounds[0], 2), foot.volume()))
    assert t.is_watertight and bodies == 1
    assert np.allclose(t.bounds[0], [0, 0, 0], atol=1e-6)
    assert np.allclose(t.bounds[1], [P.FOOT_W, L["foot_h"] + P.KEY_H, L["key_len"]], atol=1e-3)
    # the print's first layer is the whole end face: block plus both key sections, one flat polygon
    first = foot.slice(0.5).to_polygons()
    rep.append("first layer: {} polygon(s), {:.0f} mm2".format(len(first), CrossSection(first).area()))
    assert len(first) == 1
    up = installed(L, foot)
    r = rail(L)
    v = (up ^ r).volume()
    rep.append("interference foot vs rail {:.4f} mm3".format(v))
    assert v < 1e-6
    for kx in L["key_x"]:   # keys sit entirely inside the slots' voids, over the full length
        key = prism_z(P.key_profile(), kx, L["key_y0"], 0.0, L["key_len"]).rotate([90, 0, 0]).translate([0, L["key_len"], 0])
        assert (key - slot_void(kx, L["foot_h"], -1, L["key_len"] + 1)).volume() < 1e-6
    assert P.KEY_W > P.ENC.SLOT_THROAT_W + 1.0
    return rep


def main():
    L = P.layout()
    foot = build_foot(L)
    stl_dir, ren_dir = os.path.join(HERE, "stl"), os.path.join(HERE, "renders")
    os.makedirs(stl_dir, exist_ok=True)
    os.makedirs(ren_dir, exist_ok=True)
    for line in check(L, foot):
        print(line)
    to_trimesh(foot).export(os.path.join(stl_dir, "foot.stl"))
    print("wrote", os.path.join(stl_dir, "foot.stl"), "(print orientation: on its end, keys vertical)")
    if "--no-render" not in sys.argv:
        tf = to_trimesh(installed(L, foot))
        tr = to_trimesh(rail(L))
        print("rendered", render_view("foot.png", [(tf, "#4a90d9", 1), (tr, "#777777", 0.45)], 25, -55,
                                      "TPU foot slid onto a 4040 rail end: full-length V-slot keys in the bottom slots, no bolts", ren_dir))
        print("rendered", render_view("foot_print.png", [(to_trimesh(foot), "#4a90d9", 1)], 30, -60,
                                      "Foot as printed: on its end face, keys vertical, no overhangs", ren_dir))
    print()
    print(P.summary(L))


if __name__ == "__main__":
    main()
