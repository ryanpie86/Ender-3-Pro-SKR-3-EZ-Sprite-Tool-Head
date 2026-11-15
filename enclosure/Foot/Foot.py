"""Printed TPU foot for the Ender 3 Pro foot rails - Fusion 360 script.

Builds one body, Foot: a plain block that SLIDES onto the underside of a 4040
foot rail from the rail's end. Two keys shaped for the rail's V-slot (a neck
through the throat, a chamfered head behind the lips, no flare into the V,
like a full-length sliding nut) run the FULL length of the block and locate it in
the rail's two bottom slots; no bolts. The frame's weight presses the foot up
against the rail. Its height comes from the enclosure script: the enclosure
hangs entirely below the frame, so the feet must lift the frame by the
enclosure's height plus GROUND_CLEARANCE. Print four (two per rail) in TPU
(95A, 100 % infill) for vibration damping.

The body is modelled IN ITS PRINT ORIENTATION: lying on one end face with
the keys running straight up, so every layer is the same cross-section and
nothing overhangs. Export it and print it as it is.

Run it like the enclosure script (Scripts and Add-Ins > + > Script or add-in
from device > pick this FOLDER > Run), in a fresh design. ../generate_foot_stl.py
imports this file for the STL, fit checks and render.

Foot frame (print orientation): origin at the bottom-left corner of the end
face on the bed. +X across the rail (from its outer face toward the inner
face), +Y from the sole (Y = 0) up to the rail face (Y = FOOT_H) and on to the
key tops, +Z along the rail (the print's vertical), 0..FOOT_L. Installed, +Y
becomes "up" and +Z becomes "along the rail".
"""

try:
    import adsk.core, adsk.fusion, adsk.cam  # noqa: F401
    HAVE_ADSK = True
except ImportError:  # pragma: no cover
    HAVE_ADSK = False
import os
import sys
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "SKR3EZ_Enclosure"))
import importlib  # noqa: E402
import SKR3EZ_Enclosure as ENC  # noqa: E402  (the enclosure sets the height and the slot geometry)
ENC = importlib.reload(ENC)      # Fusion keeps modules loaded between runs: pick up edits to the enclosure script

RAIL_W = ENC.RAIL_W
SLOT_X = ENC.SLOT_X                     # slot centres from the rail's inner face
FOOT_W = ENC.FOOT_W                     # = rail width
FOOT_L = ENC.FOOT_L                     # along the rail = print height
KEY_W, KEY_H, KEY_CLR = ENC.KEY_W, ENC.KEY_H, ENC.KEY_CLR
key_profile = ENC.key_profile           # same V-slot key as the enclosure's hanger bar


def layout():
    L = {}
    E = ENC.layout()
    L["foot_h"] = E["foot_h"]           # sole -> rail face
    L["box_h"] = E["total_h"]
    # slots measured from the rail's inner face; the foot's +X runs from the outer face
    L["slot_x"] = [FOOT_W - sx for sx in SLOT_X]
    L["key_x"] = L["slot_x"]            # key centres across the foot
    L["key_y0"] = L["foot_h"]           # keys stand on the rail face (print frame: +Y)
    L["key_len"] = FOOT_L               # full length, end face to end face
    assert KEY_W > ENC.SLOT_THROAT_W + 1.0 and KEY_H < ENC.SLOT_DEPTH
    assert min(L["key_x"]) - KEY_W / 2.0 > 0 and max(L["key_x"]) + KEY_W / 2.0 < FOOT_W
    return L


def summary(L):
    return ("Foot: {:.0f} x {:.0f} x {:.0f} mm block (print 4 in TPU, as modelled: on its end, keys vertical). "
            "Lifts the frame so the {:.0f} mm enclosure clears the table by {:.0f} mm.\n"
            "V-slot keys at X = {:.0f} and {:.0f} run the full length and slide into the rail's bottom slots; no bolts"
            ).format(FOOT_W, FOOT_L, L["foot_h"], L["box_h"], ENC.GROUND_CLEARANCE, L["slot_x"][0], L["slot_x"][1])


if HAVE_ADSK:
    NEW_BODY = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation


def mm(v):
    return v / 10.0


def world_pt(x, y, z):
    return adsk.core.Point3D.create(mm(x), mm(y), mm(z))


def _sketch_pt(sk, x, y, z):
    p = sk.modelToSketchSpace(world_pt(x, y, z))
    return adsk.core.Point3D.create(p.x, p.y, 0)


def rect_profile(comp, plane, c1, c2, name=None):
    sk = comp.sketches.add(plane)
    if name:
        sk.name = name
    sk.sketchCurves.sketchLines.addTwoPointRectangle(_sketch_pt(sk, *c1), _sketch_pt(sk, *c2))
    return sk.profiles.item(0)


def poly_profile(comp, plane, pts, name=None):
    """Closed polygon from world points (all on `plane`); one profile."""
    sk = comp.sketches.add(plane)
    if name:
        sk.name = name
    lines = sk.sketchCurves.sketchLines
    sp = [_sketch_pt(sk, *p) for p in pts]
    for i in range(len(sp)):
        lines.addByTwoPoints(sp[i], sp[(i + 1) % len(sp)])
    return sk.profiles.item(0)


def _finish(comp, ext_in, op, target):
    if op != NEW_BODY and target is not None:
        ext_in.participantBodies = [target]
    feat = comp.features.extrudeFeatures.add(ext_in)
    return feat.bodies.item(0) if op == NEW_BODY else feat


def extrude_up(comp, profile, op, dist_mm, target=None):
    e = comp.features.extrudeFeatures.createInput(profile, op)
    e.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(dist_mm)))
    return _finish(comp, e, op, target)


def build_foot(comp, L):
    """Everything is one cross-section on the XY plane extruded FOOT_L up Z: the
    block, then each key polygon joined to it."""
    xy = comp.xYConstructionPlane
    H = L["foot_h"]
    foot = extrude_up(comp, rect_profile(comp, xy, (0, 0, 0), (FOOT_W, H, 0), "Foot_Section"), NEW_BODY, L["key_len"])
    foot.name = "Foot"
    for i, kx in enumerate(L["key_x"]):
        pts = [(kx + u, L["key_y0"] + v, 0.0) for (u, v) in key_profile()]
        extrude_up(comp, poly_profile(comp, xy, pts, "SlotKey_%d" % i), JOIN, L["key_len"], foot)
    return foot


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox("No active Fusion design. Open or create a design first.")
            return
        L = layout()
        build_foot(design.rootComponent, L)
        ui.messageBox("Built foot\n\n" + summary(L))
    except Exception:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))


if __name__ == "__main__":
    print(summary(layout()))
