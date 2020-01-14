import unittest

from open_cycle_export.route_processor.route_creator import route_creator


def basic_route_data():
    waypoints = [0, 1, 2]
    connected_waypoints = {0: [1], 1: [0, 2], 2: [1]}
    # vertex_distances = {(0, 1): 2, (1, 0): 2, (1, 2): 2, (2, 1): 2}
    waypoint_distances = [[0, 2, 4], [2, 0, 2], [4, 2, 0]]
    return waypoints, connected_waypoints, waypoint_distances, waypoint_distances


def disconnected_route_data():
    waypoints = [0, 1, 2, 3, 4]
    # waypoints 2 and 3 do not connect to one another
    connected_waypoints = {0: [1], 1: [0, 2], 2: [1], 3: [4], 4: [3]}
    waypoint_distances = [
        [0, 2, 4, 5, 7],
        [2, 0, 2, 3, 5],
        [4, 2, 0, 1, 3],
        [5, 3, 1, 0, 2],
        [7, 5, 4, 2, 0],
    ]
    return waypoints, connected_waypoints, waypoint_distances, waypoint_distances


class TestRouteCreator(unittest.TestCase):
    "Test routes can be created when waypoints connected or close to one another"

    def test_basic_base_case(self):
        "Route between same start and end should only contain single waypoint"
        create_route = route_creator(*basic_route_data())
        self.assertListEqual(create_route(2, 2), [2])

    def test_basic_single_connected_route(self):
        "Waypoints directly connected should be returned as two element list"
        create_route = route_creator(*basic_route_data())
        self.assertListEqual(create_route(0, 1), [0, 1])

    def test_basic_connected_route(self):
        "Waypoints directly connected should be returned as three element list"
        create_route = route_creator(*basic_route_data())
        self.assertListEqual(create_route(0, 2), [0, 1, 2])

    def test_disconnected_waypoints_jump_gap(self):
        "Waypoints which are close but there is no connection should return connection"
        create_route = route_creator(*disconnected_route_data())
        self.assertListEqual(create_route(2, 3), [2, 3])

    def test_disconnected_waypoints_full_route(self):
        "Waypoints which are close but there is no connection should return route"
        create_route = route_creator(*disconnected_route_data())
        self.assertListEqual(create_route(0, 4), [0, 1, 2, 3, 4])
