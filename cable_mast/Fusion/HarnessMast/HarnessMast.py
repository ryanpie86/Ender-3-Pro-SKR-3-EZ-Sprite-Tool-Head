"""Ender 3 Pro Sprite harness slack take-up - Fusion 360 script (derived from the Kobra Max mast).

Builds four bodies in a fresh design, every dimension from ../../mast_params.py (the same
file cable_mast.py uses for the STLs, checks and renders):

  Mast    one piece: a 20 wide foot keyed into the 2020 top bar's 6 mm slot, reaching out
          along the bar on the arm's side only with a semicircular end and 2 x M5 T-nut
          holes, 20 x 20 column to 295 with an R12 radius into the foot, R40 inside / R20
          outside radii into a 75 mm arm that sweeps along the bar (to the right, in the
          frame's plane), a 10 mm tip plate lying on the bed face, blended into the arm with
          R5 radii, with a 14 x 44 slot across the bar for the reel's carabiner(s) to move
          along. Built installed, then laid flat on its back by a Move: print as it sits.
  DRing   the shackle: one 5 mm band, 14 deep along the cable; the legs reach below the pin
          and end in half-rounds about the pin axis, a half-ring arch, a tab with the same
          half-round end. Modelled flat on XY, print-ready, 150 mm +X of the mast.
  Pin     snap pin: round head, 5 mm shank, slotted barbed tip that clicks through the far
          leg; a flat along its underside. Modelled lying on that flat, slot vertical.
  Roller  12 x 28.5 sleeve, 5.6 bore, standing, beside the pin.

Run: Scripts and Add-Ins > + > Script or add-in from device > pick this FOLDER > Run, in a
new design with Z up. Export each body as STL from the browser. Edit mast_params.py, run
again. CI runs this file against a stub adsk package (../tests/run_mock.py) to catch API
mistakes; Fusion itself is the real test.

Fusion's API works in cm: every mm value goes through mm().
"""
try:
    import adsk.core, adsk.fusion, adsk.cam  # noqa: F401
    HAVE_ADSK = True
except ImportError:  # pragma: no cover
    HAVE_ADSK = False
import importlib
import math
import os
import sys
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import mast_params as P  # noqa: E402
P = importlib.reload(P)   # Fusion keeps modules loaded between runs: pick up edits

DRING_X = 150.0     # where the catch parts sit in the design, clear of the mast
ROD_Y = 120.0
ROLLER_DX = 50.0

if HAVE_ADSK:
    NEW_BODY = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation


def mm(v):
    return v / 10.0


def world_pt(x, y, z):
    return adsk.core.Point3D.create(mm(x), mm(y), mm(z))


def _sk_pt(sk, x, y, z):
    p = sk.modelToSketchSpace(world_pt(x, y, z))
    return adsk.core.Point3D.create(p.x, p.y, 0)


def offset_plane(comp, base, dist_mm, name=None):
    pi = comp.constructionPlanes.createInput()
    pi.setByOffset(base, adsk.core.ValueInput.createByReal(mm(dist_mm)))
    pl = comp.constructionPlanes.add(pi)
    if name:
        pl.name = name
    return pl


def path_profile(comp, plane, segs, name=None):
    """Closed loop from world points. segs: list of ('L', pt) lines to pt, or ('A', mid, pt) arcs
    through mid to pt; the loop starts at the last segment's end point. One profile."""
    sk = comp.sketches.add(plane)
    if name:
        sk.name = name
    lines, arcs = sk.sketchCurves.sketchLines, sk.sketchCurves.sketchArcs
    cur = _sk_pt(sk, *segs[-1][-1])
    for seg in segs:
        if seg[0] == "L":
            nxt = _sk_pt(sk, *seg[1])
            lines.addByTwoPoints(cur, nxt)
        else:
            mid, nxt = _sk_pt(sk, *seg[1]), _sk_pt(sk, *seg[2])
            arcs.addByThreePoints(cur, mid, nxt)
        cur = nxt
    return sk.profiles.item(0)


def rect_profile(comp, plane, c1, c2, name=None):
    sk = comp.sketches.add(plane)
    if name:
        sk.name = name
    sk.sketchCurves.sketchLines.addTwoPointRectangle(_sk_pt(sk, *c1), _sk_pt(sk, *c2))
    return sk.profiles.item(0)


def circle_profile(comp, plane, c, d, name=None):
    sk = comp.sketches.add(plane)
    if name:
        sk.name = name
    sk.sketchCurves.sketchCircles.addByCenterRadius(_sk_pt(sk, *c), mm(d / 2.0))
    return sk.profiles.item(0)


