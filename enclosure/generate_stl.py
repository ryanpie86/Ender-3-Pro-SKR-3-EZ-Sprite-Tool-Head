#!/usr/bin/env python3
"""Geometry twin of SKR3EZ_Enclosure/SKR3EZ_Enclosure.py.

Imports the SAME constants and layout() from the Fusion script, builds the
base and lid with manifold3d (CSG), writes printable STLs, runs fit checks
(watertight, one body, lid-on-base, PCB, driver row, fan, the foot rail with
its bottom V-slots, the printed feet) and renders PNG views.

    pip install manifold3d trimesh numpy matplotlib
    python3 generate_stl.py              # stl/*.stl + renders/*.png
    python3 generate_stl.py --no-render

Any dimension change belongs in the Fusion script; this file only consumes it.
"""
import os
import sys

import math

import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "SKR3EZ_Enclosure"))
import SKR3EZ_Enclosure as P  # noqa: E402

SEG = 64


def box(x0, y0, z0, x1, y1, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def cyl_z(cx, cy, z0, z1, d):
    return Manifold.cylinder(z1 - z0, d / 2.0, d / 2.0, SEG).translate([cx, cy, z0])


def cyl_x(x0, x1, cy, cz, d):
    return Manifold.cylinder(x1 - x0, d / 2.0, d / 2.0, SEG).rotate([0, 90, 0]).translate([x0, cy, cz])


def cyl_y(y0, y1, cx, cz, d):
    return Manifold.cylinder(y1 - y0, d / 2.0, d / 2.0, SEG).rotate([-90, 0, 0]).translate([cx, y0, cz])


def prism_y(poly_uv, cx, z0, y0, y1):
    """Extrude a (u, v) polygon along +Y: u -> X about cx, v -> Z above z0, from y0 to y1."""
    pts = [(cx + u, z0 + v) for (u, v) in poly_uv]
    area = sum(x0 * y1_ - x1 * y0_ for (x0, y0_), (x1, y1_) in zip(pts, pts[1:] + pts[:1]))
    if area < 0:
        pts.reverse()
    solid = Manifold.extrude(CrossSection([pts]), y1 - y0)        # along +Z
    return solid.rotate([90, 0, 0]).translate([0, y1, 0])           # Z -> -Y, then shift so it spans y0..y1


def prism_x(poly_yz, x0, x1):
    """Extrude a (y, z) polygon along +X from x0 to x1."""
    pts = list(poly_yz)
    area = sum(a * d - c * b for (a, b), (c, d) in zip(pts, pts[1:] + pts[:1]))
    if area < 0:
        pts.reverse()
    solid = Manifold.extrude(CrossSection([pts]), x1 - x0)        # (y, z, t) with t along +Z
    # want (x = x0 + t, y, z): rotate so Z -> X: Ry(+90): (x,y,z) -> (z, y, -x); then (y,z,t) -> (t, z, -y)... do it in two steps
    s = solid.rotate([0, 90, 0])           # (y, z, t) -> (t, z, -y)
    s = s.rotate([90, 0, 0])               # (t, z, -y) -> (t, y, z)
    return s.translate([x0, 0, 0])


def cove_y(x_wall, z_under, y0, y1, r):
    """Concave fillet (cove) of radius r in the corner between a wall face at x = x_wall
    (material at x > x_wall) and an underside at z = z_under (material above), along Y."""
    blk = box(x_wall - r, y0, z_under - r, x_wall, y1, z_under)
    return blk - cyl_y(y0 - 1, y1 + 1, x_wall - r, z_under - r, 2 * r)


def flare_ring(cx, cy, z0, r_in, r):
    """Concave fillet ring around a vertical cylinder of radius r_in standing on z0: revolve the
    region between the cylinder, the floor and a quarter circle of radius r."""
    pts = [(r_in, 0.0), (r_in + r, 0.0)]
    n = 16
    for i in range(1, n + 1):
        a = math.radians(270.0 - 90.0 * i / n)
        pts.append((r_in + r + r * math.cos(a), r + r * math.sin(a)))
    ring = Manifold.revolve(CrossSection([pts]), SEG)        # manifold revolves about Y and makes that the Z axis
    return ring.translate([cx, cy, z0])


def slot_void(cx, face_z, y0, y1):
    """The V-slot cut into a rail whose face is at face_z, the slot going UP (+Z) into it."""
    return prism_y(P.slot_profile(below=0.05), cx, face_z, y0, y1)


def key_prism(cx, z0, y0, y1):
    return prism_y(P.key_profile(), cx, z0, y0, y1)


def build_base(L):
    ox, oy = L["outer_x"], L["outer_y"]
    W, F = P.WALL, P.FLOOR
    base = box(0, 0, 0, ox, oy, L["wall_top"])
    base -= box(W, W, F, ox - W, oy - W, L["wall_top"] + 1)
    h = P.POST / 2.0
    for (px, py) in L["posts"]:
        base += box(px - h, py - h, F, px + h, py + h, L["post_top"])
        base -= cyl_z(px, py, L["post_top"] - P.POST_HOLE_DEPTH, L["post_top"] + 1, P.POST_HOLE_D)
    for (sx, sy) in L["standoffs"].values():
        base += cyl_z(sx, sy, F, F + P.STANDOFF_H, P.STANDOFF_D)
        base -= cyl_z(sx, sy, -1, F + P.STANDOFF_H + 1, P.STANDOFF_HOLE_D)
    t = W + 1.0
    fx, fz = L["fan_center"]
    base -= cyl_y(-t, t, fx, fz, P.FAN_HOLE_D)
    for (sx, sz) in L["fan_screws"]:
        base -= cyl_y(-t, t, sx, sz, P.FAN_SCREW_D)
    for (wall, u0, u1, z0, z1) in L["cutouts"]:
        if wall == "front":
            base -= box(u0, -t, z0, u1, t, z1)
        elif wall == "back":
            base -= box(u0, oy - t, z0, u1, oy + t, z1)
        elif wall == "left":
            base -= box(-t, u0, z0, t, u1, z1)
        else:
            base -= box(ox - t, u0, z0, ox + t, u1, z1)
    for (x0, x1, z0, z1) in L["rear_vents"]:
        base -= box(x0, oy - t, z0, x1, oy + t, z1)
    by0, by1 = L["bar_y"]
    x0, x1, z0, z1 = L["bar_low"]
    base += box(x0, by0, z0, x1, by1, z1)
    x0, x1, z0, z1 = L["bar_top"]
    base += box(x0, by0, z0, x1, by1, z1)
    ky0, ky1 = L["key_y"]
    for kx in L["key_x"]:
        base += key_prism(kx, L["key_z0"], ky0, ky1)
    ct = L["col_top"]
    fy0, fy1 = L["strip_y"]
    base += prism_y(L["flange_poly"], 0.0, 0.0, fy0, fy1)
    for (bx0, bx1, by0, by1, bz0, bz1) in L["col_blocks"]:
        base += box(bx0, by0, bz0, bx1, by1, bz1)
    for tri in L["col_webs"]:
        base += prism_x(tri, ox, L["col_x"][1])
    for (y0, y1) in L["columns"]:
        base += key_prism(L["col_key_x"], ct, y0, y1)
    # strength fillets (fillet features in Fusion): cove under the hanger bar, standoff flares
    cy0, cy1 = L["bar_y"]
    base += cove_y(0.0, L["total_h"] - P.BAR_T, cy0, cy1, P.BAR_COVE_R)
    for (sx, sy) in L["standoffs"].values():
        base += flare_ring(sx, sy, F, P.STANDOFF_D / 2.0, P.STANDOFF_FILLET_R)
    return base


def build_lid(L, at_origin=True):
    ox, oy = L["outer_x"], L["outer_y"]
    lid = box(0, 0, 0, ox, oy, P.LID_T)
    lo, li = L["lip_outer"], L["lip_inner"]
    top = P.LID_T + P.LID_LIP_H
    lid += box(lo[0], lo[1], P.LID_T, lo[2], li[1], top)
    lid += box(lo[0], li[3], P.LID_T, lo[2], lo[3], top)
    lid += box(lo[0], lo[1], P.LID_T, li[0], lo[3], top)
    lid += box(li[2], lo[1], P.LID_T, lo[2], lo[3], top)
    for (x0, y0, x1, y1) in L["lid_bosses"]:
        lid += box(x0, y0, P.LID_T, x1, y1, P.LID_T + P.LID_BOSS_H)
    for (px, py) in L["lid_screws"]:
        lid -= cyl_z(px, py, -1, P.LID_T + P.LID_BOSS_H + 1, P.LID_SCREW_D)
        lid -= cyl_z(px, py, -1, P.LID_CBORE_DEPTH, P.LID_CBORE_D)
    if not at_origin:
        lid = lid.translate([L["lid_x0"], 0, 0])
    return lid


def base_print(L, base):
    """The base in its print orientation (P.PRINT_ORIENTATION), nothing below Z = 0."""
    tr = P.print_transform(L)
    if tr is None:
        return base
    angle, t = tr
    return base.rotate([angle, 0, 0]).translate(list(t))


def lid_assembled(L, lid):
    """Flip the printed lid over onto the base (as installed)."""
    return lid.mirror([0, 0, 1]).translate([0, 0, L["total_h"]])


def frame_parts(L):
    """The left foot rail above the box (with its two bottom V-slots, true profile) and the feet under its ends."""
    th = L["total_h"]
    y0, y1 = L["rail_y"]
    rail = box(-P.RAIL_W, y0, th, 0, y1, th + P.RAIL_W)
    for sx in P.SLOT_X:
        rail -= slot_void(-sx, th, y0 - 1, y1 + 1)
    feet = Manifold()
    for (fy0, fy1) in L["feet_y"]:
        feet += box(-P.RAIL_W, fy0, th - L["foot_h"], 0, fy1, th)
    yx0, yx1 = L["yrail_x"]
    yz0 = L["yrail_z0"]
    yy0, yy1 = L["yrail_y"]
    yrail = box(yx0, yy0, yz0, yx1, yy1, yz0 + 40)
    for sx in L["yrail_slots"]:
        yrail -= slot_void(sx, yz0, yy0 - 1, yy1 + 1)
    cy0, cy1 = L["cross_y"]
    cross = box(0, cy0, th, 250, cy1, th + 40)
    return {"foot_rail": rail, "feet": feet, "y_rail": yrail, "cross_profile": cross}


def to_trimesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts), process=False)


