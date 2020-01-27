import json

from open_cycle_export.shapely_utilities.geometry_encoder import GeometryEncoder


def pretty_geometry_print(name, obj):
    print(name, json.dumps(obj, cls=GeometryEncoder))
