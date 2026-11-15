"""Minimal stub of the Fusion 360 `adsk` package, enough to execute the
enclosure script's run() outside Fusion and catch API misuse:
points off the sketch plane, extrudes without an extent, JOIN/CUT without a
single participant body, wrong-direction offset planes."""
from . import core, fusion, cam  # noqa: F401
