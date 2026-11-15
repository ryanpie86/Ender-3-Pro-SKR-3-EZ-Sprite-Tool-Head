"""Key filler for the left foot rail - Fusion 360 script.

Builds one body, KeyFiller: a short length of the same two slot keys the
foot and the enclosure's hanger bar use, on a thin base, to fill the gap
between the TPU foot and the hanger bar's front end. With the end cap
(../Cap) in front of the foot, it locks the foot and the enclosure against
sliding along the rail. Measure the gap on the printer, set FILLER_L, run.

Modelled base-down (print it like that: the key heads overhang their
throats by 2.2 mm a side, which prints fine on a part this small). Frame:
+X across the rail (from its outer face toward the inner face), +Y along
the rail, +Z up; the base's top face (Z = BASE_T) touches the rail's
underside.
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

RAIL_W = ENC.RAIL_W
FILLER_L = 34.0              # measured on the printer: gap between the foot and the hanger bar with both on the rail
BASE_T = 3.0                 # base under the rail
KEY_FIT = 0.3                # the filler is a touch shorter than the gap so it drops in


def layout():
    L = {}
    L["length"] = FILLER_L - KEY_FIT
    assert L["length"] >= 1.0, "gap too small for a filler: raise FOOT_GAP in the enclosure script or skip the filler"
    L["key_x"] = [RAIL_W - sx for sx in ENC.SLOT_X]     # slot centres, from the rail's outer face
    L["key_z0"] = BASE_T
    return L


def summary(L):
    return ("KeyFiller: {:.1f} mm long ({:.1f} gap less {:.1f}), base {:.0f} x {:.0f}, two slot keys on top; print base down"
            ).format(L["length"], FILLER_L, KEY_FIT, RAIL_W, BASE_T)


if HAVE_ADSK:
    NEW_BODY = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation


def build_filler(comp, L):
    xy = comp.xYConstructionPlane
    xz = comp.xZConstructionPlane
    n = L["length"]
    body = ENC.extrude_up(comp, ENC.rect_profile(comp, xy, (0, 0, 0), (RAIL_W, n, 0), "Filler_Base"), NEW_BODY, BASE_T)
    body.name = "KeyFiller"
    mid = ENC.offset_plane(comp, xz, "y", n / 2.0, "KeyMid")
    for i, kx in enumerate(L["key_x"]):
        pts = [(kx + u, n / 2.0, BASE_T + v) for (u, v) in ENC.key_profile()]
        ENC.extrude_sym(comp, ENC.poly_profile(comp, mid, pts, "SlotKey_%d" % i), JOIN, n, body)
    return body


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
        build_filler(design.rootComponent, L)
        ui.messageBox("Built key filler\n\n" + summary(L))
    except Exception:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))


if __name__ == "__main__":
    print(summary(layout()))
