"""SKR 3 EZ enclosure for the Ender 3 Pro - Fusion 360 script.

Builds two bodies in the active design's root component:
  * Enclosure_Base - a deep tray that hangs ENTIRELY BELOW the frame from two
                     rails: a hanger bar along its left side carries two
                     keys shaped for the V-slot (a neck through the throat,
                     a chamfered head behind the lips, no flare into the V)
                     that SLIDE into the left foot rail's bottom slots from
                     the rail's end (no bolts), and two slim brackets rising
                     off its right wall carry the same keys up into the
                     centre (Y) rail's bottom slot 33 mm higher. No bolts
                     anywhere: the box slides on from the rail ends.
                     Printed feet (../Foot) lift the frame to clear it. Board standoffs,
                     corner posts, a 40 mm fan standing in the front wall,
                     USB-B / micro-SD openings on the right wall
                     (toward the screen), a cable notch across the rear wall.
  * Enclosure_Lid  - solid plate with an inner lip and counterbored screw
                     bosses; nothing can fall in. Modelled in its print
                     orientation (plate down, lip up), laid out beside the base.

How to run (Fusion 360): File > New Design, then Utilities > Add-Ins >
Scripts and Add-Ins (Shift+S) > "+" > "Script or add-in from device" and pick
the FOLDER this file sits in (folder name must equal the file name). Select it
and Run. Run it in a fresh design every time; re-running stacks bodies.

Every dimension lives in the constants below (millimetres). ../generate_stl.py
imports this same file, so the printable STLs, the fit checks and the renders
always share one set of numbers. ../Foot/Foot.py reads BOX_DROP from here to
size the feet. Edit here, re-run both.

Enclosure frame (world): origin at the box's outer bottom-left-front corner.
  +X toward the printer's RIGHT (toward the screen), +Y toward the REAR,
  +Z up. The left wall's outer face is at X = 0, directly under the inner
  edge of the left 4040 foot rail; the hanger bar spans X = -40..0 under the
  rail. The frame's bottom plane (the rail's underside) is at Z = total_h,
  i.e. the top of the lid and of the hanger bar. The box sits BOX_Y_ON_RAIL
  behind the rail's front end; negative means it protrudes in front of the
  frame. The whole box stays IN FRONT of the 4040 cross brace (126 mm behind
  the rail's front end), which is why it protrudes: the left-front foot sits
  between the box and the brace.

Board orientation: the board is turned 90 degrees anticlockwise (seen from
above) so its USB-B / micro-SD edge faces the printer's RIGHT. That puts the
screw terminals on the FRONT (fan) side and the EZ driver row along the LEFT
(rail) wall. All cables enter through the rear notch and run forward along
the 20 mm side channels. b2e() is the only place this mapping lives.

Sources: BIGTREETECH "SKR 3 EZ V1.0-SIZE.pdf" (board, read from its vector
geometry), Creality's published Ender-3 CAD (Ender3.STEP) for the rail, the
EZ2209 height measured on the real parts.
"""

try:  # importable outside Fusion (generate_stl.py, mock harness, Foot script)
    import adsk.core, adsk.fusion, adsk.cam  # noqa: F401
    HAVE_ADSK = True
except ImportError:  # pragma: no cover
    HAVE_ADSK = False
import math
import traceback

# ---------------------------------------------------------------------------
# 1. Measured part dimensions
# ---------------------------------------------------------------------------
# SKR 3 EZ. Board coords: origin bottom-left, X right, Y up, with the five
# driver sockets along the TOP edge, screw terminals down the LEFT edge,
# USB / micro-SD / thermistors along the BOTTOM edge.
BOARD_W = 109.67
BOARD_D = 98.00
BOARD_T = 1.6
HOLE_DX = 101.85          # X distance between the two hole columns
HOLE_DY_RIGHT = 76.30     # Y distance between the two right-hand holes
HOLE_TL_RISE = 14.49      # top-left hole is this much HIGHER than top-right
HOLE_BL_DROP = 0.97       # bottom-left hole is this much LOWER than bottom-right
BOARD_HOLE_D = 3.2
HOLE_EDGE_X = 3.85        # hole centre to the left/right board edge (from the drawing's vector geometry)
HOLE_EDGE_Y_LEFT = 3.12   # left-column hole centre to the board's top/bottom edge
USB_BODY = (24.1, 36.1)   # USB-B receptacle span along the bottom edge (board X); protrudes 1.35 mm
SD_BODY = (43.2, 56.9)    # micro-SD socket span along the bottom edge; card protrudes 1.6 mm
DRIVER_H = 24.0           # measured: 25.54 mm from the PCB underside to the top of a seated EZ2209, minus the PCB
DRIVER_ROW_BOARD = (5.0, 62.0, 107.0, 92.0)       # x0, y0, x1, y1 of the EZ driver row on the board
MOTOR_SOCKETS_BOARD = (0.0, 92.0, 109.67, 98.0)   # motor / MFAN sockets along the board's top edge

