#!/usr/bin/env python3
"""Sprite harness slack take-up for the Ender 3 Pro, all printed: a mast on the 2020 top bar, a
retractable reel at its top, and a roller catch the sleeve slides through. Derived from the Kobra
Max mast: 295 tall, one foot on the arm's side, two M5 T-nuts.

Why: the Sprite's cable sleeve is thrown over the gantry's top bar. As Z rises the path
from the toolhead to the frame anchor shortens and the loop goes slack (the apex wants
to rise by about HALF the Z change, ~226 mm over the full 452 mm); as X moves the apex
shifts sideways. A retractable reel hanging from a mast ~300 mm above the bar holds the
sleeve up through a catch with rollers: Z up -> the reel retracts, no slack; X moves ->
the sleeve slides through the rollers.

Two printed assemblies, no bought hardware beyond two M5 x 8 screws and T-nuts:
  mast  : ONE piece. A 20 wide foot keyed into the top bar's 6 mm slot, reaching out along
          the bar on the arm's side only (2 x M5 T-nuts), a 20 x 20 column 295 mm tall, an
          arm along the bar with a slotted tip plate for the reel's carabiner.
          Printed lying on its back so the layers run along the column.
  catch : a printed shackle: one 16 x 20 band with rounded ends, hung from the reel's
          split ring by a tab on the arch. The straight side is a printed snap pin: round
          head, plain shank carrying a loose printed sleeve (the roller), and a slotted
          barbed tip that clicks through the far leg. Squeeze the tip to pull it and
          admit the cable sleeve.

Frame: origin on the bar's top face at the slot centre under the mast. +X along the
bar, +Y across it, +Z up. The sleeve runs along Y through the catch (front to back).

    python3 cable_mast.py            # STLs + checks + renders into ./out
    python3 cable_mast.py --no-render
"""
import os
import sys

import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold

HERE = os.path.dirname(os.path.abspath(__file__))

from mast_params import *  # noqa: F401,F403  (every constant and derived value lives there)


def box(x0, y0, z0, x1, y1, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def cyl_z(cx, cy, z0, z1, d, n=96):
    return Manifold.cylinder(z1 - z0, d / 2, d / 2, n).translate([cx, cy, z0])


def cyl_x(x0, x1, cy, cz, d, n=96):
    return Manifold.cylinder(x1 - x0, d / 2, d / 2, n).rotate([0, 90, 0]).translate([x0, cy, cz])


def cyl_y(y0, y1, cx, cz, d, n=96):
    return Manifold.cylinder(y1 - y0, d / 2, d / 2, n).rotate([-90, 0, 0]).translate([cx, y0, cz])


def hex_x(x0, x1, cy, cz, af):
    return Manifold.cylinder(x1 - x0, af / np.sqrt(3), af / np.sqrt(3), 6).rotate([0, 90, 0]).translate([x0, cy, cz])


def prism_yz(pts, x0, x1):
    """Polygon in (y, z), extruded from x0 to x1 (winding fixed)."""
    area = sum(ya * zb - yb * za for (ya, za), (yb, zb) in zip(pts, pts[1:] + pts[:1]))
    if area < 0:
        pts = list(reversed(pts))
    m = Manifold.extrude(CrossSection([pts]), x1 - x0)
    return m.transform([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0]])      # (u, v, w) -> (w + x0, u, v)


def prism_xz(pts, y0, y1):
    area = sum(xa * zb - xb * za for (xa, za), (xb, zb) in zip(pts, pts[1:] + pts[:1]))
    if area < 0:
        pts = list(reversed(pts))
    return Manifold.extrude(CrossSection([pts]), y1 - y0).rotate([90, 0, 0]).translate([0, y1, 0])