def polygon_profile(comp, plane, c, n, circumradius, name=None, rot=0.0):
    pts = [(c[0] + circumradius * math.cos(rot + 2 * math.pi * i / n), c[1] + circumradius * math.sin(rot + 2 * math.pi * i / n), c[2]) for i in range(n)]
    return path_profile(comp, plane, [("L", p) for p in pts], name)


def _finish(comp, e, op, target):
    if op != NEW_BODY and target is not None:
        e.participantBodies = [target]
    feat = comp.features.extrudeFeatures.add(e)
    return feat


def extrude(comp, profile, op, dist_mm, target=None):
    """One-sided, along the sketch plane's normal (negative = the other way)."""
    e = comp.features.extrudeFeatures.createInput(profile, op)
    e.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(dist_mm)))
    return _finish(comp, e, op, target)


def extrude_sym(comp, profile, op, full_mm, target=None):
    e = comp.features.extrudeFeatures.createInput(profile, op)
    e.setSymmetricExtent(adsk.core.ValueInput.createByReal(mm(full_mm)), True)
    return _finish(comp, e, op, target)


# ---------------------------------------------------------------------------- mast
def arc_mid(cx, cz, r, a0, a1):
    """Point on a circle midway between two angles (radians), for three-point arcs."""
    am = (a0 + a1) / 2.0
    return (cx + r * math.cos(am), cz + r * math.sin(am))


