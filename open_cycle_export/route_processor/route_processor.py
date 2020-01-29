from typing import Dict, List, Tuple

import logging

import numpy
from shapely.geometry import Point, LineString, MultiLineString

from open_cycle_export.route_processor.routing_algorithm import route_creator
from open_cycle_export.route_processor.way_processor import (
    Waypoints,
    WaypointConnections,
    Matrix,
    process_ways,
)
from open_cycle_export.route_processor.way_coefficient_calculator import (
    create_way_coefficient_calculator,
)

from open_cycle_export.shapely_utilities.immutable_point import ImmutablePoint

Feature = Dict
Features = List[Feature]

logger = logging.getLogger(__name__)


def create_line_strings(features: Features) -> List[LineString]:
    logger.info("create line strings for %s features", len(features))
    return [LineString(feature["geometry"]["coordinates"]) for feature in features]


def process_route_features(
    features: Features,
) -> Tuple[Waypoints, Matrix, WaypointConnections, Matrix]:

    ways = create_line_strings(features)

    connected_coefficients = [1, 2, 10, 100]

    calculate_way_coefficient = create_way_coefficient_calculator(
        connected_coefficients
    )

    forward_coefficients = [
        calculate_way_coefficient(feature["properties"], "bicycle", "forward")
        for feature in features
    ]

    reverse_coefficients = [
        calculate_way_coefficient(feature["properties"], "bicycle", "reverse")
        for feature in features
    ]

    unconnected_coefficient = 1000

    logger.info("processing %s ways to find waypoints", len(ways))
    waypoints, waypoint_distances, waypoint_connections, costs_matrix = process_ways(
        ways, forward_coefficients, reverse_coefficients, unconnected_coefficient
    )

    return waypoints, waypoint_distances, waypoint_connections, costs_matrix


def find_furthest_waypoints(waypoint_distances: Matrix):
    waypoint_distances = numpy.array(waypoint_distances)
    max_flat_index = numpy.argmax(waypoint_distances)
    return numpy.unravel_index(max_flat_index, waypoint_distances.shape)


def straight_line_creator(waypoints: Waypoints):
    def straight_line(i_a: int, i_b: int) -> LineString:
        return LineString([*waypoints[i_a].coords, *waypoints[i_b].coords])

    return straight_line


def create_route_line_string(
    waypoints: Waypoints, waypoint_connections: WaypointConnections, route: List[int]
) -> MultiLineString:

    connection_indexes = map(lambda i: (route[i - 1], route[i]), range(1, len(route)))
    straight_line = straight_line_creator(waypoints)

    return MultiLineString(
        [
            waypoint_connections[i_a][i_b] or straight_line(i_a, i_b)
            for i_a, i_b in connection_indexes
        ]
    )


def create_longest_route(
    waypoints: Waypoints,
    waypoint_distances: Matrix,
    waypoint_connections: WaypointConnections,
    costs_matrix: Matrix,
) -> MultiLineString:

    waypoint_indexes = list(range(len(waypoints)))
    logger.info("creating route using %s waypoints", len(waypoints))
    create_route_function = route_creator(waypoint_indexes, costs_matrix)

    (start_index, end_index) = find_furthest_waypoints(waypoint_distances)
    (start_waypoint, end_waypoint) = waypoints[start_index], waypoints[end_index]
    logger.info("finding route between %s and %s", start_waypoint, end_waypoint)

    route = create_route_function(start_index, end_index)
    logger.info("found route through %s waypoints", len(route))
    return create_route_line_string(waypoints, waypoint_connections, route)


def create_route(
    features: Features, start_point: ImmutablePoint, end_point: ImmutablePoint
):

    processed_features = process_route_features(features)
    waypoints, _, waypoint_connections, costs_matrix = processed_features

    waypoint_indexes = list(range(len(waypoints)))
    create_route_function = route_creator(waypoint_indexes, costs_matrix)

    start_waypoint_index = waypoints.index(start_point)
    end_waypoint_index = waypoints.index(end_point)
    route = create_route_function(start_waypoint_index, end_waypoint_index)

    return create_route_line_string(waypoints, waypoint_connections, route)
