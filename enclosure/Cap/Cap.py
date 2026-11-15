"""End cap for the left foot rail's front end - Fusion 360 script.

Builds one body, Cap: a plate over the 4040 rail's open end with four + shaped
pegs into the rail's corner cavities, plus a skirt that hangs down over the front of
the TPU foot so the foot cannot slide forward off the rail. With the key
filler (../KeyFiller) behind the foot and the enclosure's hanger bar behind
that, nothing on the rail can slide either way.

Modelled in print orientation: plate flat on the bed, pegs pointing up.
Frame: +X across the rail (from its outer face toward the inner face),
+Y up the plate (0 = bottom of the skirt, CAP_SKIRT = the rail's underside,
CAP_SKIRT + 40 = its top), +Z out of the plate (pegs).

Run like the other scripts (Scripts and Add-Ins > + > Script or add-in from
device > this FOLDER > Run) in a fresh design.
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
import SKR3EZ_Enclosure as ENC  # noqa: E402
ENC = importlib.reload(ENC)

RAIL_W = ENC.RAIL_W          # 40
PLATE_T = 3.0                # cap plate thickness
CAP_SKIRT = 10.0             # how far the plate hangs below the rail, over the foot's front face
BORE_XY = [(10.0, 10.0), (30.0, 10.0), (10.0, 30.0), (30.0, 30.0)]   # the 4040's four corner cavities, from its outer-bottom corner (Creality STEP)
# The cavities are not round: each is a + (cross) about 4 mm across. A round peg cannot enter one,
# so the pegs are crosses too. Fitted on the rail: 4.5 mm across was too tight, 4.0 seated
# loosely; 4.2 is the target. 1.5 mm arms confirmed.
PEG_SPAN = 4.2               # overall width of the cross, tip to tip
PEG_ARM = 1.5                # width of each bar
CAV_SPAN = 4.5               # fit-check model of the cavity (span and arm, with clearance)
CAV_ARM = 1.8
PEG_L = 8.0
PEG_TIP = 1.0                # lead-in: the last 1 mm is a smaller cross
PEG_TIP_SHRINK = 0.8         # span and arm both this much smaller at the tip


def layout():
    L = {}
    L["plate"] = (0.0, 0.0, RAIL_W, CAP_SKIRT + RAIL_W)                  # x0, y0, x1, y1 on the bed
    L["pegs"] = [(bx, CAP_SKIRT + by) for (bx, by) in BORE_XY]
    assert PEG_SPAN < CAV_SPAN and PEG_ARM < CAV_ARM
    return L


def summary(L):
    return ("Cap: {:.0f} x {:.0f} x {:.0f} plate, {:.0f} mm skirt over the foot, four + pegs {:.1f} across / {:.1f} arms x {:.0f} into the rail's corner cavities (print flat, pegs up)"
            ).format(RAIL_W, CAP_SKIRT + RAIL_W, PLATE_T, CAP_SKIRT, PEG_SPAN, PEG_ARM, PEG_L)


if HAVE_ADSK:
    NEW_BODY = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation


def build_cap(comp, L):
    xy = comp.xYConstructionPlane
    x0, y0, x1, y1 = L["plate"]
    cap = ENC.extrude_up(comp, ENC.rect_profile(comp, xy, (x0, y0, 0), (x1, y1, 0), "Cap_Plate"), NEW_BODY, PLATE_T)
    cap.name = "Cap"
    top = ENC.offset_plane(comp, xy, "z", PLATE_T, "PlateTop")
    tip = ENC.offset_plane(comp, xy, "z", PLATE_T + PEG_L - PEG_TIP, "PegTip")
    for i, (px, py) in enumerate(L["pegs"]):
        cross(comp, cap, top, PLATE_T, px, py, PEG_SPAN, PEG_ARM, PEG_L - PEG_TIP, "Peg_%d" % i)
        cross(comp, cap, tip, PLATE_T + PEG_L - PEG_TIP, px, py, PEG_SPAN - PEG_TIP_SHRINK, PEG_ARM - PEG_TIP_SHRINK, PEG_TIP, "PegTip_%d" % i)
    return cap


def cross(comp, body, plane, z, cx, cy, span, arm, length, name):
    """A + shaped peg: two bars span long and arm wide, crossing at (cx, cy), extruded up from z."""
    ENC.extrude_up(comp, ENC.rect_profile(comp, plane, (cx - span / 2, cy - arm / 2, z), (cx + span / 2, cy + arm / 2, z), name + "_H"), JOIN, length, body)
    ENC.extrude_up(comp, ENC.rect_profile(comp, plane, (cx - arm / 2, cy - span / 2, z), (cx + arm / 2, cy + span / 2, z), name + "_V"), JOIN, length, body)


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
        build_cap(design.rootComponent, L)
        ui.messageBox("Built cap\n\n" + summary(L))
    except Exception:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))


if __name__ == "__main__":
    print(summary(layout()))
