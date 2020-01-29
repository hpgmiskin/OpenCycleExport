import unittest

from shapely.geometry import LineString

from open_cycle_export.shapely_utilities.immutable_point import ImmutablePoint
from open_cycle_export.route_processor.way_processor import (
    waypoint_connection_storage,
    create_line_segments,
    create_waypoints,
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


class TestLineSegmentCreator(unittest.TestCase):
    """Test ways can be split into line segments"""

    def test_no_intersecting_points(self):
        ways = [LineString([(0, 0), (1, 1)]), LineString([(1, 1), (2, 2)])]
        line_segments, line_segment_ways = create_line_segments(ways)
        self.assertListEqual(ways, line_segments)
        self.assertListEqual(line_segment_ways, [0, 1])

    def test_single_intersection(self):
        ways = [LineString([(0, 0), (2, 2)]), LineString([(1, 1), (1, 2)])]
        line_segments, line_segment_ways = create_line_segments(ways)
        self.assertEqual(len(line_segments), 3)
        self.assertIn(LineString([(0, 0), (1, 1)]), line_segments)
        self.assertIn(LineString([(1, 1), (2, 2)]), line_segments)
        self.assertIn(LineString([(1, 1), (1, 2)]), line_segments)
        self.assertListEqual(line_segment_ways, [0, 0, 1])


class TestCreateWaypoints(unittest.TestCase):
    """Test creation of a unique list of waypoints in order provided"""

    def test_create_two_waypoints(self):
        waypoints, retrieve = create_waypoints([LineString([(0, 0), (3, 4)])])
        p_a, p_b = ImmutablePoint(0, 0), ImmutablePoint(3, 4)
        self.assertListEqual(waypoints, [p_a, p_b])
        self.assertEqual(retrieve(p_a, p_b), [0])

    def test_create_three_waypoints(self):
        waypoints, retrieve = create_waypoints(
            [LineString([(0, 0), (3, 4)]), LineString([(3, 4), (5, 6)])]
        )
        p_a, p_b, p_c = ImmutablePoint(0, 0), ImmutablePoint(3, 4), ImmutablePoint(5, 6)
        self.assertListEqual(waypoints, [p_a, p_b, p_c])
        self.assertEqual(retrieve(p_a, p_b), [0])
        self.assertEqual(retrieve(p_b, p_c), [1])


class TestWayProcessor(unittest.TestCase):
    """Test ways can be converted to line segments and cost matrix"""

    def test_single_way(self):
        "Should create basic cost matrix for a single way"

        ways = [LineString([(0, 0), (3, 4)])]
        forward_coefficients = [1]
        reverse_coefficients = [10]
        unconnected_coefficient = 100

        waypoints, _, waypoint_connections, cost_matrix = process_ways(
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

    def test_two_connected_ways(self):
        "Should find waypoints at all endpoints of ways and compute simple cost matrix"

        ways = [LineString([(0, 0), (3, 0)]), LineString([(3, 0), (3, 4)])]
        forward_coefficients = [1, 1]
        reverse_coefficients = [1, 1]
        unconnected_coefficient = 1000

        waypoints, _, waypoint_connections, cost_matrix = process_ways(
            ways, forward_coefficients, reverse_coefficients, unconnected_coefficient
        )

        expected_waypoints = [
            ImmutablePoint(0, 0),
            ImmutablePoint(3, 0),
            ImmutablePoint(3, 4),
        ]

        self.assertListEqual(waypoints, expected_waypoints)

        _way_0 = LineString([(3, 0), (0, 0)])
        _way_1 = LineString([(3, 4), (3, 0)])

        self.assertListEqual(
            waypoint_connections,
            [[None, ways[0], None], [_way_0, None, ways[1]], [None, _way_1, None]],
        )

        self.assertListEqual(cost_matrix, [[0, 3, 5000], [3, 0, 4], [5000, 4, 0]])
