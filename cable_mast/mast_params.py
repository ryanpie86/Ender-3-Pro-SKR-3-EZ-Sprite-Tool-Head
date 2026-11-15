"""Every number of the Ender 3 Pro harness mast and shackle, in mm, and the values derived from them.

Derived from the Kobra Max mast (ryanpie86/Kobra-Max-Improvements, parts/cable_mast): same shackle,
pin and roller; the mast is 295 tall, stands on ONE foot that reaches out on the arm's
side only, and bolts to the Ender's 2020 top bar with two M5 T-nuts.

Shared by cable_mast.py (manifold3d geometry, STLs, checks, renders) and
Fusion/HarnessMast/HarnessMast.py (the editable Fusion 360 model), so the two cannot drift.
No imports beyond the standard library: Fusion's Python loads this file too.
"""
import math

# ---- the only hardware -------------------------------------------------------
M5_CLEAR = 5.5
M5_HEAD_D = 9.0        # M5 button / cap head, counterbored
SLOT_W = 6.0           # the Ender's top bar: a 2020, standard 6 mm slot, M5 T-nuts
BAR_W = 20.0
BED = 400.0            # bed of the printer the mast is printed on: it is longer than the Ender's 235 when flat (needs >= 310)
Z_TRAVEL = 235.0       # the Ender's Z range: the loop's apex moves about half of it
CARABINER_BAR = 6.0    # the reel clip's wire/bar the hole must pass
E_PETG = 2000.0        # N/mm2, for the stiffness estimate

# ---- sleeve ------------------------------------------------------------------
SLEEVE_W = 25.0        # the harness sleeve is a flat ribbon: this wide (measured) ...
SLEEVE_T = 3.0         # ... and about this thick
SLEEVE_D = SLEEVE_T    # (kept for the mast docstrings)

# ---- mast (one piece, everything in the frame's plane, every corner a radius) ---
# ONE foot: the base plate runs from the column's outer face out along the bar on the arm's side only
# (the column's outer face goes straight down to the bar); its far end is a semicircle.
FOOT_LEN = 55.0        # from the column's inner face to the foot's far end, along the bar
BASE_W = BAR_W         # across the bar: no overhang off the 20 mm face
BASE_T = 8.0
BASE_END_R = BASE_T / 2   # the foot's far end is a full semicircle (in the frame's plane)
KEY_W = 5.8            # locating key into the slot
KEY_H = 1.5
SCREW_XS = (28.0, 52.0)   # 2 x M5 on the slot centreline, out along the foot (from the column centre), clear of the foot radius and the rounded end
COL_X = 20.0           # column section along the bar
COL_Y = 20.0           # column section across the bar (= the face width = the print thickness)
ARM_TOP_Z = 295.0      # top face of the arm above the bar (320 less an inch)
ARM_REACH = 75.0       # the arm's horizontal reach from the column's face, along the bar ("a few inches")
ARM_DIR = +1           # +1: the arm sweeps toward +X, to the right along the bar, staying in the frame's plane; the foot is on the same side
INNER_R = 40.0         # radius inside the column/arm corner
OUTER_R = 20.0         # radius outside the column/arm corner (was a chamfer; in a flat print a radius is free)
FOOT_R = 12.0          # concave radius where the column meets the foot (arm side only)
PAD_R = 15.0           # the arm's tip plate: a stadium of this half-height in the arm's plane, rounded at both ends
PAD_T = 10.0           # plate thickness across the bar, FLUSH WITH THE PRINT-BED FACE (not centred): thinner than the arm so a reel carabiner closes around it, and no support under it
PAD_FILLET_R = 5.0     # concave radii where the plate's back semicircle meets the arm's top and bottom edges
HOLE_D = 14.0          # the slot's width, axis across the bar (Y): two 6 mm carabiner bars side by side
SLOT_STRAIGHT = 30.0   # the slot's straight length back toward the column: a long U, so the clip has room to move; the plate is this much longer too
TIP_LOAD_N = 10.0      # pull at the hole for the deflection figures (two reels + a tug)