# ---------------------------------------------------------------------------- mast
def build_mast():
    """Base + column + swept arm, one body, in the installed frame, entirely in the frame's plane
    (XZ) and with every corner in that plane a radius: street-light shape, up, over along the bar,
    a rounded paddle tip with the carabiner hole running across the bar."""
    d = ARM_DIR
    # base plate: ONE foot, from the column's outer face out along the bar on the arm's side, its far
    # end a semicircle; the key into the slot runs under it
    x_end_c = BASE_X1 - d * BASE_END_R                                     # centre of the rounded end
    xa, xb = sorted([BASE_X0, x_end_c])
    m = box(xa, -BASE_W / 2, 0, xb, BASE_W / 2, BASE_T)
    m += cyl_y(-BASE_W / 2, BASE_W / 2, x_end_c, BASE_T / 2, BASE_T)
    ka, kb = sorted([KEY_X0, KEY_X1])
    m += box(ka, -KEY_W / 2, -KEY_H, kb, KEY_W / 2, 0.01)
    # column, with a concave radius into the foot on the arm's side; the outer face runs straight down
    m += box(-COL_X / 2, -COL_Y / 2, 0, COL_X / 2, COL_Y / 2, ARM_TOP_Z)
    x0, x1 = sorted([d * COL_X / 2, d * (COL_X / 2 + FOOT_R)])
    fil = box(x0, -COL_Y / 2, BASE_T - 0.01, x1, COL_Y / 2, BASE_T + FOOT_R)
    fil -= cyl_y(-COL_Y / 2 - 1, COL_Y / 2 + 1, d * (COL_X / 2 + FOOT_R), BASE_T + FOOT_R, 2 * FOOT_R)
    m += fil
    # arm, full thickness, from the column to the plate's back; the plate carries on to the tip
    x_a0, x_a1 = sorted([d * (-COL_X / 2), BACK_X])
    m += box(x_a0, -COL_Y / 2, ARM_Z0, x_a1, COL_Y / 2, ARM_TOP_Z)
    # inside radius: the square in the corner minus the quarter circle
    xf0, xf1 = sorted([d * COL_X / 2, d * (COL_X / 2 + INNER_R)])
    fil = box(xf0, -COL_Y / 2, ARM_Z0 - INNER_R, xf1, COL_Y / 2, ARM_Z0 + 0.01)
    fil -= cyl_y(-COL_Y / 2 - 1, COL_Y / 2 + 1, d * (COL_X / 2 + INNER_R), ARM_Z0 - INNER_R, 2 * INNER_R, 128)
    m += fil
    # outside radius on the column/arm corner (the side away from the arm)
    xc = -d * COL_X / 2
    xo0, xo1 = sorted([xc, xc + d * OUTER_R])
    corner = box(xo0, -COL_Y / 2 - 1, ARM_TOP_Z - OUTER_R, xo1, COL_Y / 2 + 1, ARM_TOP_Z + 1)
    corner -= cyl_y(-COL_Y / 2 - 2, COL_Y / 2 + 2, xc + d * OUTER_R, ARM_TOP_Z - OUTER_R, 2 * OUTER_R, 128)
    m -= corner
    # tip plate: a stadium PAD_T thick, flush with the -Y face (the bed), from the arm's end to the tip,
    # with concave radii into the arm's edges at its back end, and the slot (a smaller stadium) through it
    xb0, xb1 = sorted([BACK_X, TIP_X])
    plate = box(xb0, PAD_Y0, EYE_CZ - PAD_R, xb1, PAD_Y1, EYE_CZ + PAD_R)
    plate += cyl_y(PAD_Y0, PAD_Y1, TIP_X, EYE_CZ, 2 * PAD_R) + cyl_y(PAD_Y0, PAD_Y1, BACK_X, EYE_CZ, 2 * PAD_R)
    m += plate
    for sz in (-1, 1):
        zl = EYE_CZ + sz * COL_Y / 2                                        # the arm's edge line
        xf = BACK_X - d * PAD_FILLET_DX                                     # fillet circle centre
        zf = zl + sz * PAD_FILLET_R
        x0, x1 = sorted([xf, BACK_X])
        z0, z1 = sorted([zl, zl + sz * PAD_FILLET_R])
        fil = box(x0, PAD_Y0, z0, x1, PAD_Y1, z1)
        fil -= cyl_y(PAD_Y0 - 1, PAD_Y1 + 1, xf, zf, 2 * PAD_FILLET_R)
        m += fil
    slot = box(xb0, -COL_Y, EYE_CZ - HOLE_D / 2, xb1, COL_Y, EYE_CZ + HOLE_D / 2)
    slot += cyl_y(-COL_Y, COL_Y, TIP_X, EYE_CZ, HOLE_D) + cyl_y(-COL_Y, COL_Y, BACK_X, EYE_CZ, HOLE_D)
    m -= slot
    for sx in SCREW_XS:
        m -= cyl_z(d * sx, 0, -KEY_H - 1, BASE_T + 1, M5_CLEAR)
        m -= cyl_z(d * sx, 0, BASE_T - 4.0, BASE_T + 1, M5_HEAD_D)    # counterbore: an M5 x 8 passes 4 mm of plate and gets 4 mm of T-nut
    return m


