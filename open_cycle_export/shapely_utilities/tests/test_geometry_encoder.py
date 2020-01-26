import unittest

import json
import shapely.geometry

from open_cycle_export.shapely_utilities.geometry_encoder import GeometryEncoder


class TestGeometryEncoder(unittest.TestCase):
    """Test geometry encoder can be used with json dumps method"""

    def test_json_dumps_point(self):
        point = shapely.geometry.Point(0, 0)
        string = json.dumps({"point": point}, cls=GeometryEncoder)
        self.assertEqual(
            string, '{"point": {"type": "Point", "coordinates": [0.0, 0.0]}}'
        )