# Ender 3 frame, from Creality's Ender3.STEP: the left foot rail is a 4040,
# 290 mm long, with two V-slots on its underside 10 and 30 mm from its inner
# face. The centre (Y) rail runs front-to-back 125 mm from that inner face,
# sitting in a notch on the 4040 cross profile so its underside is 33 mm
# above the foot rails' bottom plane; the cross profile itself spans the bay
# at mid-length. Nothing of the printer reaches below the frame's bottom plane.
RAIL_W = 40.0
RAIL_L = 290.0
SLOT_X = (10.0, 30.0)     # bottom-slot centres measured from the rail's inner face
# Creality V-slot profile, traced from a cross-section of the STEP (same on the
# 4040 and the 2040). From the rail's face inward: a 45-degree V 9.6 wide at the
# surface narrows to a 6.0 throat 1.8 in; behind that the cavity is 10.4 wide
# with straight walls to 3.8 in, then 45-degree chamfers close it to 6.0 wide
# at the 6.0 roof. A key that slides in has to be the same shape, not a T.
SLOT_V_W = 9.6            # V opening at the surface
SLOT_THROAT_W = 6.0       # narrowest point, where the V meets the lips' underside
SLOT_LIP = 1.8            # surface to the lips' underside
SLOT_CAVITY_W = 10.4      # cavity behind the lips
SLOT_CAVITY_STRAIGHT = 3.8   # cavity walls straight to this depth, then 45 deg to the roof
SLOT_DEPTH = 6.0          # roof


def slot_profile(below=0.0):
    """The slot void as a polygon (u across the slot, v into the rail from its face),
    counter-clockwise. `below` extends it past the face for clean boolean cuts."""
    a, t, c = SLOT_V_W / 2.0, SLOT_THROAT_W / 2.0, SLOT_CAVITY_W / 2.0
    return [(-a - below, -below), (a + below, -below), (t, SLOT_LIP), (c, SLOT_LIP), (c, SLOT_CAVITY_STRAIGHT),
            (t, SLOT_DEPTH), (-t, SLOT_DEPTH), (-c, SLOT_CAVITY_STRAIGHT), (-c, SLOT_LIP), (-t, SLOT_LIP)]
Y_RAIL_CENTER = 125.0     # from the left foot rail's inner face (= enclosure X)
Y_RAIL_W = 40.0           # confirmed on the printer: a 4040 with two bottom slots at +/-10 from centre (the original Ender 3 has a 2040 on edge, one slot: 20)
Y_RAIL_BOTTOM = 33.0      # Y rail underside above the foot rails' bottom plane (measured on the printer)
CROSS_FROM_FRONT = 125.1  # foot-rail front end -> cross profile front face (it is 40 deep)

# ---------------------------------------------------------------------------
# 2. Case parameters
# ---------------------------------------------------------------------------
WALL = 2.5
FLOOR = 2.5
LID_T = 2.5
LID_LIP_H = 2.0
LID_LIP_T = 1.6
LID_LIP_CLR = 0.3
INNER_H = 44.0            # floor top -> lid underside: a 40 mm fan stands in the front wall with room to spare
BOX_Y_ON_RAIL = -65.0     # box front 65 mm IN FRONT of the rail's front end; the box must end before the cross brace
FOOT_GAP = 2.0            # left-front foot sits this far behind the box (it cannot be at the rail end any more)
CLR_LEFT = 20.0           # board (driver) edge -> left wall: motor-cable channel
CLR_RIGHT = 4.0           # board (USB) edge -> right wall: the plug passes through the wall opening
CLR_FRONT = 32.0          # board (terminal) edge -> front wall: the fan's 10 mm plus 22 of wire room for the terminal leads (was 12: too tight)
CLR_REAR = 10.0           # board (EXP) edge -> rear wall: cable entry
STANDOFF_H = 5.0
STANDOFF_D = 7.0
STANDOFF_HOLE_D = 2.5     # M3 self-tapping
POST = 7.0                # corner post square for the lid screws
POST_HOLE_D = 2.5
POST_HOLE_DEPTH = 10.0
LID_SCREW_D = 3.4
LID_BOSS = 6.4
LID_BOSS_H = 3.0
LID_CBORE_D = 6.2         # M3 pan head sits nearly flush: the lid runs under the Y rail
LID_CBORE_DEPTH = 1.5
FAN = 40.0                # 40 x 40 x 10 fan standing inside the front wall, blowing in
FAN_T = 10.0
FAN_HOLE_D = 38.0
FAN_SCREW_PITCH = 32.0
FAN_SCREW_D = 3.4
FAN_Z_CENTER = 24.0       # fan centre above the floor's underside (fan spans 4..44, under the lid lip)
REAR_NOTCH_Z = 22.0       # rear cable notch from this height up to the top, open
REAR_NOTCH_MARGIN = 20.0  # rear wall kept at both ends of the notch
REAR_VENT_W = 2.5         # low intake slots in the rear wall
REAR_VENT_H = 12.0
REAR_VENT_PITCH = 8.0
REAR_VENT_COUNT = 13
BAR_T = 8.0               # hanger bar under the rail, flush with the lid top
# Slot keys: a straight neck of throat width standing off the mating face, then
# a head shaped like the cavity (straight walls, 45-degree chamfers to the roof)
# shrunk by KEY_CLR, like a full-length sliding nut. The key deliberately does
# NOT fill the V groove at the rail's face: a V flare there wedged on the first
# TPU test print, so only the throat locates it sideways and only the lips'
# underside carries it. The box slides onto the rail from its front end.
KEY_CLR = 0.4             # clearance to every slot face (0.3 was tight in TPU)
KEY_END_MARGIN = 0.0      # keys run the bar's full length, front face to back face


def key_profile(clr=None):
    """Key cross-section (u across, v up from the mating face), counter-clockwise:
    neck through the throat, head in the cavity, no flare into the V."""
    c = KEY_CLR if clr is None else clr
    t, w = SLOT_THROAT_W / 2.0 - c, SLOT_CAVITY_W / 2.0 - c
    v_lip, v_str, v_top = SLOT_LIP + c, SLOT_CAVITY_STRAIGHT, SLOT_DEPTH - c
    v_ch = v_top - (w - t)                                   # 45-degree chamfer from the wall to the top
    return [(-t, 0.0), (t, 0.0), (t, v_lip), (w, v_lip), (w, max(v_str, v_ch)), (t, v_top),
            (-t, v_top), (-w, max(v_str, v_ch)), (-w, v_lip), (-t, v_lip)]