def build_mast(comp):
    """Modelled installed (base on XY, Z up, the arm along ARM_DIR * X in the frame's plane), then
    laid flat on its back with a Move so the design is print-ready."""
    xy, xz = comp.xYConstructionPlane, comp.xZConstructionPlane
    d = P.ARM_DIR
    x_out, x_in = -d * P.COL_X / 2, d * P.COL_X / 2
    x_tip = d * (P.ARM_X1 - P.PAD_R)
    # inside radius (concave) centre and the outside radius (convex) centre
    fx, fz = d * (P.COL_X / 2 + P.INNER_R), P.ARM_Z0 - P.INNER_R
    ox, oz = x_out + d * P.OUTER_R, P.ARM_TOP_Z - P.OUTER_R
    # angles as seen from each centre: the inside arc runs from the arm's underside (pointing up from the
    # centre) round to the column face (pointing toward the column); the outside arc from the column's
    # outer face (pointing away from the arm) over the top
    a_in0, a_in1 = math.pi / 2, (math.pi if d > 0 else 0.0)
    a_out0, a_out1 = (math.pi if d > 0 else 0.0), math.pi / 2
    im = arc_mid(fx, fz, P.INNER_R, a_in0, a_in1)
    om = arc_mid(ox, oz, P.OUTER_R, a_out0, a_out1)
    x_back = P.BACK_X
    side = [("A", (om[0], 0, om[1]), (x_out + d * P.OUTER_R, 0, P.ARM_TOP_Z)),   # from (x_out, top - R) over the outside radius
            ("L", (x_back, 0, P.ARM_TOP_Z)),
            ("L", (x_back, 0, P.ARM_Z0)),
            ("L", (fx, 0, P.ARM_Z0)),
            ("A", (im[0], 0, im[1]), (x_in, 0, fz)),                                # the inside radius
            ("L", (x_in, 0, 0.0)),
            ("L", (x_out, 0, 0.0)),
            ("L", (x_out, 0, P.ARM_TOP_Z - P.OUTER_R))]
    feat = extrude_sym(comp, path_profile(comp, xz, side, "Mast_Side"), NEW_BODY, P.COL_Y)
    mast = feat.bodies.item(0)
    mast.name = "Mast"
    # tip plate: a stadium from the arm's end to the tip, PAD_T thick on the -Y face (the bed face),
    # blended into the arm's edges at its back end, with a stadium slot through it
    xb0, xb1 = sorted([P.BACK_X, P.TIP_X])
    r = P.PAD_R
    zc = P.EYE_CZ
    plate = [("A", (xb1 + d * r, 0, zc), (xb1, 0, zc + r)) if d > 0 else ("A", (xb1 + r, 0, zc), (xb1, 0, zc + r)),
             ("L", (xb0, 0, zc + r)), ("A", (xb0 - r, 0, zc), (xb0, 0, zc - r)), ("L", (xb1, 0, zc - r))]
    extrude_sym(comp, path_profile(comp, xz, plate, "Tip_Plate"), JOIN, P.COL_Y, mast)
    for sz in (-1, 1):
        zl = P.EYE_CZ + sz * P.COL_Y / 2                       # the arm's edge line
        xf, zf = P.BACK_X - d * P.PAD_FILLET_DX, zl + sz * P.PAD_FILLET_R   # fillet circle centre
        dx, dz = P.BACK_X - xf, P.EYE_CZ - zf
        L = math.hypot(dx, dz)
        tpx, tpz = xf + dx / L * P.PAD_FILLET_R, zf + dz / L * P.PAD_FILLET_R
        xe = P.BACK_X - d * math.sqrt(P.PAD_R ** 2 - (P.COL_Y / 2) ** 2)
        fm = arc_mid(xf, zf, P.PAD_FILLET_R, math.atan2(zl - zf, 0.0), math.atan2(tpz - zf, tpx - xf))
        pm = arc_mid(P.BACK_X, P.EYE_CZ, P.PAD_R, math.atan2(tpz - P.EYE_CZ, tpx - P.BACK_X), math.atan2(zl - P.EYE_CZ, xe - P.BACK_X))
        fil = [("A", (fm[0], 0, fm[1]), (tpx, 0, tpz)), ("A", (pm[0], 0, pm[1]), (xe, 0, zl)), ("L", (xf, 0, zl))]
        extrude_sym(comp, path_profile(comp, xz, fil, "Plate_Fillet"), JOIN, P.COL_Y, mast)
    hr = P.HOLE_D / 2
    slot = [("A", (xb1 + hr, 0, zc), (xb1, 0, zc + hr)), ("L", (xb0, 0, zc + hr)), ("A", (xb0 - hr, 0, zc), (xb0, 0, zc - hr)), ("L", (xb1, 0, zc - hr))]
    extrude_sym(comp, path_profile(comp, xz, slot, "Slot"), CUT, 2 * P.COL_Y, mast)
    # the plate and its blends were made full thickness: trim them to PAD_T on the -Y face (the XY plane
    # is used so the direction is unambiguous: a box from Y = PAD_Y1 to +Y, beyond the arm's end)
    xt0, xt1 = sorted([P.BACK_X, P.TIP_X + d * (P.PAD_R + 1.0)])      # from the arm's end outward; the lobes behind it stay full thickness, merged into the arm
    trim_plane = offset_plane(comp, xy, zc - r - 1.0, "Trim_Plane")
    extrude(comp, rect_profile(comp, trim_plane, (xt0, P.PAD_Y1, zc - r - 1.0), (xt1, P.COL_Y / 2 + 1.0, zc - r - 1.0), "Plate_Trim"), CUT, 2 * r + 2.0, mast)
    # ONE foot: from the column's outer face out along the bar on the arm's side, semicircular far end,
    # a radius into the column on that side only, and the key under it
    r = P.BASE_END_R
    xr = P.BASE_X1 - d * r                                   # centre of the rounded end
    base = [("L", (xr, 0, 0.0)), ("A", (P.BASE_X1, 0, r), (xr, 0, P.BASE_T)), ("L", (P.BASE_X0, 0, P.BASE_T)), ("L", (P.BASE_X0, 0, 0.0))]
    extrude_sym(comp, path_profile(comp, xz, base, "Base"), JOIN, P.BASE_W, mast)
    x0 = d * P.COL_X / 2
    cx, cz = d * (P.COL_X / 2 + P.FOOT_R), P.BASE_T + P.FOOT_R
    m = arc_mid(cx, cz, P.FOOT_R, (math.pi if d > 0 else 0.0), -math.pi / 2)
    foot = [("L", (cx, 0, P.BASE_T)), ("A", (m[0], 0, m[1]), (x0, 0, cz)), ("L", (x0, 0, P.BASE_T))]
    extrude_sym(comp, path_profile(comp, xz, foot, "Foot_Radius"), JOIN, P.COL_Y, mast)
    extrude(comp, rect_profile(comp, xy, (P.KEY_X0, -P.KEY_W / 2, 0), (P.KEY_X1, P.KEY_W / 2, 0), "Key"), JOIN, -P.KEY_H, mast)
    # T-nut screws: through holes and counterbores
    cb_plane = offset_plane(comp, xy, P.BASE_T - 4.0, "Counterbore_Plane")
    for sx in P.SCREW_XS:
        extrude_sym(comp, circle_profile(comp, xy, (d * sx, 0, 0), P.M5_CLEAR, "Screw"), CUT, 2 * (P.BASE_T + P.KEY_H + 2), mast)
        extrude(comp, circle_profile(comp, cb_plane, (d * sx, 0, P.BASE_T - 4.0), P.M5_HEAD_D, "Counterbore"), CUT, 10.0, mast)
    lay_flat(comp, mast, P.COL_Y / 2)
    return mast