def check(L, base, lid):
    rep = []
    for name, m in (("base", base), ("lid", lid)):
        t = to_trimesh(m)
        bodies = len(m.decompose())
        rep.append("{}: watertight={} bodies={} extents={} volume={:.0f} mm3".format(
            name, t.is_watertight, bodies, np.round(t.bounds[1] - t.bounds[0], 2), m.volume()))
        assert t.is_watertight and bodies == 1, name
    tb, tl = to_trimesh(base), to_trimesh(lid)
    assert np.allclose(tb.bounds[0], [-P.RAIL_W, 0, 0], atol=1e-3)
    assert np.allclose(tb.bounds[1], [L["col_x"][1], L["outer_y"], L["col_top"] + P.KEY_H], atol=1e-3)
    assert np.allclose(tl.bounds[1] - tl.bounds[0], [L["outer_x"], L["outer_y"], P.LID_T + P.LID_BOSS_H], atol=1e-3)
    lid_in = lid_assembled(L, lid)
    bz = L["board_z0"]
    px0, py0, px1, py1 = L["pcb_rect"]
    pcb = box(px0, py0, bz, px1, py1, bz + P.BOARD_T)
    for (sx, sy) in L["standoffs"].values():
        pcb -= cyl_z(sx, sy, bz - 1, bz + P.BOARD_T + 1, P.BOARD_HOLE_D)
    dx0, dy0, dx1, dy1 = L["driver_rect"]
    drivers = box(dx0, dy0, L["board_top"], dx1, dy1, L["driver_top"])
    fan = box(*L["fan_block"])
    frame = frame_parts(L)
    pairs = [("lid on base", base, lid_in), ("PCB vs base", base, pcb), ("PCB vs lid", lid_in, pcb),
             ("drivers vs base", base, drivers), ("drivers vs lid", lid_in, drivers),
             ("fan vs base", base, fan), ("fan vs lid", lid_in, fan), ("fan vs PCB", fan, pcb)]
    for fname, fm in frame.items():
        pairs.append(("base vs " + fname, base, fm))
        pairs.append(("lid vs " + fname, lid_in, fm))
    for name, a, b in pairs:
        v = (a ^ b).volume()
        rep.append("interference {:28s} {:.4f} mm3".format(name, v))
        assert v < 1e-6, "interference: " + name
    # every key sits entirely inside its slot's void (so inside the rail's envelope, touching no metal),
    # and its head is wider than the throat so the lips hold it up
    ky0, ky1 = L["key_y"]
    for kx in L["key_x"]:
        key = key_prism(kx, L["key_z0"], ky0, ky1)
        void = slot_void(kx, L["total_h"], ky0 - 1, ky1 + 1)
        assert (key ^ frame["foot_rail"]).volume() < 1e-6
        assert (key - void).volume() < 1e-6, "key pokes out of the slot profile"
        assert key.volume() > 0.9 * (ky1 - ky0) * 30.0        # it is a real key, not a sliver
        rep.append("key at X={:.0f}: {:.0f} mm3, {:.0f}% of the slot void".format(kx, key.volume(), 100 * key.volume() / void.volume() * (ky1 - ky0 + 2) / (ky1 - ky0)))
    assert P.KEY_W > P.SLOT_THROAT_W + 1.0
    for (y0, y1) in L["columns"]:   # the bracket key, where it is inside the Y rail, sits entirely in its slot void
        yy0 = max(y0, L["yrail_y"][0])
        key = key_prism(L["col_key_x"], L["col_top"], yy0, y1)
        void = slot_void(L["col_key_x"], L["yrail_z0"], yy0 - 1, y1 + 1)
        assert (key ^ frame["y_rail"]).volume() < 1e-6
        assert (key - void).volume() < 1e-6
        rep.append("bracket key inside the Y rail over {:.0f} mm; hanger bar keys inside the foot rail over {:.0f} mm".format(
            y1 - yy0, L["key_on_rail"][1] - L["key_on_rail"][0]))
    # the whole box is in front of the cross brace
    assert L["outer_y"] <= L["cross_y"][0]
    return rep