KEY_W = SLOT_CAVITY_W - 2 * KEY_CLR      # widest point of a key (its head)
KEY_H = SLOT_DEPTH - KEY_CLR             # key height above the mating face
FOOT_W, FOOT_L = 40.0, 30.0   # printed foot footprint under each rail end (../Foot); 60 was far longer than needed
# Y-rail bracket: a strip under the Y rail carrying a slot key into the rail's
# outer bottom slot, standing on a full-length flange bonded to the right wall,
# with a root at each end and 45-degree webs from the roots to the strip. No
# bolts. The flange / deep roots / cove / standoff flares came from the Fusion
# iteration (stronger, prints better); the cosmetic edge rounds stay in Fusion.
COL_W = 15.0              # how far the bracket stands out from the right wall's outer face (must cover the key)
COL_ROOT = 25.0           # the flange runs this far down the wall (bonds it over the full length)
FLANGE_TOP_BELOW = 2.5    # flange top this far below the wall top
STRIP_H = 13.4            # strip under the key
ROOT_L = 18.0             # each root's length along Y
BAR_COVE_R = 8.0          # fillet under the hanger bar where it meets the left wall
STANDOFF_FILLET_R = 5.0   # flare at the foot of each board standoff
USB_PLUG_W, USB_PLUG_H = 19.0, 15.0    # opening for a USB-B plug's overmould
SD_SLOT_W, SD_SLOT_H = 18.0, 8.0
CUTOUT_BELOW_BOARD = 1.0
GROUND_CLEARANCE = 8.0    # box floor -> table, sets the printed feet height
# Print orientation of the base. The body is designed in the installed frame
# (above) and rotated into this orientation as the last feature; generate_stl.py
# writes the STL the same way.
#   "front": front (fan) wall on the bed (chosen). Keys and the bracket strip
#            stand vertical. The hanger bar is recessed 32 mm behind the box
#            front for the foot, so its front end starts 77 mm up in mid-air:
#            that one 40 x 8 face takes a small slicer support, then the bar
#            goes straight up.
#   "rear":  rear wall on the bed. Every mount starts on the bed; the fan wall
#            becomes the top face (a bridge) instead of the rear wall.
#   "floor": as designed, floor down.
PRINT_ORIENTATION = "front"
LID_GAP_X = 15.0


