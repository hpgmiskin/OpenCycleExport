"""
Create a route from a collection of waypoints and route segments

Waypoint - Index of point at start or end of a line

"""

from typing import List, Dict, Set

import itertools

Waypoint = int
Waypoints = List[Waypoint]

ConnectedWaypoints = Dict[Waypoint, Waypoints]
WaypointDistances = List[List[float]]

WaypointSet = Set[Waypoint]


class NoRouteError(Exception):
    pass


def add_waypoint(current_set, *new_items):
    return current_set | set(new_items)


def route_creator(
    waypoints: Waypoints,
    connected_waypoints: ConnectedWaypoints,
    waypoint_distances: WaypointDistances,
    number_close_waypoint_search: int = 10,
):
    """Returns a function used to create a route between two points
    
    Arguments:
        waypoints {Waypoints} -- Waypoints available to use for navigation
        connected_waypoints {ConnectedWaypoints} -- Lookup table connected waypoints
        waypoint_distances {WaypointDistances} -- Distance between each waypoint
    
    Returns:
        create_route -- Function to create a route between two locations
    """

    def create_route(
        start_point: Waypoint,
        end_point: Waypoint,
        visited_waypoints: WaypointSet = set(),
    ):
        """Create a route between two places
        
        Arguments:
            start_point {Waypoint} -- Start waypoint to generate route from
            end_point {Waypoint} -- End waypoint to find route too
            visited_waypoints {WaypointSet} -- Set of waypoints already visited
        
        Returns:
            route {Waypoints} -- List of waypoints which make a route
            unconnected_distance {float} -- Distance 
        """

        # Base case where route complete
        if start_point == end_point:
            return [end_point], 0

        def find_distance(next_point):
            if start_point == next_point:
                return max(waypoint_distances[start_point])
            return waypoint_distances[start_point][next_point]

        def find_route(next_waypoint, current_unconnected_distance=0):
            updated_visited = add_waypoint(visited_waypoints, start_point)
            route, unconnected_distance = create_route(
                next_waypoint, end_point, updated_visited
            )
            return (
                [start_point, *route],
                current_unconnected_distance + unconnected_distance,
            )

        # List of directly connected waypoints
        directly_connected_waypoints = connected_waypoints[start_point]

        # All unvisited waypoints which are connected to the start point
        connected_unvisited_waypoints = [
            connected_waypoint
            for connected_waypoint in directly_connected_waypoints
            if connected_waypoint not in visited_waypoints
        ]

        # Compare distance from start point to end point with distance to start point
        current_distance = waypoint_distances[start_point][end_point]
        closer_connected_waypoints = [
            next_waypoint
            for next_waypoint in connected_unvisited_waypoints
            if waypoint_distances[next_waypoint][end_point] < current_distance
        ]

        # If there are directly connected waypoints we chose the route with least unconnected
        if len(closer_connected_waypoints):
            return min(
                [
                    find_route(next_waypoint)
                    for next_waypoint in closer_connected_waypoints
                ],
                key=lambda result: result[1],
            )

        # If there are no connected and unvisited waypoints find all unvisited waypoints
        unvisited_waypoints = [
            waypoint for waypoint in waypoints if waypoint not in visited_waypoints
        ]

        # Create list of a couple of closest unvisited waypoint
        closest_unvisited_waypoints = itertools.islice(
            sorted(unvisited_waypoints, key=find_distance), number_close_waypoint_search
        )

        # Select the route with the least
        return min(
            [
                find_route(next_waypoint, find_distance(next_waypoint))
                for next_waypoint in closest_unvisited_waypoints
            ],
            key=lambda result: result[1],
        )

    return create_route
