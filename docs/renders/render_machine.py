"""Whole-machine render: a simplified Ender 3 Pro frame with every printed part of this build in place.

    python3 docs/renders/render_machine.py docs/renders

The frame members are plain boxes at representative Ender 3 Pro positions; the printed parts are the real
geometry from enclosure/ and cable_mast/."""
import os, sys
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # repo root
sys.path.insert(0, R + "/enclosure"); sys.path.insert(0, R + "/enclosure/SKR3EZ_Enclosure"); sys.path.insert(0, R + "/enclosure/Foot")
sys.path.insert(0, R + "/enclosure/Cap"); sys.path.insert(0, R + "/enclosure/KeyFiller"); sys.path.insert(0, R + "/cable_mast")
import generate_stl as G
import generate_foot_stl as GF
import generate_cap_stl as GC
import generate_filler_stl as GK
import SKR3EZ_Enclosure as E
import Foot as FT
import KeyFiller as KF
import cable_mast as M
from manifold3d import Manifold
box, cyl_y, cyl_z, to_trimesh = G.box, G.cyl_y, G.cyl_z, G.to_trimesh
OUT = sys.argv[1] if len(sys.argv) > 1 else "."

L = E.layout()
base = G.build_base(L); lid = G.build_lid(L)
lid_on = G.lid_assembled(L, lid)
fr = G.frame_parts(L)
th = L["total_h"]                 # rail underside (frame bottom plane) in enclosure Z
y0, y1 = L["rail_y"]              # the left foot rail's extent along Y (front end .. back end)
foot_h = L["foot_h"]
# ---- frame stand-ins (dimensions representative of an Ender 3 Pro, not a CAD model)
right_rail = box(250, y0, th, 290, y1, th + 40)
right_feet = Manifold()
for (fy0, fy1) in L["feet_y"]:
    right_feet += box(250, fy0, th - foot_h, 290, fy1, th)
cy0, cy1 = L["cross_y"]
z_cross_top = th + 40
UP_H = 440.0
uprights = box(-40, cy0, z_cross_top, 0, cy0 + 20, z_cross_top + UP_H) + box(250, cy0, z_cross_top, 290, cy0 + 20, z_cross_top + UP_H)
z_bar = z_cross_top + UP_H
top_bar = box(-40, cy0, z_bar, 290, cy0 + 20, z_bar + 20)
# bed: 235 square plate over the Y rail, centred on it, carriage under it
yx0, yx1 = L["yrail_x"]; yz0 = L["yrail_z0"]
bed_cx = (yx0 + yx1) / 2; bed_cy = (y0 + y1) / 2 + 20
bed_z = yz0 + 40 + 28
bed = box(bed_cx - 117.5, bed_cy - 117.5, bed_z, bed_cx + 117.5, bed_cy + 117.5, bed_z + 4)
carriage = box(bed_cx - 80, bed_cy - 60, yz0 + 40, bed_cx + 80, bed_cy + 60, yz0 + 40 + 10)
# X gantry 2040 between the uprights, toolhead block on it
z_gantry = bed_z + 120
gantry = box(-40, cy0 - 20, z_gantry, 290, cy0, z_gantry + 40)
th_x = bed_cx
toolhead = box(th_x - 32, cy0 - 70, z_gantry - 40, th_x + 32, cy0 - 20, z_gantry + 60)
nozzle = cyl_z(th_x, cy0 - 45, z_gantry - 55, z_gantry - 40, 6)
# ---- printed parts: enclosure (box + lid), feet, filler, cap already placed by the enclosure modules
cap = GC.installed(GC.build_cap(GC.P.layout()), foot_h)                     # on the left rail's front end, foot frame: rail outer face X=0 -> enclosure X = -40 .. 0
cap = cap.translate([-40, y0, th - foot_h])                                      # foot frame: X 0..40 from the rail's outer face, Y 0 at the rail's front end, Z H = rail underside
# ---- cable mast on the top bar's top face, column near the left end, arm to the right
mast_x0 = -20.0                                                             # column centre along the bar (enclosure X)
mast_y = cy0 + 10.0                                                         # bar centre across
mast_z = z_bar + 20.0                                                       # bar top face
def place(m):
    return m.translate([mast_x0, mast_y, mast_z])
mast = place(M.build_mast())
drop = 120.0
z0 = M.catch_installed_z(drop)
shackle = place(M.build_dring_local().translate([M.HANG_X, 0, z0]))
catch = Manifold()
for _, m, _c in M.catch_parts_local():
    catch += place(m.translate([M.HANG_X, 0, z0]))
