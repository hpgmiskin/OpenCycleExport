"""
Create a route from a collection of waypoints and route segments

Waypoint - Index of point at start or end of a line

"""

from typing import List, Dict, Set, Tuple

import numpy

Waypoint = int
Waypoints = List[Waypoint]
WaypointSet = Set[Waypoint]
ConnectedWaypoints = Dict[Waypoint, Waypoints]
WaypointDistances = List[List[float]]


def route_creator(
    waypoints: Waypoints,
    connected_waypoints: ConnectedWaypoints,
    vertex_distances: WaypointDistances,
    euclidean_distances: WaypointDistances,
):
    """Returns a function used to create a route between two points
    
    Arguments:
        waypoints {Waypoints} -- Waypoints available to use for navigation
        neighbor_distances {NeighborDistances} -- Path distance to neighbor waypoints
        euclidean_distances {WaypointDistances} -- Straight line between each waypoint
    
    Returns:
        create_route -- Function to create a route between two locations
    """

    waypoints = numpy.array(waypoints)
    vertex_distances = numpy.array(vertex_distances)
    euclidean_distances = numpy.array(euclidean_distances)

    def create_route(start_waypoint: Waypoint, end_waypoint: Waypoint):
        """Create a route between two places
        
        Arguments:
            start_waypoint {Waypoint} -- Start waypoint to generate route from
            end_waypoint {Waypoint} -- End waypoint to find route too
        
        Returns:
            route {Waypoints} -- List of waypoints which make a route
        """

        waypoint_parents = {}
        unvisited_waypoints = set(waypoints)
        min_distances = numpy.full(len(waypoints), numpy.inf)
        min_distances[start_waypoint] = 0
        current_waypoint = start_waypoint

        # Find minimum distances from start waypoint until end waypoint is current minimum

        while current_waypoint != end_waypoint:

            unvisited_waypoints.remove(current_waypoint)

            current_waypoint_distances = euclidean_distances[current_waypoint] * 1000
            current_connected_waypoints = connected_waypoints[current_waypoint]
            current_vertex_distances = numpy.array(
                [
                    vertex_distances[current_waypoint][next_waypoint]
                    for next_waypoint in current_connected_waypoints
                ]
            )

            numpy.put(
                current_waypoint_distances,
                current_connected_waypoints,
                current_vertex_distances,
            )

            distance_to_current = min_distances[current_waypoint]
            distances_from_start = distance_to_current + current_waypoint_distances
            is_closer_from_here = distances_from_start < min_distances
            child_indexes = numpy.flatnonzero(is_closer_from_here)

            waypoint_parents.update(
                {child_index: current_waypoint for child_index in child_indexes}
            )

            min_distances = numpy.where(
                is_closer_from_here, distances_from_start, min_distances
            )

            unvisited_waypoints_array = numpy.array(list(unvisited_waypoints))
            is_unvisited = numpy.isin(waypoints, unvisited_waypoints_array)
            unvisited_distances = numpy.where(is_unvisited, min_distances, numpy.inf)
            current_waypoint = numpy.argmin(unvisited_distances)

        # Build the route by traversing the parents backwards

        reverse_route = [end_waypoint]
        current_waypoint = end_waypoint
        while current_waypoint != start_waypoint:
            current_waypoint = waypoint_parents[current_waypoint]
            reverse_route.append(current_waypoint)

        return reverse_route[-1::-1]

    return create_route