def lay_flat(comp, body, lift_mm):
    coll = adsk.core.ObjectCollection.create()
    coll.add(body)
    m = adsk.core.Matrix3D.create()
    m.setToRotation(math.pi / 2, adsk.core.Vector3D.create(1, 0, 0), adsk.core.Point3D.create(0, 0, 0))   # +90: the -Y face (the plate's face) goes down
    t = adsk.core.Matrix3D.create()
    t.translation = adsk.core.Vector3D.create(0, 0, mm(lift_mm))
    m.transformBy(t)
    mi = comp.features.moveFeatures.createInput2(coll)
    mi.defineAsFreeMove(m)
    return comp.features.moveFeatures.add(mi)


# ---------------------------------------------------------------------------- shackle
def build_dring(comp):
    """Modelled flat on the XY plane, print-ready: one HOOP_W-deep slab, pin axis along X at
    Z = HOOP_W/2, the arch toward +Y. The legs reach LEG_DROP below the axis (toward -Y) and are
    rounded about the pin axis, as is the tab's end. Build order: each JOIN touches what is there."""
    xy, yz = comp.xYConstructionPlane, comp.yZConstructionPlane
    X = DRING_X
    R, t, h = P.R_HOOP, P.HOOP_T / 2, P.HOOP_W
    zc = h / 2

    def half_round_cut(x0, width, y_edge, direction, name):
        """Cut, over x0..x0+width, the material beyond y_edge (direction +1: +Y side, -1: -Y side) that lies
        outside a cylinder of radius h/2 about the X axis at (y_edge, zc): leaves a half-round end."""
        yf = y_edge + direction * (h / 2 + 1.0)
        # profile on the YZ plane at x0: the rectangle y_edge..yf x 0..h minus the half-disc
        mid = (y_edge + direction * h / 2, zc)
        path = [("L", (x0, yf, 0.0)), ("L", (x0, yf, h)), ("L", (x0, y_edge, h)), ("A", (x0, mid[0], mid[1]), (x0, y_edge, 0.0))]
        extrude(comp, path_profile(comp, offset_plane(comp, yz, x0, name + "_Plane"), path, name), CUT, width, body)

    body = None
    for sx in (-1, 1):
        xl = X + sx * R - t
        f = extrude(comp, rect_profile(comp, xy, (xl, -P.LEG_DROP, 0), (xl + P.HOOP_T, P.LEG_H, 0), "Leg"), NEW_BODY if body is None else JOIN, h, body)
        if body is None:
            body = f.bodies.item(0)
            body.name = "DRing"
        half_round_cut(xl - 0.5, P.HOOP_T + 1.0, -P.LEG_DROP, -1, "Leg_End")
        if sx < 0:
            outer = [("A", (X, P.LEG_H + R + t, 0), (X + R + t, P.LEG_H, 0)), ("L", (X - R - t, P.LEG_H, 0))]
            extrude(comp, path_profile(comp, xy, outer, "Arch"), JOIN, h, body)
            inner = [("A", (X, P.LEG_H + R - t, 0), (X + R - t, P.LEG_H, 0)), ("L", (X - R + t, P.LEG_H, 0))]
            extrude(comp, path_profile(comp, xy, inner, "Arch_Inside"), CUT, h + 2, body)
    top = P.LEG_H + R + t
    ty = top + P.TAB_H
    tt = P.TAB_T / 2
    extrude(comp, rect_profile(comp, xy, (X - tt, top - 1, 0), (X + tt, ty + h / 2, 0), "Tab"), JOIN, h, body)
    half_round_cut(X - tt - 0.5, P.TAB_T + 1.0, ty, +1, "Tab_End")
    p_hole = offset_plane(comp, yz, X - tt - 1, "Tab_Hole_Plane")
    extrude(comp, circle_profile(comp, p_hole, (X - tt - 1, ty, zc), P.TAB_HOLE, "Tab_Hole"), CUT, P.TAB_T + 2, body)
    xh = X - R - t - 1
    extrude(comp, circle_profile(comp, offset_plane(comp, yz, xh, "Pin_Hole_Plane"), (xh, 0, zc), P.PIN_HOLE, "Pin_Holes"), CUT, 2 * (R + t) + 2, body)
    return body