# ---- shackle: one uniform band with a snap-pin roller --------------------------
RING_IN = SLEEVE_W + 4.0      # clear width inside the shackle (between the legs): 2 mm each side of the ribbon
HOOP_T = 5.0                  # the band's width in the shackle's plane, the same everywhere: legs, arch, tab
HOOP_W = 14.0                 # the shackle's depth along the cable: one flat slab, prints flat; the pin holes live in this dimension
LEG_DROP = HOOP_W / 2         # the legs reach this far below the pin axis and end in a half-round of that radius (seen along the pin)
LEG_H = 8.0                   # straight legs above the pin axis: just past the roller, then the arch (the ribbon needs no more)
TAB_H = 10.0                  # split-ring tab above the arch, rounded end
TAB_T = HOOP_T                # the tab is as wide as the band (along the pin); its end is a half-round of HOOP_W/2 like the legs
TAB_HOLE = 5.0                # two 1 inch split rings (2 mm wire) side by side
PIN_D = 5.0                   # snap pin shank
PIN_HOLE = PIN_D + 0.8        # both legs: plain clearance holes (was +0.4: too tight as printed, 1 Nov)
PIN_HEAD_D = 10.0             # round head (a flat is cut on it, see PIN_FLAT)
PIN_HEAD_T = 3.0
BARB_D = PIN_HOLE + 0.6       # the barb ring that clicks through the far leg: 0.3 mm per side, whatever the hole
BARB_L = 1.5
BARB_LEAD = 1.2               # lead-in cone so it finds the hole
PIN_SLOT_W = 1.2              # slot across the tip: the two halves squeeze together to pass the hole
PIN_SLOT_L = 10.0             # finger length: longer = softer click, lower strain
PIN_FLAT = 0.4                # a flat along the whole pin so it prints lying down, slot vertical
ROLLER_OD = 12.0
RIBBON_CLEAR = 5.0            # headroom over the ribbon on the roller, to the arch
ROLLER_BORE = PIN_D + 1.0     # loose on the pin (was +0.6)
ROLLER_CLR = 0.5              # each end, to the legs (was 0.25)
E_PETG_STRAIN_OK = 0.02       # bending strain the snap fingers may see (PETG yields around 0.025)

# ---- derived -----------------------------------------------------------------
BASE_H = BASE_T
BASE_X0 = -ARM_DIR * COL_X / 2               # the base starts at the column's outer face ...
BASE_X1 = ARM_DIR * (COL_X / 2 + FOOT_LEN)   # ... and ends out along the bar on the arm's side
BASE_L = COL_X + FOOT_LEN                    # total length along the bar
KEY_X0, KEY_X1 = BASE_X0, BASE_X1 - ARM_DIR * BASE_END_R   # the key stops short of the rounded end
ARM_Z0 = ARM_TOP_Z - COL_Y                   # underside of the arm
ARM_X1 = COL_X / 2 + ARM_REACH               # far end of the arm (|X|)
TIP_X = ARM_DIR * (ARM_X1 - PAD_R)           # the plate's front semicircle centre; the arm's rounded tip is its far edge
BACK_X = TIP_X - ARM_DIR * SLOT_STRAIGHT     # the plate's back semicircle centre: the full-thickness arm ends here
HANG_X = (TIP_X + BACK_X) / 2                # where the reel is drawn hanging (anywhere along the slot in practice)
PAD_Y0 = -COL_Y / 2                          # the plate sits on the -Y face of the arm, which is the face that goes on the bed
PAD_Y1 = PAD_Y0 + PAD_T
EYE_CZ = ARM_Z0 + COL_Y / 2                  # hole centre: on the arm's centreline
REEL_EYE_Z = EYE_CZ - HOLE_D / 2             # a carabiner hangs from the bottom of the hole
EYE_IN = HOLE_D
COL_H = ARM_TOP_Z
# paddle fillets: a circle of PAD_FILLET_R tangent to the arm's edge line and to the paddle circle
PAD_FILLET_DX = math.sqrt((PAD_R + PAD_FILLET_R) ** 2 - (PAD_R - PAD_FILLET_R) ** 2)   # centre offset from the paddle centre, toward the column

ROLLER_L = RING_IN - 2 * ROLLER_CLR
EYE_L = HOOP_T                               # the pin passes through a leg's full width
EYE_X = RING_IN / 2 + HOOP_T / 2             # leg centrelines (and pin hole centres) at +-EYE_X
R_HOOP = EYE_X                               # arch mean radius: the band's centreline
D_HEIGHT = LEG_H + R_HOOP + HOOP_T / 2       # pin axis to the top of the arch
FAR_FACE = EYE_L + RING_IN + EYE_L           # from the near leg's outer face to the far leg's outer face
BARB_X0 = PIN_HEAD_T + FAR_FACE + 0.3        # barb starts just past the far face (from the head's outer face)
PIN_L = BARB_X0 + BARB_L + BARB_LEAD + 0.5   # head included
PIN_X0 = -EYE_X - HOOP_T / 2 - PIN_HEAD_T    # head's outer face, in the shackle's frame
# bending strain in a finger as the barb passes the hole: cantilever PIN_SLOT_L long, ~PIN_D/2 thick,
# tip deflection (BARB_D - PIN_HOLE)/2
PIN_FINGER_STRAIN = 3 * (PIN_D / 2) * ((BARB_D - PIN_HOLE) / 2) / (2 * PIN_SLOT_L ** 2)