def mast_print():
    """Lying on its back: the whole part is in the frame's plane, so it lies flat, 20 mm thick,
    with the paddle hole vertical. Layers run along the column and the arm."""
    return build_mast().rotate([90, 0, 0]).translate([0, 0, COL_Y / 2])


# ---------------------------------------------------------------------------- catch (D-ring)
def build_dring_local():
    """The shackle, origin at the pin axis midpoint; pin along X, cable along Y, arch up +Z.
    One band HOOP_T wide in its plane and HOOP_W deep along the cable: two legs that reach below
    the pin axis and end in a half-round (seen along the pin) round the pin holes, a half-ring
    arch, a tab on top with the same half-round end. Prints flat on either face."""
    t = HOOP_T / 2
    d = Manifold()
    for sx in (-1, 1):
        x0, x1 = sorted([sx * (R_HOOP - t), sx * (R_HOOP + t)])
        d += box(x0, -HOOP_W / 2, 0, x1, HOOP_W / 2, LEG_H)                                       # leg above the axis
        end = box(x0, -HOOP_W / 2, -LEG_DROP - 1, x1, HOOP_W / 2, 0.01)                          # below the axis ...
        end = end ^ cyl_x(x0 - 1, x1 + 1, 0, 0, 2 * LEG_DROP)                                     # ... rounded about the pin axis
        d += end
    arch = cyl_y(-HOOP_W / 2, HOOP_W / 2, 0, LEG_H, 2 * (R_HOOP + t)) - cyl_y(-HOOP_W / 2 - 1, HOOP_W / 2 + 1, 0, LEG_H, 2 * (R_HOOP - t))
    arch -= box(-R_HOOP - HOOP_T, -HOOP_W, -R_HOOP - HOOP_T, R_HOOP + HOOP_T, HOOP_W, LEG_H)       # keep the top half only
    d += arch
    top = LEG_H + R_HOOP + t
    tz = top + TAB_H
    tab = box(-TAB_T / 2, -HOOP_W / 2, top - 1, TAB_T / 2, HOOP_W / 2, tz)
    tab += box(-TAB_T / 2, -HOOP_W / 2, tz - 0.01, TAB_T / 2, HOOP_W / 2, tz + HOOP_W / 2 + 1) ^ cyl_x(-TAB_T, TAB_T, 0, tz, HOOP_W)   # half-round end
    tab -= cyl_x(-TAB_T, TAB_T, 0, tz, TAB_HOLE)
    d += tab
    d -= cyl_x(-R_HOOP - t - 1, R_HOOP + t + 1, 0, 0, PIN_HOLE)                                  # pin holes through both legs
    return d