# ---------------------------------------------------------------------------
# 3. Derived layout. Everything downstream reads from this dict.
# ---------------------------------------------------------------------------
def layout():
    L = {}
    L["inner_x"] = CLR_LEFT + BOARD_D + CLR_RIGHT      # board turned: its 98 mm side runs across the bay
    L["inner_y"] = CLR_FRONT + BOARD_W + CLR_REAR      # its 109.67 mm side runs front-to-back
    ox = L["outer_x"] = L["inner_x"] + 2 * WALL
    oy = L["outer_y"] = L["inner_y"] + 2 * WALL
    L["wall_top"] = FLOOR + INNER_H
    L["total_h"] = L["wall_top"] + LID_T               # = the frame's bottom plane: lid top and bar top touch the rail
    L["box_drop"] = L["total_h"]                       # the whole box hangs below the frame
    L["foot_h"] = L["total_h"] + GROUND_CLEARANCE
    L["post_top"] = L["wall_top"] - max(LID_LIP_H, LID_BOSS_H)
    L["board_x0"] = WALL + CLR_LEFT
    L["board_y0"] = WALL + CLR_FRONT
    L["board_z0"] = FLOOR + STANDOFF_H
    L["board_top"] = L["board_z0"] + BOARD_T
    bx, by = L["board_x0"], L["board_y0"]

    def b2e(x, y):
        """Board coords (origin bottom-left, USB edge = bottom) -> enclosure XY.
        90 deg CCW: board +X -> enclosure +Y (rear), board +Y -> enclosure -X (left)."""
        return (bx + (BOARD_D - y), by + x)

    def b2e_rect(x0, y0, x1, y1):
        ax, ay = b2e(x0, y0)
        cx, cy = b2e(x1, y1)
        return (min(ax, cx), min(ay, cy), max(ax, cx), max(ay, cy))

    L["b2e"] = b2e
    L["pcb_rect"] = b2e_rect(0, 0, BOARD_W, BOARD_D)
    L["driver_rect"] = b2e_rect(*DRIVER_ROW_BOARD)
    L["motor_rect"] = b2e_rect(*MOTOR_SOCKETS_BOARD)

    # --- frame fit: the foot rail runs along Y above the hanger bar; feet sit under its ends;
    #     the cross profile crosses above the box; the Y rail runs along Y, 33 mm up ---
    L["rail_y"] = (-BOX_Y_ON_RAIL, -BOX_Y_ON_RAIL + RAIL_L)
    L["yrail_y"] = (L["rail_y"][0] - 20.0, L["rail_y"][1] + 20.0)   # the Y rail overhangs the foot rails 20 mm each end
    L["cross_y"] = (CROSS_FROM_FRONT - BOX_Y_ON_RAIL, CROSS_FROM_FRONT - BOX_Y_ON_RAIL + 40.0)
    assert oy <= L["cross_y"][0], "the box must end in front of the cross brace: protrude further (lower BOX_Y_ON_RAIL)"
    # feet at both rail ends; the left-front one slides on after the box, into the
    # recess in front of the hanger bar
    L["feet_y"] = [(L["rail_y"][0], L["rail_y"][0] + FOOT_L), (L["rail_y"][1] - FOOT_L, L["rail_y"][1])]
    # the hanger bar and its keys start BAR_RECESS behind the rail's front end, so the
    # left-front foot (FOOT_L long) slides onto the rail end after the box is on
    L["bar_y0"] = L["rail_y"][0] + FOOT_L + FOOT_GAP
    L["key_on_rail"] = (L["bar_y0"], oy)                # the keys are inside the rail over their whole length
    assert L["key_on_rail"][1] - L["key_on_rail"][0] >= 50.0, "too little key inside the rail"
    L["yrail_x"] = (Y_RAIL_CENTER - Y_RAIL_W / 2.0, Y_RAIL_CENTER + Y_RAIL_W / 2.0)
    L["yrail_z0"] = L["total_h"] + Y_RAIL_BOTTOM
    L["yrail_slots"] = [Y_RAIL_CENTER] if Y_RAIL_W < 30 else [Y_RAIL_CENTER - 10.0, Y_RAIL_CENTER + 10.0]
    assert ox < L["yrail_x"][1], "box must end under the Y rail so the columns can reach its far slot"

    # --- heights ---
    L["driver_top"] = L["board_top"] + DRIVER_H
    L["lid_bottom"] = L["wall_top"]
    assert L["driver_top"] + 3.0 <= L["lid_bottom"], "drivers too close to the lid"
    L["driver_lid_gap"] = L["lid_bottom"] - L["driver_top"]

    # --- board holes / standoffs ---
    hb = {
        "BL": (HOLE_EDGE_X, HOLE_EDGE_Y_LEFT),
        "TL": (HOLE_EDGE_X, BOARD_D - HOLE_EDGE_Y_LEFT),
        "BR": (HOLE_EDGE_X + HOLE_DX, HOLE_EDGE_Y_LEFT + HOLE_BL_DROP),
        "TR": (HOLE_EDGE_X + HOLE_DX, HOLE_EDGE_Y_LEFT + HOLE_BL_DROP + HOLE_DY_RIGHT),
    }
    assert abs((hb["TL"][1] - hb["TR"][1]) - HOLE_TL_RISE) < 1e-6
    L["holes_board"] = hb
    L["standoffs"] = {k: b2e(x, y) for k, (x, y) in hb.items()}

    # --- corner posts ---
    p = WALL + POST / 2.0
    L["posts"] = [(p, p), (ox - p, p), (p, oy - p), (ox - p, oy - p)]
    rx0, ry0, rx1, ry1 = L["pcb_rect"]
    for (px, py) in L["posts"]:   # posts live in the front/rear channels, never under the board
        assert px + POST / 2 <= rx0 or px - POST / 2 >= rx1 or py + POST / 2 <= ry0 or py - POST / 2 >= ry1, "post under the board"
    pc = WALL + POST + 0.5

    # --- fan in the front wall ---
    fx, fz = ox / 2.0, FAN_Z_CENTER
    L["fan_center"] = (fx, fz)
    assert fz - FAN / 2.0 >= FLOOR + 1.0 and fz + FAN / 2.0 <= L["wall_top"] - LID_LIP_H - 0.5, "fan does not fit the front wall"
    assert FAN_T + 1.0 <= CLR_FRONT, "fan too thick for the front channel"
    L["fan_screws"] = [(fx + sx, fz + sz) for sx in (-FAN_SCREW_PITCH / 2, FAN_SCREW_PITCH / 2)
                       for sz in (-FAN_SCREW_PITCH / 2, FAN_SCREW_PITCH / 2)]
    L["fan_block"] = (fx - FAN / 2, WALL, fz - FAN / 2, fx + FAN / 2, WALL + FAN_T, fz + FAN / 2)   # x0,y0,z0,x1,y1,z1

    # --- wall cutouts: (wall, u0, u1, z0, z1); u = X on front/back, Y on left/right ---
    zb = L["board_top"] - CUTOUT_BELOW_BOARD
    usb_c = (USB_BODY[0] + USB_BODY[1]) / 2.0
    sd_c = (SD_BODY[0] + SD_BODY[1]) / 2.0
    cut = [
        ("right", by + usb_c - USB_PLUG_W / 2, by + usb_c + USB_PLUG_W / 2, zb, zb + USB_PLUG_H),   # USB-B
        ("right", by + sd_c - SD_SLOT_W / 2, by + sd_c + SD_SLOT_W / 2, zb, zb + SD_SLOT_H),      # micro-SD
        # (no opening at the TFT / CAN / PS-ON / thermistor headers: nothing leaves the box there;
        #  the thermistor leads come in over the rear notch with everything else)
        ("back", REAR_NOTCH_MARGIN, ox - REAR_NOTCH_MARGIN, REAR_NOTCH_Z, L["wall_top"] + 1.0),  # everything comes in here
    ]
    clamped = []
    for (wall, u0, u1, z0, z1) in cut:
        lim = ox if wall in ("front", "back") else oy
        u0c, u1c = max(u0, pc), min(u1, lim - pc)
        assert u1c - u0c > 5.0, wall
        clamped.append((wall, u0c, u1c, z0, z1))
    L["cutouts"] = clamped
    vx0 = (ox - (REAR_VENT_COUNT - 1) * REAR_VENT_PITCH - REAR_VENT_W) / 2.0
    L["rear_vents"] = [(vx0 + i * REAR_VENT_PITCH, vx0 + i * REAR_VENT_PITCH + REAR_VENT_W,
                        FLOOR + 3.0, FLOOR + 3.0 + REAR_VENT_H) for i in range(REAR_VENT_COUNT)]
    for (x0, x1, z0, z1) in L["rear_vents"]:
        assert x0 > pc and x1 < ox - pc and z1 < REAR_NOTCH_Z - 1.0

    # --- mounting: hanger bar under the rail, ribs up into its bottom slots ---
    th = L["total_h"]
    L["bar_top"] = (-RAIL_W, 0.0, L["wall_top"], th)                  # x0, x1, z0, z1 ; over bar_y
    L["bar_low"] = (-RAIL_W, WALL, th - BAR_T, L["wall_top"])        # overlaps the left wall
    L["bar_y"] = (L["bar_y0"], oy)                                    # clipped: nothing of the mount in front of the rail
    assert BAR_T > LID_T + 2.0, "the bar must reach below the lid to overlap the wall"
    # slot keys on the bar: key_profile() stood on the bar's top (Z = th) at each slot centre, along key_y
    L["key_x"] = [-sx for sx in SLOT_X]
    L["key_z0"] = th
    L["key_y"] = (L["bar_y0"] + KEY_END_MARGIN, oy - KEY_END_MARGIN)
    assert KEY_W > SLOT_THROAT_W + 1.0, "key head no wider than the throat: nothing holds the box up"
    assert KEY_H < SLOT_DEPTH and 0.0 < KEY_CLR < 0.6

    # --- Y-rail bracket: strip + key along the full length, a root at each end, 45-degree webs ---
    slot = L["yrail_slots"][-1]
    cx0, cx1 = ox - WALL, ox + COL_W                    # roots overlap the right wall so the bodies fuse
    wt = L["wall_top"]
    yz0 = L["yrail_z0"]
    zs = yz0 - STRIP_H                                  # strip underside
    zr = wt - COL_ROOT                                  # flange underside
    zt = wt - FLANGE_TOP_BELOW                          # flange top = where the roots and webs start
    L["col_x"] = (cx0, cx1)
    L["col_top"] = yz0
    L["col_key_x"] = slot
    assert slot - KEY_W / 2.0 >= ox + 1.5 and slot + KEY_W / 2.0 <= cx1 - 1.5, "the key must sit on the strip with 1.5 mm each side"
    assert zs > wt + 5.0, "strip would meet the wall top: lower STRIP_H"
    # the strip is clipped flush with the Y rail's front end: nothing of the mount in front of the rail
    sy0 = max(0.0, L["yrail_y"][0])
    L["strip_y"] = (sy0, oy)
    # blocks (x0, x1, y0, y1, z0, z1) in BUILD ORDER: each must touch what is already there,
    # or Fusion makes it a separate body. The flange first (overlaps the wall along the full
    # length), then the roots (overlap the flange), then the strip (overlaps the roots by 1 mm).
    # Roots and strip start at the wall's outer face so they clear the lid's edge.
    # the flange's underside is chamfered at 45 degrees: zr at the wall, rising to zr + COL_W
    # at the outer face. (x, z) polygon over y = strip_y, built first so it bonds to the wall.
    assert zr + COL_W <= zt, "flange too shallow for a 45-degree underside: raise COL_ROOT"
    L["flange_poly"] = [(cx0, zr), (ox, zr), (cx1, zr + COL_W), (cx1, zt), (cx0, zt)]
    L["col_blocks"] = []
    for (y0, y1) in ((sy0, sy0 + ROOT_L), (oy - ROOT_L, oy)):
        L["col_blocks"].append((ox, cx1, y0, y1, zt - 1.0, zs + 1.0))
    L["col_blocks"].append((ox, cx1, sy0, oy, zs, yz0))
    # 45-degree webs from each root's inner face at the flange top up to the strip's underside,
    # (y, z) triangles over x = ox..cx1
    run = (zs + 1.0) - zt
    L["col_webs"] = [[(sy0 + ROOT_L, zt), (sy0 + ROOT_L, zs + 1.0), (sy0 + ROOT_L + run, zs + 1.0)],
                     [(oy - ROOT_L, zt), (oy - ROOT_L, zs + 1.0), (oy - ROOT_L - run, zs + 1.0)]]
    assert sy0 + ROOT_L + run < oy - ROOT_L - run, "webs overlap: the box is too short for ROOT_L / STRIP_H"
    assert zr > L["board_top"] + 2.0, "flange would reach the board's level on the outside; fine, but check the USB opening"
    L["columns"] = [(sy0, oy)]                          # key span on the bracket
    assert L["col_top"] > L["total_h"] + 5.0

    # --- lid (print orientation: plate on Z=0, lip rising). Solid. ---
    L["lid_x0"] = ox + LID_GAP_X
    L["base_zmax"] = L["col_top"] + KEY_H                 # tallest point of the base (bracket keys)
    lip_in = WALL + LID_LIP_CLR
    L["lip_outer"] = (lip_in, lip_in, ox - lip_in, oy - lip_in)
    L["lip_inner"] = (lip_in + LID_LIP_T, lip_in + LID_LIP_T, ox - lip_in - LID_LIP_T, oy - lip_in - LID_LIP_T)
    L["lid_screws"] = L["posts"]
    L["lid_bosses"] = [(px - LID_BOSS / 2.0, py - LID_BOSS / 2.0, px + LID_BOSS / 2.0, py + LID_BOSS / 2.0) for (px, py) in L["posts"]]
    assert WALL + POST / 2.0 - LID_BOSS / 2.0 >= lip_in - 1e-9
    return L


