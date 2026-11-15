from . import core

AXES = {"x": 0, "y": 1, "z": 2}


class FeatureOperations:
    NewBodyFeatureOperation = "NEW_BODY"
    JoinFeatureOperation = "JOIN"
    CutFeatureOperation = "CUT"


class _Origin:
    def __init__(self, axis, value):
        self.x = self.y = self.z = 0.0
        setattr(self, axis, value)


class _Geometry:
    def __init__(self, axis, value):
        self.origin = _Origin(axis, value)


class ConstructionPlane:
    def __init__(self, axis, value, name=""):
        self.axis, self.value, self.name = axis, value, name
        self.geometry = _Geometry(axis, value)
        self.deleted = False

    def deleteMe(self):
        self.deleted = True


class _PlaneInput:
    def setByOffset(self, base, vi):
        self.base, self.offset = base, vi.value


class ConstructionPlanes:
    def __init__(self):
        self.items = []

    def createInput(self):
        return _PlaneInput()

    def add(self, pi):
        pl = ConstructionPlane(pi.base.axis, pi.base.value + pi.offset)
        self.items.append(pl)
        return pl


class _Lines:
    def __init__(self, sk):
        self.sk = sk

    def addTwoPointRectangle(self, p1, p2):
        assert p1.x != p2.x and p1.y != p2.y, "degenerate rectangle in sketch %s" % self.sk.name
        self.sk.shapes.append(("rect", (p1.x, p1.y), (p2.x, p2.y)))

    def addByTwoPoints(self, p1, p2):
        assert (p1.x, p1.y) != (p2.x, p2.y), "zero-length line in sketch %s" % self.sk.name
        self.sk.shapes.append(("line", (p1.x, p1.y), (p2.x, p2.y)))


class _Circles:
    def __init__(self, sk):
        self.sk = sk

    def addByCenterRadius(self, c, r):
        assert r > 0, "non-positive radius in sketch %s" % self.sk.name
        self.sk.shapes.append(("circle", (c.x, c.y), r))


class _Curves:
    def __init__(self, sk):
        self.sketchLines = _Lines(sk)
        self.sketchCircles = _Circles(sk)


class _Profile:
    def __init__(self, sk):
        self.sketch = sk


class _Profiles:
    def __init__(self, sk):
        self.sk = sk

    def item(self, i):
        shapes = self.sk.shapes
        if all(s[0] == "line" for s in shapes):
            # a polygon: the lines must chain end to start and close, with no repeated vertex
            assert len(shapes) >= 3, "sketch %s: fewer than 3 lines" % self.sk.name
            for a, b in zip(shapes, shapes[1:] + shapes[:1]):
                assert a[2] == b[1], "sketch %s: lines do not chain into one closed profile" % self.sk.name
            starts = [s[1] for s in shapes]
            assert len(set(starts)) == len(starts), "sketch %s: polygon revisits a vertex" % self.sk.name
            return _Profile(self.sk)
        assert len(shapes) == 1, "sketch %s has %d shapes; one shape per sketch" % (self.sk.name, len(shapes))
        return _Profile(self.sk)


class Sketch:
    def __init__(self, plane):
        self.plane, self.name, self.shapes = plane, "", []
        self.sketchCurves = _Curves(self)
        self.profiles = _Profiles(self)

    def modelToSketchSpace(self, p):
        a = AXES[self.plane.axis]
        coords = [p.x, p.y, p.z]
        assert abs(coords[a] - self.plane.value) < 1e-6, (
            "point (%.3f, %.3f, %.3f) cm not on plane %s=%.3f cm for sketch '%s'"
            % (p.x, p.y, p.z, self.plane.axis, self.plane.value, self.name))
        rest = [c for i, c in enumerate(coords) if i != a]
        return core.Point3D(rest[0], rest[1], 0.0)


class Sketches:
    def __init__(self, comp):
        self.comp = comp

    def add(self, plane):
        assert not plane.deleted, "sketch on a deleted plane"
        sk = Sketch(plane)
        self.comp.sketch_list.append(sk)
        return sk


