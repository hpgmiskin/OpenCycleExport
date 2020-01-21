import shapely.geometry


class ImmutablePoint(shapely.geometry.Point):
    """Shapely point which cannot be modified once created and provides a hash value to compare with other points"""

    def __init__(self, x, y):
        super(ImmutablePoint, self).__init__(x, y)

    def __setattr__(self, name, value):
        if name in ["x", "y", "coords"]:
            raise AttributeError("Immutable point coords cannot be modified")
        else:
            return super(ImmutablePoint, self).__setattr__(name, value)

    def __hash__(self):
        return hash(tuple(self.coords))

    def __repr__(self):
        return "({}, {})".format(self.x, self.y)