def summary(L):
    return ("Enclosure_Base: {:.1f} x {:.1f} x {:.1f} mm (walls {:.1f}), lid {:.1f} thick, hanger bar {:.0f} wide x {:.0f} thick\n"
            "Slides onto the left foot rail: V-slot keys at X = -{:.0f} and -{:.0f} ({:.1f} wide x {:.1f} tall, {:.1f} clearance), no bolts\n"
            "Y-rail bracket: {:.0f} mm strip with a full-length key up to the Y rail's slot at X = {:.0f}, roots at both ends, no bolts\n"
            "On the rail: box protrudes {:.0f} mm in front of the frame, ends {:.0f} mm before the cross brace; bar recessed {:.0f} mm for the front foot\n"
            "Board turned 90 deg: USB / SD on the RIGHT wall (screen side), terminals front, drivers along the left wall\n"
            "Fan: 40 mm in the FRONT wall at Z={:.0f}; all cables through the rear notch; lid solid\n"
            "Whole box below the frame: {:.1f} mm -> print feet {:.0f} mm tall (../Foot); driver->lid {:.1f}"
            ).format(L["outer_x"], L["outer_y"], L["wall_top"], WALL, LID_T, RAIL_W, BAR_T,
                     SLOT_X[0], SLOT_X[1], KEY_W, KEY_H, KEY_CLR,
                     COL_W, L["yrail_slots"][-1], -BOX_Y_ON_RAIL, L["cross_y"][0] - L["outer_y"], FOOT_L + FOOT_GAP,
                     L["fan_center"][1], L["box_drop"], L["foot_h"], L["driver_lid_gap"])


