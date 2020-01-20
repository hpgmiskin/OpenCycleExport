from typing import Dict, List

import logging

from shapely.geometry import LineString

from open_cycle_export.route_processor.routing_algorithm import route_creator
from open_cycle_export.route_processor.way_processor import process_ways
from open_cycle_export.route_processor.way_coefficient_calculator import (
    create_way_coefficient_calculator,
)

Feature = Dict
Features = List[Feature]

logger = logging.getLogger(__name__)


def create_line_strings(features: Features) -> List[LineString]:
    logger.info("create line strings for %s features", len(features))
    return [LineString(feature["geometry"]["coordinates"]) for feature in features]


def create_route(features: Features):

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
        calculate_way_coefficient(feature["properties"], "bicycle", "forward")
        for feature in features
    ]

    logger.info("processing %s ways to find waypoints", len(ways))
    waypoints, waypoint_connections, costs_matrix = process_ways(
        ways, forward_coefficients, reverse_coefficients, unconnected_coefficient
    )

    waypoint_indexes = list(range(len(waypoints)))
    logger.info("creating route between %s waypoints", len(waypoints))
    route = route_creator(waypoint_indexes, costs_matrix)(
        waypoint_indexes[0], waypoint_indexes[-1]
    )

    segments = []

    for i in range(1, len(route)):
        i_a, i_b = i - 1, i
        connection = waypoint_connections[i_a][i_b]
        segments.append(
            connection or LineString([*waypoints[i_a].coords, *waypoints[i_b].coords])
        )

    return segments
