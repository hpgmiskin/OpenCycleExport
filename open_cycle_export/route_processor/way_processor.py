"""Way processor takes ways which make up a route and transforms them for the route creator

1. Split ways into line segments at connections with other ways
2. Find waypoints at all joins between created line segments
3. Create cost matrix between all waypoints using line segment length or euclidean distance

"""

from typing import List, Dict, Tuple, Callable
from collections import OrderedDict

import shapely.ops
from shapely.geometry import Point, LineString

from open_cycle_export.shapely_utilities.immutable_point import ImmutablePoint
from open_cycle_export.shapely_utilities.line_string_tools import reverse_line_string

Waypoints = List[ImmutablePoint]
WaypointConnections = List[List[LineString]]
CostsMatrix = List[List[float]]

StoreWaypointConnection = Callable[[ImmutablePoint, ImmutablePoint, int], None]
RetrieveWaypointConnections = Callable[[ImmutablePoint, ImmutablePoint], List[int]]


def find_intersecting_lines(lines: List[LineString]) -> List[List[LineString]]:
    return [
        [
            line_b
            for j, line_b in enumerate(lines)
            if i != j and line_a.intersects(line_b)
        ]
        for i, line_a in enumerate(lines)
    ]


def filter_contained_points(line: LineString, points: List[Point]) -> List[Point]:
    return [point for point in points if line.contains(point)]


def split_line_at_points(line: LineString, points: List[Point]):
    "Reccursively split the line at all the break points"

    contained_points = filter_contained_points(line, points)
    if len(contained_points) < 1:
        return [line]
    else:
        split_lines = []
        break_point = contained_points[0]
        try:
            for line_segment in shapely.ops.split(line, break_point):
                split_lines.extend(split_line_at_points(line_segment, points))
        except ValueError as split_error:
            # print(line)
            # print(break_point)
            # print(split_error)
            split_lines.append(line)
        return split_lines


def split_line_by_intersecting_lines(
    line: LineString, intersecting_lines: List[LineString]
) -> List[LineString]:
    intersection_points = [
        line.intersection(intersecting_line) for intersecting_line in intersecting_lines
    ]
    return split_line_at_points(line, intersection_points)


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

    # Split all ways into line segments where other ways intersect
    for way_index in range(len(ways)):
        way = ways[way_index]
        intersecting_ways = ways_intersecting_ways[way_index]
        way_line_segments = split_line_by_intersecting_lines(way, intersecting_ways)
        for way_line_segment in way_line_segments:
            line_segments.append(way_line_segment)
            line_segments_way_lookup.append(way_index)

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

    for line_index, line_segment in enumerate(line_segments):
        start_waypoint, end_waypoint = get_line_endpoints(line_segment)
        add_waypoint(start_waypoint, line_index)
        add_waypoint(end_waypoint, line_index + 0.5)
        store_connection(start_waypoint, end_waypoint, line_index)

    return sorted(list(waypoints.keys()), key=get_order), retrieve_connections


def process_ways(
    ways: List[LineString],
    forward_coefficients: List[float],
    reverse_coefficients: List[float],
    unconnected_coefficient: float,
) -> Tuple[Waypoints, WaypointConnections, CostsMatrix]:
    """Process ways to be used in route creation
    
    Arguments:
        ways {List[LineString]} -- List of all available ways 
        forward_coefficients {List[float]} -- Coefficients for travel along each way in forward direction
        reverse_coefficients {List[float]} -- Coefficients for travel along each way in reverse direction
        unconnected_coefficient {float} -- Coefficient to apply to straight line distance when no way exists between waypoints
    
    Returns:
        Tuple[Waypoints, WaypointConnections, CostsMatrix] -- waypoints, waypoint_connections, cost_matrix
    """

    line_segments, line_segments_way_lookup = create_line_segments(ways)

    def create_segment_costs(coefficients):
        return [
            coefficients[line_segments_way_lookup[index]] * line_segment.length
            for index, line_segment in enumerate(line_segments)
        ]

    line_forward_costs = create_segment_costs(forward_coefficients)
    line_reverse_costs = create_segment_costs(reverse_coefficients)

    waypoints, retrieve_connections = create_waypoints(line_segments)

    waypoint_connections: WaypointConnections = []
    costs_matrix: CostsMatrix = []

    def get_costs_from_indexes(directed_costs, connection_indexes):
        return [
            directed_costs[connection_index] for connection_index in connection_indexes
        ]

    for i, point_a in enumerate(waypoints):

        waypoint_connections.append([])
        costs_matrix.append([])

        for j, point_b in enumerate(waypoints):

            forward_connections = retrieve_connections(point_a, point_b)
            reverse_connections = retrieve_connections(point_b, point_a)

            connections = [
                *[(index, "forward") for index in forward_connections],
                *[(index, "reverse") for index in reverse_connections],
            ]

            def get_connection_cost(connection):
                connection_index, direction = connection
                if direction == "forward":
                    return line_forward_costs[connection_index]
                elif direction == "reverse":
                    return line_reverse_costs[connection_index]
                else:
                    raise RuntimeError("Should be forward or reverse")

            if len(connections):

                connection_index, direction = min(connections, key=get_connection_cost)
                line_segment = line_segments[connection_index]
                waypoint_connections[i].append(
                    line_segment
                    if direction == "forward"
                    else reverse_line_string(line_segment)
                )

                cost = get_connection_cost((connection_index, direction))
                costs_matrix[i].append(cost)

            else:

                waypoint_connections[i].append(None)

                euclidean_distance = point_a.distance(point_b)
                unconnected_cost = euclidean_distance * unconnected_coefficient
                costs_matrix[i].append(unconnected_cost)

    return waypoints, waypoint_connections, costs_matrix