def render_view(fig_name, parts, elev, azim, title, outdir, crop=None):
    """parts: list of (trimesh, color, alpha). Writes a PNG and returns its path."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    def draw(ax, t, color, alpha=1.0):
        try:
            t = t.subdivide_to_size(max_edge=6.0, max_iter=8)
        except ValueError:                      # very long context parts: coarser is fine
            t = t.subdivide_to_size(max_edge=15.0, max_iter=8)
        light = np.array([0.4, -0.6, 0.7])
        light /= np.linalg.norm(light)
        shade = 0.45 + 0.55 * np.clip(t.face_normals @ light, 0, 1)
        rgb = np.array(matplotlib.colors.to_rgb(color))
        ax.add_collection3d(Poly3DCollection(t.vertices[t.faces], facecolors=np.clip(shade[:, None] * rgb[None, :], 0, 1),
                                             edgecolors="none", alpha=alpha))

    fig = plt.figure(figsize=(10, 7.5), dpi=130)
    ax = fig.add_subplot(111, projection="3d")
    for t, c, a in parts:
        draw(ax, t, c, a)
    allv = np.vstack([t.vertices for t, _, _ in parts]) if crop is None else np.array(crop)
    lo, hi = allv.min(axis=0), allv.max(axis=0)
    c = (lo + hi) / 2
    r = (hi - lo).max() / 2
    ax.set_xlim(c[0] - r, c[0] + r)
    ax.set_ylim(c[1] - r, c[1] + r)
    ax.set_zlim(c[2] - r, c[2] + r)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_title(title, fontsize=10)
    fig.tight_layout()
    path = os.path.join(outdir, fig_name)
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path


def render_section(L, base, lid, frame, outdir):
    """True cross-section across the mount: foot rail with the keys in its V-slots,
    hanger bar, bracket with its key in the Y rail's slot. The 3D views hide this
    inside the opaque rails, so this is the picture that proves the engagement."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    y_cut = (L["columns"][0][0] + L["columns"][0][1]) / 2.0
    parts = [(frame["foot_rail"], "#555555"), (frame["y_rail"], "#777777"), (frame["cross_profile"], "#b0b0b0"),
             (base, "#4a90d9"), (lid_assembled(L, lid), "#e07b39")]

    def polys(m):
        # rotate -90 deg about X: original Y -> -Z'. Slice at Z' = -y_cut, polygons come back as (X, Z).
        return [np.asarray(p) for p in m.rotate([-90, 0, 0]).slice(-y_cut).to_polygons()]

    def area(p):
        x, y = p[:, 0], p[:, 1]
        return 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)

    fig, axes = plt.subplots(1, 2, figsize=(14, 7), dpi=130, gridspec_kw={"width_ratios": [2, 1]})
    for ax in axes:
        for m, col in parts:
            for p in sorted(polys(m), key=lambda q: -abs(area(q))):
                ax.fill(p[:, 0], p[:, 1], color=col if area(p) > 0 else "white", lw=0)
        ax.set_aspect("equal")
        ax.set_xlabel("X (mm), + toward the screen")
        ax.set_ylabel("Z (mm)")
        ax.grid(True, lw=0.3, alpha=0.5)
    th = L["total_h"]
    axes[0].set_title("Section at Y = {:.0f} mm through the front column. Grey: foot rail (left), Y rail (top right), cross profile. Blue: base. Orange: lid".format(y_cut))
    axes[0].set_xlim(-50, L["col_x"][1] + 15)
    axes[0].set_ylim(-5, L["col_top"] + 45)
    axes[0].axhline(th, color="k", lw=0.6, ls="--")
    axes[0].text(-48, th + 1.5, "frame bottom plane", fontsize=8)
    axes[1].set_title("Detail: V-slot keys inside the foot rail's two bottom slots")
    axes[1].set_xlim(-P.RAIL_W - 2, 4)
    axes[1].set_ylim(th - 10, th + 14)
    fig.tight_layout()
    path = os.path.join(outdir, "section_mount.png")
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path


