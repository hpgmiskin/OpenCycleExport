"""Way processor takes ways which make up a route and transforms them for the route creator

1. Split ways into line segments at connections with other ways
2. Find waypoints at all joins between created line segments
3. Create cost matrix between all waypoints using line segment length or euclidean distance

"""

from typing import List, Dict, Tuple, Callable
from collections import OrderedDict

import time
import logging

import shapely.ops
from shapely.geometry import Point, LineString

from open_cycle_export.shapely_utilities.formatting_tools import pretty_geometry_print
from open_cycle_export.shapely_utilities.immutable_point import ImmutablePoint
from open_cycle_export.shapely_utilities.line_string_tools import reverse_line_string
from open_cycle_export.shapely_utilities.line_string_splitter import (
    split_line_by_intersecting_lines,
)

Waypoints = List[ImmutablePoint]
WaypointConnections = List[List[LineString]]
Matrix = List[List[float]]

StoreWaypointConnection = Callable[[ImmutablePoint, ImmutablePoint, int], None]
RetrieveWaypointConnections = Callable[[ImmutablePoint, ImmutablePoint], List[int]]

logger = logging.getLogger(__name__)


def find_intersecting_lines(lines: List[LineString]) -> List[List[LineString]]:
    logger.info("find intersecting lines")
    return [
        [
            line_b
            for j, line_b in enumerate(lines)
            if i != j and line_a.intersects(line_b)
        ]
        for i, line_a in enumerate(lines)
    ]


def get_line_endpoints(line: LineString) -> ImmutablePoint:
    return (ImmutablePoint(*line.coords[0]), ImmutablePoint(*line.coords[-1]))


def waypoint_connection_storage() -> Tuple[
    StoreWaypointConnection, RetrieveWaypointConnections
]:
    """Store and retrieve waypoint connections
    
    Returns:
        Tuple[StoreWaypointConnection, RetrieveWaypointConnections] -- Functions to store and retrieve waypoint connections
    """

    storage = {}

    def store(point_a: ImmutablePoint, point_b: ImmutablePoint, index: int):
        point_pair = (point_a, point_b)
        storage[point_pair] = storage.get(point_pair, [])
        storage[point_pair].append(index)

    def load(point_a: ImmutablePoint, point_b: ImmutablePoint) -> List[int]:
        point_pair = (point_a, point_b)
        return storage.get(point_pair, [])

    return store, load


def create_line_segments(ways: List[LineString]) -> Tuple[List[LineString], List[int]]:
    """Split ways into smallest line segments
    
    Arguments:
        ways {List[LineString]} -- Ways included in a route
    
    Returns:
        Tuple[List[LineString], List[int]] -- Smaller line segments and association between line segments and ways
    """

    line_segments = []
    line_segments_way_lookup = []
    ways_intersecting_ways = find_intersecting_lines(ways)
    logger.info("split ways into line segments")

    # Split all ways into line segments where other ways intersect
    for way_index in range(len(ways)):
        way = ways[way_index]
        intersecting_ways = ways_intersecting_ways[way_index]
        way_line_segments = split_line_by_intersecting_lines(way, intersecting_ways)
        for way_line_segment in way_line_segments:
            line_segments.append(way_line_segment)
            line_segments_way_lookup.append(way_index)

    logger.info("found %s line segments", len(line_segments))
    return line_segments, line_segments_way_lookup


def create_waypoints(
    line_segments: List[LineString],
) -> Tuple[List[ImmutablePoint], RetrieveWaypointConnections]:
    """Create a list of unique waypoints
    
    Arguments:
        line_segments {List[LineString]} -- Line segments between every desired waypoint
    
    Returns:
        Tuple[List[ImmutablePoint], RetrieveWaypointConnections] -- List of waypoints and function to get waypoint connections
    """

    waypoints = dict()
    store_connection, retrieve_connections = waypoint_connection_storage()

    def add_waypoint(waypoint, order):
        waypoints[waypoint] = waypoints.get(waypoint, order)

    def get_order(waypoint):
        return waypoints[waypoint]

    logger.info("create waypoints from line segments")
    for line_index, line_segment in enumerate(line_segments):
        start_waypoint, end_waypoint = get_line_endpoints(line_segment)
        add_waypoint(start_waypoint, line_index)
        add_waypoint(end_waypoint, line_index + 0.5)
        store_connection(start_waypoint, end_waypoint, line_index)

    logger.info("sort %s extracted waypoints", len(waypoints))
    return sorted(list(waypoints.keys()), key=get_order), retrieve_connections