def build_pin_local():
    """Snap pin, axis along +X from the head's outer face at x = 0: round head, plain shank, a barbed
    slotted tip, and a flat along the underside (print lying on it, slot vertical)."""
    p = cyl_x(0, PIN_HEAD_T, 0, 0, PIN_HEAD_D)
    p += cyl_x(PIN_HEAD_T - 0.01, PIN_L, 0, 0, PIN_D)
    p += cyl_x(BARB_X0, BARB_X0 + BARB_L, 0, 0, BARB_D)
    p += Manifold.cylinder(BARB_LEAD, BARB_D / 2, PIN_D / 2 - 0.3, 64).rotate([0, 90, 0]).translate([BARB_X0 + BARB_L, 0, 0])
    p -= box(PIN_L - PIN_SLOT_L, -PIN_SLOT_W / 2, -PIN_D, PIN_L + 1, PIN_SLOT_W / 2, PIN_D)      # slot, vertical
    p -= box(-1, -PIN_HEAD_D, -PIN_HEAD_D, PIN_L + 1, PIN_HEAD_D, -(PIN_D / 2 - PIN_FLAT))       # the flat
    return p


def pin_print():
    """Lying on its flat, slot vertical: the fingers flex along the layers, not across them."""
    return build_pin_local().translate([0, 0, PIN_D / 2 - PIN_FLAT])


def build_roller_local():
    return cyl_x(0, ROLLER_L, 0, 0, ROLLER_OD) - cyl_x(-1, ROLLER_L + 1, 0, 0, ROLLER_BORE)


def roller_print():
    return build_roller_local().rotate([0, -90, 0]).translate([0, 0, ROLLER_L])


def dring_print():
    """Flat on the bed (its -Y face down)."""
    return build_dring_local().rotate([90, 0, 0]).translate([0, 0, HOOP_W / 2])


def catch_parts_local():
    return [("pin", build_pin_local().translate([PIN_X0, 0, 0]), "#c9a227"),
            ("roller", build_roller_local().translate([-ROLLER_L / 2, 0, 0]), "#d9822b")]


def sleeve_local():
    """The harness ribbon lying on the roller, along Y: SLEEVE_W wide (along the pin), SLEEVE_T thick."""
    z = ROLLER_OD / 2
    return box(-SLEEVE_W / 2, -50, z, SLEEVE_W / 2, 50, z + SLEEVE_T)


def catch_installed_z(drop):
    """Z of the rod axis when the catch hangs `drop` mm below the mast eye."""
    return REEL_EYE_Z - drop - D_HEIGHT - TAB_H


def bar(length=200.0, depth=40.0):
    """The top bar: a 2020, 20 mm wide face up, 6 mm slot, drawn 20 deep."""
    depth = min(depth, 20.0)
    b = box(-length / 2, -BAR_W / 2, -depth, length / 2, BAR_W / 2, 0)
    b -= box(-length / 2 - 1, -SLOT_W / 2, -1.8, length / 2 + 1, SLOT_W / 2, 0.1)
    b -= box(-length / 2 - 1, -5.5, -8.0, length / 2 + 1, 5.5, -1.8)
    return b


def to_trimesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts), process=False)