cord = place(cyl_z(M.HANG_X, 0, z0 + M.D_HEIGHT + M.TAB_H, M.REEL_EYE_Z - 40, 1.5))
reel = place(Manifold.cylinder(12, 19, 19, 48).rotate([-90, 0, 0]).translate([M.HANG_X, -6, M.REEL_EYE_Z - 26]))
# the Sprite's flat cable: from the toolhead's back up over the shackle's roller and down to the enclosure's rear notch (stylised polyline of boxes)
zc = mast_z + z0 + M.ROLLER_OD / 2
rx = mast_x0 + M.HANG_X
ribbon = box(rx - 12.5, mast_y - 40, zc, rx + 12.5, mast_y + 30, zc + 1.5)                                   # over the roller
ribbon += box(rx - 12.5, mast_y + 28.5, th + 40, rx + 12.5, mast_y + 30, zc)                                 # down behind the bar to the enclosure's rear notch
# from the toolhead's back, up and across to the shackle: a slanted ribbon as a thin extruded quad
import numpy as _np
from manifold3d import CrossSection as _CS
pts = [(th_x, z_gantry + 60), (rx - 12.5, zc), (rx + 12.5, zc), (th_x + 25, z_gantry + 60)]
area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
if area < 0: pts.reverse()
ribbon += Manifold.extrude(_CS([pts]), 1.5).rotate([90, 0, 0]).translate([0, mast_y - 40 + 1.5, 0])
# ---- colours
GREY, DGREY, BLUE, ORANGE, SAND, GOLD, RUST, BLACK = "#8a8a8a", "#5a5a5a", "#4a90d9", "#e07b39", "#e8e3d6", "#c9a227", "#d9822b", "#1f1f1f"
parts = [(to_trimesh(fr["foot_rail"]), GREY, 1), (to_trimesh(fr["feet"]), "#3a6fb0", 1), (to_trimesh(fr["cross_profile"]), GREY, 1), (to_trimesh(fr["y_rail"]), GREY, 1),
         (to_trimesh(right_rail), GREY, 1), (to_trimesh(right_feet), "#3a6fb0", 1), (to_trimesh(uprights), GREY, 1), (to_trimesh(top_bar), GREY, 1),
         (to_trimesh(bed), "#2b2b2b", 1), (to_trimesh(carriage), DGREY, 1), (to_trimesh(gantry), GREY, 1), (to_trimesh(toolhead), DGREY, 1), (to_trimesh(nozzle), GOLD, 1),
         (to_trimesh(base), BLUE, 1), (to_trimesh(lid_on), ORANGE, 1), (to_trimesh(cap), "#b03030", 1),
         (to_trimesh(mast), SAND, 1), (to_trimesh(shackle), SAND, 1), (to_trimesh(catch), RUST, 1), (to_trimesh(cord), "#222222", 1), (to_trimesh(reel), "#333333", 1), (to_trimesh(ribbon), BLACK, 0.85)]
cap_t = to_trimesh(cap); print("cap bounds", cap_t.bounds.round(1).tolist())

def view(name, parts, elev, azim, title):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    import numpy as np
    fig = plt.figure(figsize=(11, 10), dpi=140); ax = fig.add_subplot(111, projection="3d")
    for t, c, a in parts:
        try: t = t.subdivide_to_size(max_edge=8.0, max_iter=6)
        except ValueError: t = t.subdivide_to_size(max_edge=20.0, max_iter=6)
        light = np.array([0.4, -0.6, 0.7]); light /= np.linalg.norm(light)
        shade = 0.45 + 0.55 * np.clip(t.face_normals @ light, 0, 1)
        rgb = np.array(matplotlib.colors.to_rgb(c))
        ax.add_collection3d(Poly3DCollection(t.vertices[t.faces], facecolors=np.clip(shade[:, None] * rgb[None, :], 0, 1), edgecolors="none", alpha=a))
    allv = np.vstack([t.vertices for t, _, _ in parts]); lo, hi = allv.min(0), allv.max(0); ext = hi - lo
    ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2]); ax.set_box_aspect(tuple(ext / ext.max()))
    ax.view_init(elev=elev, azim=azim); ax.set_axis_off(); ax.set_title(title, fontsize=10)
    fig.tight_layout(); path = os.path.join(OUT, name); fig.savefig(path, facecolor="white", bbox_inches="tight"); plt.close(fig); return path
print("render", view("assembled-machine.png", parts, 20, -55,
      "The build on a simplified Ender 3 Pro frame: board enclosure (blue, orange lid) under the left foot rail, TPU feet (dark blue) on the rail ends,\nend cap (red), cable mast (sand) on the 2020 top bar with its reel and roller shackle carrying the Sprite's flat cable (black)"))
print("render", view("assembled-machine-front.png", parts, 2, -90,
      "From the front: the enclosure hangs below the frame plane on the feet; the mast stands at the left end of the top bar"))
print("render", view("assembled-machine-left.png", parts, 8, 180,
      "From the left: hanger bar keyed into the foot rail's bottom slots, foot and end cap at the rail's front end, cable down the back"))
