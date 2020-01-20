from typing import Tuple, List, Set

import math
import unittest

from open_cycle_export.route_processor.routing_algorithm import (
    Waypoint,
    Waypoints,
    CostMatrix,
    route_creator,
)

Coordinate = Tuple[float, float]
Coordinates = List[Coordinate]
Connection = Tuple[int, int]
Connections = List[Connection]


def euclidean_distance(c1: Coordinate, c2: Coordinate) -> float:
    """Straight line distance between two coordinates in 2D space
    
    Arguments:
        c1 {Coordinate} -- Source coordinate
        c2 {Coordinate} -- Destination coordinate
    
    Returns:
        float -- Straight line distance between coordinates
    """
    return math.sqrt((c2[0] - c1[0]) ** 2 + (c2[1] - c1[1]) ** 2)


def compute_cost(
    euclidean_distance: float, is_connected: bool, disconnected_multiplier: float
) -> float:
    """Cost of travel given a straight line distance and if points are connected
    
    Arguments:
        euclidean_distance {float} -- Straight line distance between locations
        is_connected {bool} -- Boolean flag to declare if the points are connected
        disconnected_multiplier {float} -- Distance multiplier for disconnected points
    
    Returns:
        float -- Cost of travel between two points
    """
    return (
        euclidean_distance
        if is_connected
        else disconnected_multiplier * euclidean_distance
    )


def create_costs_matrix(
    waypoints: Waypoints,
    coordinates: Coordinates,
    connections: Connections,
    disconnected_multiplier: float = 1000,
) -> CostMatrix:
    """Create a matrix of costs for travel between all waypoints
    
    Arguments:
        waypoints {Waypoints} -- List of all waypoints
        coordinates {Coordinates} -- Coordinate positions of all waypoints
        connections {Connections} -- List of connections between waypoints
    
    Keyword Arguments:
        disconnected_multiplier {float} -- Multiplier for costs where no connection exists (default: {1000})
    
    Returns:
        CostMatrix -- Matrix for cost of travel between all waypoints
    """
    return [
        [
            compute_cost(
                euclidean_distance(coordinates[i], coordinates[j]),
                ((i, j) in connections),
                disconnected_multiplier,
            )
            for j in waypoints
        ]
        for i in waypoints
    ]


class TestCreateCostsMatrix(unittest.TestCase):
    """Should create a costs matrix from coordinates and connections"""

    def test_simple_cost_matrix(self):
        cost_matrix = create_costs_matrix([0, 1], [(0, 0), (2, 0)], [(0, 1), (1, 0)])
        self.assertListEqual(cost_matrix[0], [0, 2])
        self.assertListEqual(cost_matrix[1], [2, 0])

    def test_disconnected_costs_matrix(self):
        cost_matrix = create_costs_matrix([0, 1], [(0, 0), (2, 0)], [(0, 1)])
        self.assertListEqual(cost_matrix[0], [0, 2])
        self.assertListEqual(cost_matrix[1], [2000, 0])


def basic_route_data() -> Tuple[Waypoints, CostMatrix]:
    waypoints: Waypoints = [0, 1, 2]
    waypoint_coordinates: Coordinates = [(0, 0), (2, 0), (4, 0)]
    waypoint_connections: Connections = set([(0, 1), (1, 2), (2, 1), (1, 0)])
    return (
        waypoints,
        create_costs_matrix(waypoints, waypoint_coordinates, waypoint_connections),
    )


def disconnected_route_data() -> Tuple[Waypoints, CostMatrix]:
    waypoints: Waypoints = [0, 1, 2, 3, 4]
    waypoint_coordinates: Coordinates = [(0, 0), (2, 0), (4, 0), (5, 0), (7, 0)]
    # waypoints 2 and 3 do not connect to one another
    waypoint_connections: Connections = set(
        [(0, 1), (1, 0), (1, 2), (2, 1), (3, 4), (4, 3)]
    )
    return (
        waypoints,
        create_costs_matrix(waypoints, waypoint_coordinates, waypoint_connections),
    )


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