def check():
    rep = []
    mast = build_mast()
    assert to_trimesh(mast).is_watertight and len(mast.decompose()) == 1, "mast"
    tm = to_trimesh(mast_print())
    ext = tm.bounds[1] - tm.bounds[0]
    rep.append("mast: one piece in the frame's plane, {:.0f} tall x {:.0f} along the bar ({:.0f} arm, {:.0f} foot on the arm's side) x {:.0f} thick, {:.0f} cm3 solid; tip plate {:.0f} thick flush with the bed face, {:.0f} tall, with a {:.0f} x {:.0f} slot across the bar ({:.0f} mm wall all round), slot centre {:.0f} above the bar, {:.0f} to {:.0f} along it".format(ARM_TOP_Z, max(ARM_X1, abs(BASE_X1)) + COL_X / 2, ARM_REACH, FOOT_LEN, COL_Y, mast.volume() / 1000, PAD_T, 2 * PAD_R, HOLE_D, HOLE_D + SLOT_STRAIGHT, PAD_R - HOLE_D / 2, EYE_CZ, abs(BACK_X), abs(TIP_X)))
    # the plate must lie on the bed: every point of it is at y >= PAD_Y0 and it touches PAD_Y0; nothing floats
    tp = to_trimesh(mast_print())
    v = tp.vertices
    assert np.any((np.abs(v[:, 2]) < 1e-6) & (np.abs(v[:, 0] - HANG_X) < PAD_R)), "the tip plate does not lie on the bed"
    assert PAD_R - HOLE_D / 2 >= 6.0, "too little material round the hole"
    rep.append("mast print footprint lying flat: {:.0f} x {:.0f} mm, {:.0f} tall".format(ext[0], ext[1], ext[2]))
    assert abs(ext[2] - COL_Y) < 1e-6 and abs(tm.bounds[0][2]) < 1e-6, "mast does not lie flat"
    td = to_trimesh(dring_print())
    assert abs(td.bounds[0][2]) < 1e-6 and abs(td.bounds[1][2] - HOOP_W) < 1e-6, "D-ring does not lie flat"
    rep.append("D-ring print: flat slab {:.0f} thick, {:.0f} x {:.0f} footprint".format(HOOP_W, td.bounds[1][0] - td.bounds[0][0], td.bounds[1][1] - td.bounds[0][1]))
    assert ext[0] <= BED and ext[1] <= BED, "does not fit the {:.0f} x {:.0f} bed".format(BED, BED)
    assert (mast ^ bar()).volume() < 1e-6, "mast base (or its key) hits the bar"
    assert KEY_W < SLOT_W
    for sx in SCREW_XS:
        assert sx + M5_HEAD_D / 2 < abs(BASE_X1) - BASE_END_R - 1, "screw too close to the foot's rounded end"
    assert min(SCREW_XS) - M5_HEAD_D / 2 > COL_X / 2 + FOOT_R, "inner screw under the foot radius"
    # the foot is on the arm's side: the tip load presses it onto the bar and the screws hold the column's
    # outer edge down; the lever from the column's outer face to the inner screw
    rep.append("foot: {:.0f} long on the arm's side, 2 x M5 at {:.0f} and {:.0f} from the column centre; the column's outer edge is {:.0f} mm from the inner screw".format(FOOT_LEN, SCREW_XS[0], SCREW_XS[1], SCREW_XS[0] + COL_X / 2))
    # column stiffness: PETG cantilever, bending about the weaker axis, sideways pull at the eye
    I = min(COL_X * COL_Y ** 3, COL_Y * COL_X ** 3) / 12.0
    L, A = ARM_Z0, abs(TIP_X)          # worst case: the clip at the slot's far end
    # vertical pull F at the eye: arm bends (F A^3/3EI), its root moment F*A rotates the column top (M L / EI) and the arm tip drops by that angle * A
    dv = TIP_LOAD_N * A ** 3 / (3 * E_PETG * I) + (TIP_LOAD_N * A * L / (E_PETG * I)) * A
    # a sideways pull F at the eye: column cantilever plus the arm as a lever
    dh = TIP_LOAD_N * L ** 3 / (3 * E_PETG * I)
    rep.append("deflection at the eye under {:.0f} N: {:.1f} mm down (arm {:.0f} mm), {:.1f} mm sideways (PETG, {:.0f} x {:.0f} section)".format(TIP_LOAD_N, dv, A, dh, COL_X, COL_Y))
    assert dv < 15.0 and dh < 10.0, "mast too floppy"
    # catch
    dring, pin, roller = build_dring_local(), build_pin_local(), build_roller_local()
    for name, m in (("dring", dring), ("pin", pin), ("roller", roller)):
        t = to_trimesh(m)
        assert t.is_watertight and len(m.decompose()) == 1, name
    rep.append("shackle: one band {:.0f} wide x {:.0f} deep, {:.0f} clear inside (sleeve {:.0f}), {:.0f} from pin axis to the arch top + {:.0f} tab; legs reach {:.0f} below the axis and end in a half-round round the O{:.1f} pin holes ({:.1f} mm wall); roller O{:.0f} x {:.1f}".format(
        HOOP_T, HOOP_W, RING_IN, SLEEVE_W, D_HEIGHT, TAB_H, LEG_DROP, PIN_HOLE, HOOP_W / 2 - PIN_HOLE / 2, ROLLER_OD, ROLLER_L))
    assert HOOP_W / 2 - PIN_HOLE / 2 >= 2.0, "too little wall round the pin hole"
    assert HOOP_W / 2 - TAB_HOLE / 2 >= 2.0, "too little wall round the tab hole"
    pin_in = pin.translate([PIN_X0, 0, 0])
    assert (pin_in ^ dring).volume() < 1e-6, "pin hits the shackle outside its holes"
    rol = roller.translate([-ROLLER_L / 2, 0, 0])
    assert (rol ^ dring).volume() < 1e-6 and (rol ^ pin_in).volume() < 1e-6
    assert BARB_X0 >= PIN_HEAD_T + FAR_FACE, "barb would sit inside the far leg"
    assert BARB_D > PIN_HOLE + 0.4, "barb too small to retain"
    assert PIN_FINGER_STRAIN < E_PETG_STRAIN_OK, "snap fingers would yield: lengthen PIN_SLOT_L or shrink BARB_D"
    rep.append("snap pin: O{:.0f} shank {:.1f} long, O{:.0f} x {:.0f} head, O{:.1f} barb {:.1f} past the far face, {:.1f} mm slot over {:.0f} mm; {:.1f} mm squeeze per finger, ~{:.1f} % strain".format(
        PIN_D, PIN_L, PIN_HEAD_D, PIN_HEAD_T, BARB_D, BARB_X0 - PIN_HEAD_T - FAR_FACE, PIN_SLOT_W, PIN_SLOT_L, (BARB_D - PIN_HOLE) / 2, 100 * PIN_FINGER_STRAIN))
    sl = sleeve_local()
    assert (sl ^ dring).volume() < 1e-6 and (sl ^ rol).volume() < 1e-6, "cable sleeve hits the shackle"
    clear_top = LEG_H + R_HOOP - HOOP_T / 2 - (ROLLER_OD / 2 + SLEEVE_T)
    rep.append("the {:.0f} x {:.0f} ribbon on the roller has {:.1f} mm to the arch and {:.1f} mm to each leg; the band is {:.0f} wide along the cable".format(SLEEVE_W, SLEEVE_T, clear_top, (RING_IN - SLEEVE_W) / 2, HOOP_W))
    assert clear_top >= RIBBON_CLEAR
    tp = to_trimesh(pin_print())
    assert abs(tp.bounds[0][2]) < 1e-6, "pin does not lie on its flat"
    rep.append("apex travel over {:.0f} mm of Z: ~{:.0f} mm; the reel cord must pay out at least that plus the margin you set at Z = 0".format(Z_TRAVEL, Z_TRAVEL / 2))
    return rep