def make_matrix(shape: Tuple[int, int], fill=None):
    return [[fill for j in range(shape[1])] for i in range(shape[0])]


def segment_cost_creator(line_segments, line_segments_way_lookup):
    def create_segment_costs(coefficients):
        return [
            coefficients[line_segments_way_lookup[index]] * line_segment.length
            for index, line_segment in enumerate(line_segments)
        ]

    return create_segment_costs


def connection_cost_getter(line_forward_costs, line_reverse_costs):
    def get_connection_cost(connection):
        connection_index, direction = connection
        if direction == "forward":
            return line_forward_costs[connection_index]
        elif direction == "reverse":
            return line_reverse_costs[connection_index]
        else:
            raise RuntimeError("Should be forward or reverse")

    return get_connection_cost


class Timer:
    def __init__(self):
        self.last_time = time.time()

    def get_elapsed(self):
        current_time = time.time()
        elapsed = current_time - self.last_time
        self.last_time = current_time
        return elapsed


def process_ways(
    ways: List[LineString],
    forward_coefficients: List[float],
    reverse_coefficients: List[float],
    unconnected_coefficient: float,
) -> Tuple[Waypoints, WaypointConnections, Matrix, Matrix]:
    """Process ways to be used in route creation
    
    Arguments:
        ways {List[LineString]} -- List of all available ways 
        forward_coefficients {List[float]} -- Coefficients for travel along each way in forward direction
        reverse_coefficients {List[float]} -- Coefficients for travel along each way in reverse direction
        unconnected_coefficient {float} -- Coefficient to apply to straight line distance when no way exists between waypoints
    
    Returns:
        Tuple[Waypoints, Matrix, WaypointConnections, Matrix] -- waypoints, waypoint_distances, waypoint_connections, cost_matrix
    """

    timer = Timer()

    logger.info("create line segment from %s ways (%s)", len(ways), timer.get_elapsed())
    line_segments, line_segments_way_lookup = create_line_segments(ways)
    logger.info("found %s line segments", len(line_segments))

    logger.info(
        "find line segment costs for forward and reverse (%s)", timer.get_elapsed()
    )
    create_segment_costs = segment_cost_creator(line_segments, line_segments_way_lookup)
    forward_costs = create_segment_costs(forward_coefficients)
    reverse_costs = create_segment_costs(reverse_coefficients)
    get_connection_cost = connection_cost_getter(forward_costs, reverse_costs)

    logger.info("create waypoints (%s)", timer.get_elapsed())
    waypoints, retrieve_connections = create_waypoints(line_segments)
    matrix_shape = (len(waypoints), len(waypoints))

    logger.info("make empty matrixes for results (%s)", timer.get_elapsed())
    waypoint_connections: WaypointConnections = make_matrix(matrix_shape)
    costs_matrix: Matrix = make_matrix(matrix_shape)

    logger.info("loop through all waypoint connections (%s)", timer.get_elapsed())
    waypoint_distances = [[w_a.distance(w_b) for w_b in waypoints] for w_a in waypoints]

    for i, point_a in enumerate(waypoints):
        for j, point_b in enumerate(waypoints):
            connections = [
                (index, "forward") for index in retrieve_connections(point_a, point_b)
            ] + [
                (index, "reverse") for index in retrieve_connections(point_b, point_a)
            ]
            if len(connections):
                connection_index, direction = min(connections, key=get_connection_cost)
                waypoint_connections[i][j] = (
                    line_segments[connection_index]
                    if direction == "forward"
                    else reverse_line_string(line_segments[connection_index])
                )
                costs_matrix[i][j] = get_connection_cost((connection_index, direction))
            else:
                costs_matrix[i][j] = waypoint_distances[i][j] * unconnected_coefficient

    time_elapsed_looping_waypoints = timer.get_elapsed()
    logger.info("process ways complete (%s)", time_elapsed_looping_waypoints)
    return waypoints, waypoint_distances, waypoint_connections, costs_matrix
