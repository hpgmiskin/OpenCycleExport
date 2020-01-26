from typing import Dict, List, Any

import logging

from shapely.geometry import Point, LineString, MultiLineString

from open_cycle_export.route_processor.routing_algorithm import route_creator
from open_cycle_export.route_processor.way_processor import process_ways
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


def create_route(
    features: Features, start_point: ImmutablePoint, end_point: ImmutablePoint
) -> MultiLineString:

    ways = create_line_strings(features)

    connected_coefficients = [1, 2, 10, 100]
    unconnected_coefficient = 1000

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

    logger.info("processing %s ways to find waypoints", len(ways))
    waypoints, waypoint_connections, costs_matrix = process_ways(
        ways, forward_coefficients, reverse_coefficients, unconnected_coefficient
    )

    waypoint_indexes = list(range(len(waypoints)))
    logger.info("creating route between %s waypoints", len(waypoints))
    create_route_function = route_creator(waypoint_indexes, costs_matrix)

    start_waypoint_index = waypoints.index(start_point)
    end_waypoint_index = waypoints.index(end_point)
    route = create_route_function(start_waypoint_index, end_waypoint_index)

    def straight_line(i_a: int, i_b: int) -> LineString:
        return LineString([*waypoints[i_a].coords, *waypoints[i_b].coords])

    connection_indexes = map(lambda i: (route[i - 1], route[i]), range(1, len(route)))
    return MultiLineString(
        [
            waypoint_connections[i_a][i_b] or straight_line(i_a, i_b)
            for i_a, i_b in connection_indexes
        ]
    )