def render(outdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    def draw(ax, t, color, alpha=1.0):
        t = t.subdivide_to_size(max_edge=6.0, max_iter=6)
        light = np.array([0.4, -0.6, 0.7]); light /= np.linalg.norm(light)
        shade = 0.45 + 0.55 * np.clip(t.face_normals @ light, 0, 1)
        rgb = np.array(matplotlib.colors.to_rgb(color))
        ax.add_collection3d(Poly3DCollection(t.vertices[t.faces], facecolors=np.clip(shade[:, None] * rgb[None, :], 0, 1), edgecolors="none", alpha=alpha))

    def view(name, parts, elev, azim, title):
        fig = plt.figure(figsize=(9, 8), dpi=130)
        ax = fig.add_subplot(111, projection="3d")
        for t, c, a in parts:
            draw(ax, t, c, a)
        allv = np.vstack([t.vertices for t, _, a in parts if a == 1.0])
        lo, hi = allv.min(axis=0), allv.max(axis=0); c = (lo + hi) / 2; r = (hi - lo).max() / 2
        ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
        ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=elev, azim=azim); ax.set_axis_off(); ax.set_title(title, fontsize=10)
        fig.tight_layout(); p = os.path.join(outdir, name); fig.savefig(p, facecolor="white"); plt.close(fig); return p

    mast = build_mast()
    drop = 120.0
    z0 = catch_installed_z(drop)
    catch = build_dring_local().translate([HANG_X, 0, z0])
    cparts = [(to_trimesh(m.translate([HANG_X, 0, z0])), c, 1.0) for _, m, c in catch_parts_local()]
    cord = cyl_z(HANG_X, 0, z0 + D_HEIGHT + TAB_H, REEL_EYE_Z - 40, 1.5)
    reel = Manifold.cylinder(12, 19, 19, 48).rotate([-90, 0, 0]).translate([HANG_X, -6, REEL_EYE_Z - 26])
    sleeve = sleeve_local().translate([HANG_X, 0, z0])
    bm = (to_trimesh(bar()), "#2a2a2a", 0.3)
    cl = [(to_trimesh(build_dring_local()), "#e8e3d6", 1.0), (to_trimesh(sleeve_local()), "#1f1f1f", 0.6)] + [(to_trimesh(m), c, 1.0) for _, m, c in catch_parts_local()]
    return [view("mast_assembly.png", [(to_trimesh(mast), "#e8e3d6", 1.0), (to_trimesh(catch), "#e8e3d6", 1.0), (to_trimesh(cord), "#222222", 1.0),
                                       (to_trimesh(reel), "#333333", 1.0), (to_trimesh(sleeve), "#1f1f1f", 0.6), bm] + cparts,
                 18, -60, "Mast on the 2020 top bar, one foot under the arm, reel clipped through the tip, D-ring {:.0f} mm below on the cord".format(drop)),
            view("mast_base.png", [(to_trimesh(mast), "#e8e3d6", 1.0), bm], 8, -88, "One keyed foot on the arm's side (R{:.0f}, 2 x M5), 20 x 20 column to {:.0f}, R{:.0f}/R{:.0f} into the {:.0f} mm arm, {:.0f} x {:.0f} slot".format(FOOT_R, ARM_TOP_Z, INNER_R, OUTER_R, ARM_REACH, HOLE_D, HOLE_D + SLOT_STRAIGHT)),
            view("catch_detail.png", cl, 20, -50, "Shackle: one {:.0f} mm band, half-round ends, O{:.0f} snap pin through both legs, loose roller; the barbed tip clicks past the far leg".format(HOOP_T, PIN_D)),
            view("catch_end.png", cl, 0, -90, "Shackle, looking along the cable: O{:.0f} roller, the {:.0f} x {:.0f} ribbon on it, {:.0f} mm clear inside".format(ROLLER_OD, SLEEVE_W, SLEEVE_T, RING_IN)),
            view("print_layout.png", [(to_trimesh(mast_print()), "#e8e3d6", 1.0), (to_trimesh(dring_print().translate([125, 20, 0])), "#e8e3d6", 1.0),
                                       (to_trimesh(roller_print().translate([125, 90, 0])), "#d9822b", 1.0), (to_trimesh(pin_print().translate([110, 130, 0])), "#c9a227", 1.0)],
                 40, -60, "Print layout: mast flat on its back, shackle flat, roller standing, pin lying on its flat")]


def main():
    outdir = os.path.join(HERE, "out")
    os.makedirs(outdir, exist_ok=True)
    for line in check():
        print(line)
    to_trimesh(mast_print()).export(os.path.join(outdir, "mast.stl"))
    to_trimesh(dring_print()).export(os.path.join(outdir, "catch_dring.stl"))
    to_trimesh(roller_print()).export(os.path.join(outdir, "catch_roller.stl"))
    to_trimesh(pin_print()).export(os.path.join(outdir, "catch_pin.stl"))
    for stale in ("mast_base.stl", "mast_top_eye.stl", "catch_spacer.stl", "base_top.png", "catch_frame.stl", "catch_rod.stl"):
        p = os.path.join(outdir, stale)
        if os.path.exists(p):
            os.remove(p)
    print("STLs in", outdir)
    if "--no-render" not in sys.argv:
        for p in render(outdir):
            print("render", p)


if __name__ == "__main__":
    main()
