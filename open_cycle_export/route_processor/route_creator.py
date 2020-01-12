"""
Create a route from a collection of waypoints and route segments

Waypoint - Index of point at start or end of a line

"""

from typing import List, Dict, Set

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

        #
        directly_connected_waypoints = connected_waypoints[start_point]

        # All unvisited waypoints which are connected to the start point
        connected_unvisited_waypoints = [
            connected_waypoint
            for connected_waypoint in directly_connected_waypoints
            if connected_waypoint not in visited_waypoints
        ]

        unconnected_unvisited_waypoints = [
            waypoint
            for waypoint in waypoints
            if (
                (waypoint not in directly_connected_waypoints)
                and (waypoint not in visited_waypoints)
            )
        ]

        closest_unconnected_unvisited_waypoints = [
            unconnected_waypoint
            for unconnected_waypoint in sorted(
                unconnected_unvisited_waypoints, key=find_distance
            )
        ][:number_close_waypoint_search]

        all_possible_routes = [
            find_route(
                next_waypoint,
                0
                if next_waypoint in directly_connected_waypoints
                else find_distance(next_waypoint),
            )
            for next_waypoint in [
                *connected_unvisited_waypoints,
                *closest_unconnected_unvisited_waypoints,
            ]
        ]

        return min(all_possible_routes, key=lambda result: result[1])

    return create_route
