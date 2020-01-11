import unittest

from open_cycle_export.shapely_utilities.immutable_point import ImmutablePoint


class TestImmutablePoint(unittest.TestCase):
    """Test immutable point does not allow modification but still works like a standard shapely point"""

    def test_require_constructor_arguments(self):
        with self.assertRaises(TypeError):
            ImmutablePoint()  # pylint: disable=no-value-for-parameter

    def test_prevent_coord_change(self):
        point = ImmutablePoint(1, 1)
        with self.assertRaises(AttributeError):
            point.x = 2
        self.assertEqual(point.x, 1)

    def test_hash_same_when_same_coords(self):
        point_a_1 = ImmutablePoint(2, 2)
        point_a_2 = ImmutablePoint(2, 2)
        self.assertEqual(hash(point_a_1), hash(point_a_2))

    def test_distance_method_correct(self):
        point_a = ImmutablePoint(0, 0)
        point_b = ImmutablePoint(3, 4)
        distance = point_a.distance(point_b)
        self.assertEqual(distance, 5)