# ---------------------------------------------------------------------------
# Fusion helpers (fusion360-parametric-script template)
# ---------------------------------------------------------------------------
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


def circle_profile(comp, plane, center, dia, name=None):
    sk = comp.sketches.add(plane)
    if name:
        sk.name = name
    sk.sketchCurves.sketchCircles.addByCenterRadius(_sketch_pt(sk, *center), mm(dia / 2.0))
    return sk.profiles.item(0)


def _finish(comp, ext_in, op, target):
    if op != NEW_BODY and target is not None:
        ext_in.participantBodies = [target]
    feat = comp.features.extrudeFeatures.add(ext_in)
    return feat.bodies.item(0) if op == NEW_BODY else feat


def extrude_up(comp, profile, op, dist_mm, target=None):      # only on XY-parallel planes (+Z)
    e = comp.features.extrudeFeatures.createInput(profile, op)
    e.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(dist_mm)))
    return _finish(comp, e, op, target)


def extrude_sym(comp, profile, op, total_mm, target=None):    # total length centred on the sketch plane
    e = comp.features.extrudeFeatures.createInput(profile, op)
    try:
        e.setSymmetricExtent(adsk.core.ValueInput.createByReal(mm(total_mm)), True)
    except AttributeError:
        e.setDistanceExtent(True, adsk.core.ValueInput.createByReal(mm(total_mm / 2.0)))
    return _finish(comp, e, op, target)


def fillet_edges(comp, body, pick, radius_mm, name):
    """Constant-radius fillet on every edge of `body` for which pick(edge) is True.
    pick gets (kind, data): ('line', (p0, p1)) or ('circle', (center, radius)), all in mm."""
    coll = adsk.core.ObjectCollection.create()
    edges = body.edges
    for i in range(edges.count):
        e = edges.item(i)
        g = e.geometry
        t = g.objectType
        if t == adsk.core.Line3D.classType():
            p0, p1 = g.startPoint, g.endPoint
            hit = pick("line", ((p0.x * 10, p0.y * 10, p0.z * 10), (p1.x * 10, p1.y * 10, p1.z * 10)))
        elif t == adsk.core.Circle3D.classType():
            c = g.center
            hit = pick("circle", ((c.x * 10, c.y * 10, c.z * 10), g.radius * 10))
        else:
            hit = False
        if hit:
            coll.add(e)
    if coll.count == 0:
        raise RuntimeError("fillet '%s': no matching edges on %s" % (name, body.name))
    fillets = comp.features.filletFeatures
    fi = fillets.createInput()
    r = adsk.core.ValueInput.createByReal(mm(radius_mm))
    try:
        fi.edgeSetInputs.addConstantRadiusEdgeSet(coll, r, False)
    except AttributeError:      # older API
        fi.addConstantRadiusEdgeSet(coll, r, False)
    feat = fillets.add(fi)
    feat.name = name
    return feat


def near(a, b, tol=0.05):
    return abs(a - b) <= tol