def _sketch_bbox(sk):
    xs, ys = [], []
    for shp in sk.shapes:
        if shp[0] == "circle":
            (cx, cy), r = shp[1], shp[2]
            xs += [cx - r, cx + r]; ys += [cy - r, cy + r]
        else:
            for (x, y) in shp[1:]:
                xs.append(x); ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


def _world_bbox(sk, extent):
    """World-space box (cm) of an extrude: sketch box on its plane, swept along the
    plane's axis. One-sided extrudes are assumed to go +axis (what the helpers do)."""
    a = AXES[sk.plane.axis]
    others = [i for i in range(3) if i != a]
    sx0, sy0, sx1, sy1 = _sketch_bbox(sk)
    lo, hi = [0.0] * 3, [0.0] * 3
    lo[others[0]], hi[others[0]] = sx0, sx1
    lo[others[1]], hi[others[1]] = sy0, sy1
    kind, d = extent
    if kind == "one":
        lo[a], hi[a] = sk.plane.value, sk.plane.value + d
    elif kind == "sym":
        lo[a], hi[a] = sk.plane.value - d, sk.plane.value + d
    else:
        lo[a], hi[a] = sk.plane.value - d / 2.0, sk.plane.value + d / 2.0
    return tuple(lo), tuple(hi)


def _boxes_touch(a, b, tol=1e-6):
    return all(a[0][i] <= b[1][i] + tol and b[0][i] <= a[1][i] + tol for i in range(3))


class _Edge:
    def __init__(self, geometry):
        self.geometry = geometry


class _Edges:
    def __init__(self, items):
        self.items = items

    @property
    def count(self):
        return len(self.items)

    def item(self, i):
        return self.items[i]


class BRepBody:
    def __init__(self, name):
        self.name = name
        self.features = []
        self.boxes = []          # world boxes of every solid added so far
        self.solids = []         # (sketch, extent) of every JOIN / NEW solid, for synthetic edges

    @property
    def edges(self):
        """Synthetic edges: the 12 lines of every rect extrude and the two circles of every
        circle extrude. Enough to check that a fillet's edge selection finds what it expects."""
        out = []
        for sk, extent in self.solids:
            a = AXES[sk.plane.axis]
            others = [i for i in range(3) if i != a]
            kind, d = extent
            if kind == "one":
                a0, a1 = sk.plane.value, sk.plane.value + d
            elif kind == "sym":
                a0, a1 = sk.plane.value - d, sk.plane.value + d
            else:
                a0, a1 = sk.plane.value - d / 2.0, sk.plane.value + d / 2.0
            for shp in sk.shapes:
                if shp[0] == "circle":
                    (cx, cy), r = shp[1], shp[2]
                    for av in (a0, a1):
                        c = [0.0] * 3
                        c[others[0]], c[others[1]], c[a] = cx, cy, av
                        out.append(_Edge(core.Circle3D(core.Point3D(*c), r)))
                elif shp[0] == "rect":
                    (x0, y0), (x1, y1) = shp[1], shp[2]
                    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
                    def P(u, v, av):
                        c = [0.0] * 3
                        c[others[0]], c[others[1]], c[a] = u, v, av
                        return core.Point3D(*c)
                    for av in (a0, a1):
                        for i in range(4):
                            out.append(_Edge(core.Line3D(P(*corners[i], av), P(*corners[(i + 1) % 4], av))))
                    for (u, v) in corners:
                        out.append(_Edge(core.Line3D(P(u, v, a0), P(u, v, a1))))
        return _Edges(out)


class _Bodies:
    def __init__(self, b):
        self.b = b

    def item(self, i):
        return self.b


class _ExtrudeInput:
    def __init__(self, profile, op):
        self.profile, self.op, self.extent = profile, op, None
        self.participantBodies = None

    def setDistanceExtent(self, sym, vi):
        self.extent = ("sym" if sym else "one", vi.value)

    def setSymmetricExtent(self, vi, full):
        self.extent = ("sym-full", vi.value)


class _Feature:
    def __init__(self, body):
        self.bodies = _Bodies(body)