# ---------------------------------------------------------------------------- snap pin and roller
def build_pin(comp):
    """Lying on its flat: axis along +X at Z = PIN_D/2 - PIN_FLAT, head at the -X end, slot vertical."""
    xy, yz = comp.xYConstructionPlane, comp.yZConstructionPlane
    x0, y0 = DRING_X - 40.0, ROD_Y
    zc = P.PIN_D / 2 - P.PIN_FLAT
    f = extrude(comp, circle_profile(comp, offset_plane(comp, yz, x0, "Pin_Head_Plane"), (x0, y0, zc), P.PIN_HEAD_D, "Pin_Head"), NEW_BODY, P.PIN_HEAD_T)
    pin = f.bodies.item(0)
    pin.name = "Pin"
    xs = x0 + P.PIN_HEAD_T
    extrude(comp, circle_profile(comp, offset_plane(comp, yz, xs, "Pin_Shank_Plane"), (xs, y0, zc), P.PIN_D, "Pin_Shank"), JOIN, P.PIN_L - P.PIN_HEAD_T, pin)
    xb = x0 + P.BARB_X0
    extrude(comp, circle_profile(comp, offset_plane(comp, yz, xb, "Barb_Plane"), (xb, y0, zc), P.BARB_D, "Barb"), JOIN, P.BARB_L, pin)
    # lead-in cone: a tapered extrude from the barb's far face down toward the shank
    xl = xb + P.BARB_L
    e = comp.features.extrudeFeatures.createInput(circle_profile(comp, offset_plane(comp, yz, xl, "Lead_Plane"), (xl, y0, zc), P.BARB_D, "Barb_Lead"), JOIN)
    e.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(P.BARB_LEAD)))
    e.taperAngle = adsk.core.ValueInput.createByReal(-math.atan((P.BARB_D / 2 - (P.PIN_D / 2 - 0.3)) / P.BARB_LEAD))
    e.participantBodies = [pin]
    comp.features.extrudeFeatures.add(e)
    # slot across the tip (vertical), and the flat along the underside
    xt = x0 + P.PIN_L
    extrude(comp, rect_profile(comp, xy, (xt - P.PIN_SLOT_L, y0 - P.PIN_SLOT_W / 2, 0), (xt + 1, y0 + P.PIN_SLOT_W / 2, 0), "Pin_Slot"), CUT, P.PIN_D + 2, pin)
    extrude(comp, rect_profile(comp, xy, (x0 - 1, y0 - P.PIN_HEAD_D, 0), (xt + 1, y0 + P.PIN_HEAD_D, 0), "Pin_Flat"), CUT, -P.PIN_HEAD_D, pin)
    return pin


def build_roller(comp):
    xy = comp.xYConstructionPlane
    c = (DRING_X + ROLLER_DX, ROD_Y, 0)
    f = extrude(comp, circle_profile(comp, xy, c, P.ROLLER_OD, "Roller"), NEW_BODY, P.ROLLER_L)
    roller = f.bodies.item(0)
    roller.name = "Roller"
    extrude(comp, circle_profile(comp, xy, c, P.ROLLER_BORE, "Roller_Bore"), CUT, P.ROLLER_L, roller)
    return roller


def summary():
    return ("Mast: one {:.0f} x {:.0f} foot on the arm's side, keyed into the 6 mm slot, 2 x M5; {:.0f} x {:.0f} column to {:.0f}, R{:.0f} inside / R{:.0f} outside, "
            "{:.0f} mm arm along the bar, {:.0f} x {:.0f} slot in the {:.0f} mm tip plate on the bed face. Laid flat: print as it sits.\n"
            "Shackle: one {:.0f} x {:.0f} band, {:.0f} clear inside for the {:.0f} x {:.0f} ribbon, O{:.1f} pin holes in half-round ends. Flat, print as it sits.\n"
            "Snap pin: O{:.0f} x {:.1f}, O{:.1f} barb, {:.0f} mm slot; lying on its flat. Roller O{:.0f} x {:.1f}, bore {:.1f}.\n"
            "Edit mast_params.py and run again; export each body as STL."
            ).format(P.BASE_L, P.BASE_W, P.COL_X, P.COL_Y, P.ARM_TOP_Z, P.INNER_R, P.OUTER_R, P.ARM_REACH, P.HOLE_D, P.HOLE_D + P.SLOT_STRAIGHT, P.PAD_T,
                     P.HOOP_T, P.HOOP_W, P.RING_IN, P.SLEEVE_W, P.SLEEVE_T, P.PIN_HOLE,
                     P.PIN_D, P.PIN_L, P.BARB_D, P.PIN_SLOT_L, P.ROLLER_OD, P.ROLLER_L, P.ROLLER_BORE)


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = app.activeProduct
        comp = design.rootComponent
        build_mast(comp)
        build_dring(comp)
        build_pin(comp)
        build_roller(comp)
        ui.messageBox(summary(), "Harness mast")
    except Exception:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