def offset_plane(comp, base_plane, axis, offset_mm, name=None):
    planes = comp.constructionPlanes
    for sign in (1, -1):
        pi = planes.createInput()
        pi.setByOffset(base_plane, adsk.core.ValueInput.createByReal(mm(sign * offset_mm)))
        pl = planes.add(pi)
        if abs(getattr(pl.geometry.origin, axis) * 10.0 - offset_mm) < 1e-3:
            if name:
                pl.name = name
            return pl
        pl.deleteMe()
    raise RuntimeError("Could not place plane at {}={} mm".format(axis, offset_mm))


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------
def build_base(comp, L):
    ox, oy = L["outer_x"], L["outer_y"]
    xy = comp.xYConstructionPlane
    xz = comp.xZConstructionPlane          # world Y = 0, front wall
    yz = comp.yZConstructionPlane          # world X = 0, left wall
    floor_top = offset_plane(comp, xy, "z", FLOOR, "FloorTop")
    back_pl = offset_plane(comp, xz, "y", oy, "BackWall")
    right_pl = offset_plane(comp, yz, "x", ox, "RightWall")
    bar_bottom_pl = offset_plane(comp, xy, "z", L["total_h"] - BAR_T, "BarBottom")   # (bar's lower block)
    bar_top_pl = offset_plane(comp, xy, "z", L["total_h"], "BarTop")
    posthole_pl = offset_plane(comp, xy, "z", L["post_top"] - POST_HOLE_DEPTH, "PostHoleBottom")

    base = extrude_up(comp, rect_profile(comp, xy, (0, 0, 0), (ox, oy, 0), "Base_Outline"), NEW_BODY, L["wall_top"])
    base.name = "Enclosure_Base"
    extrude_up(comp, rect_profile(comp, floor_top, (WALL, WALL, FLOOR), (ox - WALL, oy - WALL, FLOOR), "Cavity"),
               CUT, L["wall_top"] - FLOOR, base)

    h = POST / 2.0
    for i, (px, py) in enumerate(L["posts"]):
        extrude_up(comp, rect_profile(comp, floor_top, (px - h, py - h, FLOOR), (px + h, py + h, FLOOR), "Post_%d" % i),
                   JOIN, L["post_top"] - FLOOR, base)
        extrude_up(comp, circle_profile(comp, posthole_pl, (px, py, L["post_top"] - POST_HOLE_DEPTH), POST_HOLE_D, "PostHole_%d" % i),
                   CUT, POST_HOLE_DEPTH + 1.0, base)
    for k, (sx, sy) in L["standoffs"].items():
        extrude_up(comp, circle_profile(comp, floor_top, (sx, sy, FLOOR), STANDOFF_D, "Standoff_" + k), JOIN, STANDOFF_H, base)
        extrude_up(comp, circle_profile(comp, xy, (sx, sy, 0), STANDOFF_HOLE_D, "StandoffHole_" + k), CUT, FLOOR + STANDOFF_H + 1.0, base)

    # fan opening and screw holes through the front wall (XZ plane, world Y = 0)
    fx, fz = L["fan_center"]
    extrude_sym(comp, circle_profile(comp, xz, (fx, 0.0, fz), FAN_HOLE_D, "FanHole"), CUT, 2 * (WALL + 1.0), base)
    for i, (sx, sz) in enumerate(L["fan_screws"]):
        extrude_sym(comp, circle_profile(comp, xz, (sx, 0.0, sz), FAN_SCREW_D, "FanScrew_%d" % i), CUT, 2 * (WALL + 1.0), base)

    planes = {"front": xz, "back": back_pl, "left": yz, "right": right_pl}
    for i, (wall, u0, u1, z0, z1) in enumerate(L["cutouts"]):
        if wall in ("front", "back"):
            y = 0.0 if wall == "front" else oy
            c1, c2 = (u0, y, z0), (u1, y, z1)
        else:
            x = 0.0 if wall == "left" else ox
            c1, c2 = (x, u0, z0), (x, u1, z1)
        extrude_sym(comp, rect_profile(comp, planes[wall], c1, c2, "Cutout_%s_%d" % (wall, i)), CUT, 2 * (WALL + 1.0), base)
    for i, (x0, x1, z0, z1) in enumerate(L["rear_vents"]):
        extrude_sym(comp, rect_profile(comp, back_pl, (x0, oy, z0), (x1, oy, z1), "RearVent_%d" % i), CUT, 2 * (WALL + 1.0), base)

    # hanger bar under the rail: a lower block overlapping the left wall and a top
    # block flush with the lid top, then the V-slot keys on top
    by0, by1 = L["bar_y"]
    x0, x1, z0, z1 = L["bar_low"]
    extrude_up(comp, rect_profile(comp, bar_bottom_pl, (x0, by0, z0), (x1, by1, z0), "BarLow"), JOIN, z1 - z0, base)
    x0, x1, z0, z1 = L["bar_top"]
    extrude_up(comp, rect_profile(comp, offset_plane(comp, xy, "z", z0, "WallTop"), (x0, by0, z0), (x1, by1, z0), "BarTop"), JOIN, z1 - z0, base)
    ky0, ky1 = L["key_y"]
    kym = (ky0 + ky1) / 2.0
    key_pl = offset_plane(comp, xz, "y", kym, "KeyMid")      # sketch across the slot, extrude both ways along it
    for i, kx in enumerate(L["key_x"]):
        pts = [(kx + u, kym, L["key_z0"] + v) for (u, v) in key_profile()]
        extrude_sym(comp, poly_profile(comp, key_pl, pts, "SlotKey_%d" % i), JOIN, ky1 - ky0, base)

    # Y-rail bracket: chamfered flange along the wall, roots and strip as blocks, 45-degree webs,
    # then the slot key along the strip
    ct = L["col_top"]
    kx = L["col_key_x"]
    fy0, fy1 = L["strip_y"]
    fym = (fy0 + fy1) / 2.0
    flange_pl = offset_plane(comp, xz, "y", fym, "FlangeMid")
    extrude_sym(comp, poly_profile(comp, flange_pl, [(x, fym, z) for (x, z) in L["flange_poly"]], "Flange"), JOIN, fy1 - fy0, base)
    for j, (bx0, bx1, by0, by1, bz0, bz1) in enumerate(L["col_blocks"]):
        pl = offset_plane(comp, xy, "z", bz0, "BracketLevel_%d" % j)
        extrude_up(comp, rect_profile(comp, pl, (bx0, by0, bz0), (bx1, by1, bz0), "Bracket_%d" % j), JOIN, bz1 - bz0, base)
    xm = (ox + L["col_x"][1]) / 2.0
    web_pl = offset_plane(comp, yz, "x", xm, "BracketWebMid")
    for j, tri in enumerate(L["col_webs"]):
        pts = [(xm, y, z) for (y, z) in tri]
        extrude_sym(comp, poly_profile(comp, web_pl, pts, "BracketWeb_%d" % j), JOIN, COL_W, base)
    for i, (y0, y1) in enumerate(L["columns"]):
        kym = (y0 + y1) / 2.0
        kpl = offset_plane(comp, xz, "y", kym, "BracketKeyMid_%d" % i)
        pts = [(kx + u, kym, ct + v) for (u, v) in key_profile()]
        extrude_sym(comp, poly_profile(comp, kpl, pts, "BracketKey_%d" % i), JOIN, y1 - y0, base)

    # cove under the hanger bar along the left wall: a block in the corner, then a cylinder
    # cut tangent to the wall face and the bar's underside leaves the concave quarter round
    by0, by1 = L["bar_y"]
    z_bar = L["total_h"] - BAR_T
    r = BAR_COVE_R
    cove_pl = offset_plane(comp, xy, "z", z_bar - r, "CoveBottom")
    extrude_up(comp, rect_profile(comp, cove_pl, (-r, by0, z_bar - r), (0.0, by1, z_bar - r), "BarCoveBlock"), JOIN, r, base)
    cym = (by0 + by1) / 2.0
    cove_cut_pl = offset_plane(comp, xz, "y", cym, "CoveMid")
    extrude_sym(comp, circle_profile(comp, cove_cut_pl, (-r, cym, z_bar - r), 2 * r, "BarCoveCut"), CUT, (by1 - by0) + 2.0, base)
    # flares at the standoff feet: a real fillet on each standoff's bottom edge
    fillet_edges(comp, base,
                 lambda kind, d: kind == "circle" and near(d[1], STANDOFF_D / 2.0) and near(d[0][2], FLOOR),
                 STANDOFF_FILLET_R, "StandoffFlares")
    return base


