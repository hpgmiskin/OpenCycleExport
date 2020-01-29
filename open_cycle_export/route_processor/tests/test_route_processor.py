import unittest

import json
import os.path


from open_cycle_export.route_processor.route_processor import (
    find_furthest_waypoints,
    create_route,
)
from open_cycle_export.shapely_utilities.immutable_point import ImmutablePoint
from open_cycle_export.test_data.test_data_loader import load_test_data


class TestFurthestWaypointFinder(unittest.TestCase):
    """Test finding the furthest waypoints"""

    def test_simple_matrix(self):
        waypoint_distances = [[0, 1, 2], [1, 0, 1], [2, 1, 0]]
        furthest_waypoints = find_furthest_waypoints(waypoint_distances)
        self.assertTupleEqual(furthest_waypoints, (0, 2))


class TestRouteProcessor(unittest.TestCase):
    """Test overall route processing"""

    def setUp(self):
        roundabout_features_file = "test_route_processor_roundabout_data.json"
        self.roundabout_features = load_test_data(roundabout_features_file)
        self.south_west_point = ImmutablePoint(-0.943355, 50.996674)
        self.north_east_point = ImmutablePoint(-0.942682, 50.996912)
        self.roundabout_north = (-0.943146, 50.996985)
        self.roundabout_east = (-0.942975, 50.996905)
        self.roundabout_south = (-0.943126, 50.996774)
        self.roundabout_west = (-0.943253, 50.996801)

    def test_roundabout_from_south_west_goes_round_north(self):
        route = create_route(
            self.roundabout_features, self.south_west_point, self.north_east_point
        )
        self.assertEqual(len(route), 3)
        self.assertEqual(route[1].coords[0], self.roundabout_west)
        self.assertIn(self.roundabout_north, route[1].coords)
        self.assertEqual(route[1].coords[-1], self.roundabout_east)

    def test_roundabout_from_north_east_goes_round_south(self):
        route = create_route(
            self.roundabout_features, self.north_east_point, self.south_west_point
        )
        self.assertEqual(len(route), 4)
        self.assertEqual(route[1].coords[0], self.roundabout_east)
        self.assertEqual(route[1].coords[-1], self.roundabout_south)
        self.assertEqual(route[2].coords[0], self.roundabout_south)
        self.assertEqual(route[2].coords[-1], self.roundabout_west)