class ExtrudeFeatures:
    def __init__(self, comp):
        self.comp = comp

    def createInput(self, profile, op):
        return _ExtrudeInput(profile, op)

    def add(self, e):
        assert e.extent is not None, "extrude without an extent (sketch %s)" % e.profile.sketch.name
        sk = e.profile.sketch
        bb = _world_bbox(sk, e.extent)
        if e.op == FeatureOperations.NewBodyFeatureOperation:
            body = BRepBody("body%d" % len(self.comp.bodies))
            self.comp.bodies.append(body)
            body.boxes.append(bb)
            body.solids.append((sk, e.extent))
        else:
            assert e.participantBodies and len(e.participantBodies) == 1, (
                "%s on sketch %s needs exactly one participant body" % (e.op, sk.name))
            body = e.participantBodies[0]
            if e.op == FeatureOperations.JoinFeatureOperation:
                # Fusion makes a JOIN that touches nothing into a NEW body, which later
                # moves/joins miss. Bounding-box contact is a cheap necessary condition.
                assert any(_boxes_touch(bb, prev) for prev in body.boxes), (
                    "JOIN from sketch '%s' touches nothing already in body %s: Fusion would make it a separate body "
                    "(build order?)" % (sk.name, body.name))
                body.boxes.append(bb)
                body.solids.append((sk, e.extent))
        body.features.append((sk.name, e.op, e.extent))
        core.LOG.append((e.profile.sketch.name, e.op, e.extent, body.name))
        return _Feature(body)


class _MoveInput:
    def __init__(self, coll, transform=None):
        self.coll, self.transform = coll, transform

    def defineAsFreeMove(self, m):
        self.transform = m
        return True


class MoveFeatures:
    def __init__(self, comp):
        self.comp = comp

    def createInput2(self, coll):
        assert coll.count >= 1, "move with no bodies"
        return _MoveInput(coll)

    def createInput(self, coll, m):
        assert coll.count >= 1, "move with no bodies"
        return _MoveInput(coll, m)

    def add(self, mi):
        m = mi.transform
        assert m is not None and m.rotation is not None, "move without a transform"
        for b in mi.coll.items:
            assert b in self.comp.bodies, "moving a body that is not in the component"
            b.features.append(("move", m.rotation, (m.translation.x, m.translation.y, m.translation.z)))
        core.LOG.append(("move", "rotate+translate", m.rotation, [b.name for b in mi.coll.items]))
        return _Feature(mi.coll.items[0])


class _EdgeSetInputs:
    def __init__(self, fi):
        self.fi = fi

    def addConstantRadiusEdgeSet(self, coll, r, tangent_chain):
        assert coll.count >= 1, "fillet with no edges"
        assert r.value > 0, "fillet radius must be positive"
        self.fi.sets.append((coll, r.value))
        return True


class _FilletInput:
    def __init__(self):
        self.sets = []
        self.edgeSetInputs = _EdgeSetInputs(self)

    def addConstantRadiusEdgeSet(self, coll, r, tangent_chain):   # deprecated API path
        return self.edgeSetInputs.addConstantRadiusEdgeSet(coll, r, tangent_chain)


class FilletFeatures:
    def __init__(self, comp):
        self.comp = comp

    def createInput(self):
        return _FilletInput()

    def add(self, fi):
        assert fi.sets, "fillet input without edge sets"
        n = sum(c.count for c, _ in fi.sets)
        core.LOG.append(("fillet", n, [r for _, r in fi.sets]))
        return _Feature(self.comp.bodies[0])


class _Features:
    def __init__(self, comp):
        self.extrudeFeatures = ExtrudeFeatures(comp)
        self.moveFeatures = MoveFeatures(comp)
        self.filletFeatures = FilletFeatures(comp)


class Component:
    def __init__(self):
        self.xYConstructionPlane = ConstructionPlane("z", 0.0, "XY")
        self.xZConstructionPlane = ConstructionPlane("y", 0.0, "XZ")
        self.yZConstructionPlane = ConstructionPlane("x", 0.0, "YZ")
        self.constructionPlanes = ConstructionPlanes()
        self.sketches = Sketches(self)
        self.features = _Features(self)
        self.bodies, self.sketch_list = [], []


class Design:
    def __init__(self):
        self.rootComponent = Component()

    @staticmethod
    def cast(x):
        return x