def build_lid(comp, L):
    ox, oy = L["outer_x"], L["outer_y"]
    dx = L["lid_x0"]
    xy = comp.xYConstructionPlane
    plate_top = offset_plane(comp, xy, "z", LID_T, "LidPlateTop")
    lid = extrude_up(comp, rect_profile(comp, xy, (dx, 0, 0), (dx + ox, oy, 0), "Lid_Outline"), NEW_BODY, LID_T)
    lid.name = "Enclosure_Lid"
    lo, li = L["lip_outer"], L["lip_inner"]
    bars = [((lo[0], lo[1]), (lo[2], li[1])), ((lo[0], li[3]), (lo[2], lo[3])),
            ((lo[0], lo[1]), (li[0], lo[3])), ((li[2], lo[1]), (lo[2], lo[3]))]
    for i, ((x0, y0), (x1, y1)) in enumerate(bars):
        extrude_up(comp, rect_profile(comp, plate_top, (dx + x0, y0, LID_T), (dx + x1, y1, LID_T), "LipBar_%d" % i), JOIN, LID_LIP_H, lid)
    for i, (x0, y0, x1, y1) in enumerate(L["lid_bosses"]):
        extrude_up(comp, rect_profile(comp, plate_top, (dx + x0, y0, LID_T), (dx + x1, y1, LID_T), "LidBoss_%d" % i), JOIN, LID_BOSS_H, lid)
    for i, (px, py) in enumerate(L["lid_screws"]):
        extrude_up(comp, circle_profile(comp, xy, (dx + px, py, 0), LID_SCREW_D, "LidScrew_%d" % i), CUT, LID_T + LID_BOSS_H + 1.0, lid)
        extrude_up(comp, circle_profile(comp, xy, (dx + px, py, 0), LID_CBORE_D, "LidCbore_%d" % i), CUT, LID_CBORE_DEPTH, lid)
    return lid


def print_transform(L):
    """(angle about X in degrees, translation (x, y, z) in mm) that stands the designed
    base in PRINT_ORIENTATION with nothing below Z = 0. None for 'floor'."""
    if PRINT_ORIENTATION == "front":      # +Y up: (x, y, z) -> (x, -z, y), then lift
        return (90.0, (0.0, L["base_zmax"], 0.0))
    if PRINT_ORIENTATION == "rear":       # -Y up: (x, y, z) -> (x, z, -y), then shift so the rear wall is at Z = 0
        return (-90.0, (0.0, 0.0, L["outer_y"]))
    return None


def stand_for_print(comp, body, L):
    """Rotate the finished base into print orientation as the last feature. The
    design frame is unchanged for everything else (fit checks, the lid, the feet)."""
    tr = print_transform(L)
    if tr is None:
        return None
    angle, (tx, ty, tz) = tr
    m = adsk.core.Matrix3D.create()
    m.setToRotation(math.radians(angle), adsk.core.Vector3D.create(1, 0, 0), adsk.core.Point3D.create(0, 0, 0))
    lift = adsk.core.Matrix3D.create()
    lift.translation = adsk.core.Vector3D.create(mm(tx), mm(ty), mm(tz))
    m.transformBy(lift)
    coll = adsk.core.ObjectCollection.create()
    coll.add(body)
    mf = comp.features.moveFeatures
    try:
        mi = mf.createInput2(coll)
        mi.defineAsFreeMove(m)
    except AttributeError:      # older API
        mi = mf.createInput(coll, m)
    feat = mf.add(mi)
    feat.name = "Base_PrintOrientation"
    return feat


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox("No active Fusion design. Open or create a design first.")
            return
        comp = design.rootComponent
        L = layout()
        base = build_base(comp, L)
        build_lid(comp, L)
        stand_for_print(comp, base, L)
        ui.messageBox("Built SKR 3 EZ enclosure\n\n" + summary(L)
                      + "\nBase print orientation: " + {"front": "stood on its front (fan) wall", "rear": "stood on its rear wall",
                                                         "floor": "as designed, floor down"}[PRINT_ORIENTATION])
    except Exception:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))


if __name__ == "__main__":
    print(summary(layout()))
