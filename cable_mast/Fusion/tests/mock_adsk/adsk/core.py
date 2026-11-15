LOG = []
MESSAGES = []


class Point3D:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z

    @staticmethod
    def create(x, y, z):
        return Point3D(x, y, z)


class ValueInput:
    def __init__(self, v):
        self.value = v

    @staticmethod
    def createByReal(v):
        return ValueInput(v)


class _UI:
    def messageBox(self, text, *args):
        MESSAGES.append(text)


class Application:
    _instance = None

    def __init__(self):
        from . import fusion
        self.userInterface = _UI()
        self.activeProduct = fusion.Design()

    @staticmethod
    def get():
        if Application._instance is None:
            Application._instance = Application()
        return Application._instance


class Vector3D:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z

    @staticmethod
    def create(x, y, z):
        return Vector3D(x, y, z)


class Matrix3D:
    """Just enough to check the script composes a rotation and a translation."""
    def __init__(self):
        self.rotation, self.translation = None, Vector3D(0, 0, 0)

    @staticmethod
    def create():
        return Matrix3D()

    def setToRotation(self, angle, axis, origin):
        assert abs(angle) > 0 and (axis.x, axis.y, axis.z) != (0, 0, 0)
        self.rotation = (angle, (axis.x, axis.y, axis.z), (origin.x, origin.y, origin.z))
        return True

    def transformBy(self, other):
        self.translation = Vector3D(self.translation.x + other.translation.x,
                                    self.translation.y + other.translation.y,
                                    self.translation.z + other.translation.z)
        return True


class ObjectCollection:
    def __init__(self):
        self.items = []

    @staticmethod
    def create():
        return ObjectCollection()

    def add(self, item):
        self.items.append(item)
        return True

    @property
    def count(self):
        return len(self.items)


class Line3D:
    def __init__(self, p0, p1):
        self.startPoint, self.endPoint = p0, p1
        self.objectType = "adsk::core::Line3D"

    @staticmethod
    def classType():
        return "adsk::core::Line3D"


class Circle3D:
    def __init__(self, c, r):
        self.center, self.radius = c, r
        self.objectType = "adsk::core::Circle3D"

    @staticmethod
    def classType():
        return "adsk::core::Circle3D"