def render(L, base, lid, outdir):
    def view(fig_name, parts, elev, azim, title, crop=None):
        return render_view(fig_name, parts, elev, azim, title, outdir, crop)

    B, Lm = "#4a90d9", "#e07b39"
    tb, tl = to_trimesh(base), to_trimesh(lid)
    ta = to_trimesh(lid_assembled(L, lid))
    bz = L["board_z0"]
    px0, py0, px1, py1 = L["pcb_rect"]
    pcb = to_trimesh(box(px0, py0, bz, px1, py1, bz + P.BOARD_T))
    dx0, dy0, dx1, dy1 = L["driver_rect"]
    drv = to_trimesh(box(dx0, dy0, L["board_top"], dx1, dy1, L["driver_top"]))
    fan = to_trimesh(box(*L["fan_block"]))
    fr = {k: to_trimesh(v) for k, v in frame_parts(L).items()}
    out = []
    out.append(view("base_iso_front.png", [(tb, B, 1), (fan, "#555555", 0.9)], 32, -58,
                    "Base from the front-left: 40 mm fan in the front wall, hanger bar with V-slot keys along the left, slot-in brackets on the right"))
    out.append(view("base_iso_rear.png", [(tb, B, 1)], 32, 128,
                    "Base from the rear-right: USB-B / micro-SD / thermistor openings under the Y-rail bracket strip, cable notch and vents in the rear wall"))
    out.append(view("base_top.png", [(tb, B, 1), (pcb, "#2e8b57", 0.55), (drv, "#8b0000", 0.5), (fan, "#555555", 0.7)], 90, -90,
                    "Top view: PCB (green) with its USB edge to the right, driver row (red) along the rail side, fan (grey) at the front"))
    out.append(view("base_left.png", [(tb, B, 1)], 12, 180,
                    "Left side: the hanger bar with two V-slot keys that slide into the rail's bottom slots, no bolts"))
    out.append(view("lid_print_orientation.png", [(tl, Lm, 1)], 35, -50,
                    "Lid as printed (plate down): solid, lip and counterbored screw bosses"))
    out.append(view("base_print_orientation.png", [(to_trimesh(base_print(L, base)), "#4a90d9", 1)], 28, -50,
                    "Base as printed (%s wall on the bed): hanger bar, keys and bracket strip stand vertical" % P.PRINT_ORIENTATION))
    out.append(view("assembled.png", [(tb, B, 1), (ta, Lm, 1)], 30, -58, "Assembled: lid seated on the base"))
    te = to_trimesh(lid_assembled(L, lid).translate([0, 0, 40]))
    out.append(view("exploded.png", [(tb, B, 1), (pcb, "#2e8b57", 0.8), (te, Lm, 1)], 28, -58, "Exploded: base, PCB, lid"))
    ctx = [(fr["foot_rail"], "#777777", 1), (fr["feet"], "#9aa4ae", 1), (fr["cross_profile"], "#8a8a8a", 0.5),
           (fr["y_rail"], "#8a8a8a", 0.55), (tb, B, 1), (ta, Lm, 1)]
    crop = [[-50, min(0.0, L["rail_y"][0]) - 5, -L["foot_h"] + L["total_h"] - 5], [175, L["rail_y"][1] + 5, L["total_h"] + 80]]
    out.append(view("in_frame_iso.png", ctx, 25, -60,
                    "Under the frame: box protruding in front of the frame, keys in the left foot rail, keyed bracket strip up to the Y rail (translucent), cross brace behind the box, left-front foot between them", crop))
    out.append(view("in_frame_front.png", ctx, 0, -90,
                    "From the front: foot rail and Y rail above, box below the frame plane, bracket keys reach the Y rail's slot", crop))
    out.append(view("in_frame_right.png", ctx, 8, 0,
                    "From the right (screen side): USB-B and micro-SD openings face this way", crop))
    out.append(render_section(L, base, lid, frame_parts(L), outdir))
    return out


def main():
    L = P.layout()
    base, lid = build_base(L), build_lid(L)
    stl_dir, ren_dir = os.path.join(HERE, "stl"), os.path.join(HERE, "renders")
    os.makedirs(stl_dir, exist_ok=True)
    os.makedirs(ren_dir, exist_ok=True)
    for line in check(L, base, lid):
        print(line)
    bp = base_print(L, base)
    tbp = to_trimesh(bp)
    assert tbp.bounds[0][2] > -1e-6 and abs(tbp.bounds[0][1]) < 1e-6, "printed base must sit on Z = 0"
    to_trimesh(bp).export(os.path.join(stl_dir, "skr3ez_enclosure_base.stl"))
    to_trimesh(lid).export(os.path.join(stl_dir, "skr3ez_enclosure_lid.stl"))
    print("wrote STLs to", stl_dir)
    if "--no-render" not in sys.argv:
        for p in render(L, base, lid, ren_dir):
            print("rendered", p)
    print()
    print(P.summary(L))


if __name__ == "__main__":
    main()
