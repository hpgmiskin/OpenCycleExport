import unittest

from shapely.geometry import LineString

from open_cycle_export.shapely_utilities.immutable_point import ImmutablePoint
from open_cycle_export.route_processor.way_processor import (
    waypoint_connection_storage,
    process_ways,
)


class TestWaypointConnectionStorage(unittest.TestCase):
    """Test waypoint connections can be stored and retrieved"""

    def test_single_index_storage(self):
        store, retrieve = waypoint_connection_storage()
        point_a_1 = ImmutablePoint(0, 0)
        point_a_2 = ImmutablePoint(0, 0)
        point_b_1 = ImmutablePoint(1, 1)
        point_b_2 = ImmutablePoint(1, 1)
        store(point_a_1, point_b_1, 1)
        store(point_a_2, point_b_2, 2)
        connections = retrieve(ImmutablePoint(0, 0), ImmutablePoint(1, 1))
        self.assertListEqual(connections, [1, 2])


class TestWayProcessor(unittest.TestCase):
    """Test ways can be converted to line segments and cost matrix"""

    def test_single_way(self):
        "Should create basic cost matrix for a single way"

        ways = [LineString([(0, 0), (3, 4)])]
        forward_coefficients = [1]
        reverse_coefficients = [10]
        unconnected_coefficient = 100

        waypoints, waypoint_connections, cost_matrix = process_ways(
            ways, forward_coefficients, reverse_coefficients, unconnected_coefficient
        )

        self.assertEqual(waypoints[0], ImmutablePoint(0, 0))
        self.assertEqual(waypoints[1], ImmutablePoint(3, 4))

        self.assertIsNone(waypoint_connections[0][0])
        self.assertEqual(waypoint_connections[0][1], LineString([(0, 0), (3, 4)]))
        self.assertEqual(waypoint_connections[1][0], LineString([(3, 4), (0, 0)]))
        self.assertIsNone(waypoint_connections[1][1])

        self.assertEqual(cost_matrix[0][0], 0)
        self.assertEqual(cost_matrix[0][1], 5)
        self.assertEqual(cost_matrix[1][0], 50)
        self.assertEqual(cost_matrix[1][1], 0)
