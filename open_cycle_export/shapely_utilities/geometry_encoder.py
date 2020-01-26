import json

import shapely.geometry
import shapely.geometry.base


class GeometryEncoder(json.JSONEncoder):
    def default(self, obj):  # pylint: disable=method-hidden
        if isinstance(obj, shapely.geometry.base.BaseGeometry):
            return shapely.geometry.mapping(obj)
        return json.JSONEncoder.default(self, obj)
