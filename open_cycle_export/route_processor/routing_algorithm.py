"""
Create a route from a collection of waypoints and route segments

Waypoint - Index of point at start or end of a line

"""

from typing import List, Dict, Set, Tuple, Callable

import numpy

Waypoint = int
Waypoints = List[Waypoint]
CostMatrix = List[List[float]]
CreateRoute = Callable[[Waypoint, Waypoint], Waypoints]


def route_creator(waypoints: Waypoints, cost_matrix: CostMatrix) -> CreateRoute:
    """Returns a function used to create a route between two points
    
    Arguments:
        waypoints {Waypoints} -- Waypoints available to use for navigation
        cost_matrix {CostMatrix} -- Cost of direct travel between all waypoints
    
    Returns:
        CreateRoute -- Function to create a route between two locations
    """

    waypoints = numpy.array(waypoints)
    cost_matrix = numpy.array(cost_matrix)

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
        min_costs = numpy.full(len(waypoints), numpy.inf)
        min_costs[start_waypoint] = 0
        current_waypoint = start_waypoint

        # Find minimum costs from start waypoint until end waypoint is current minimum
        while current_waypoint != end_waypoint:
            unvisited_waypoints.remove(current_waypoint)
            # Find waypoints best accessed from current
            cost_to_current = min_costs[current_waypoint]
            costs_from_current = cost_matrix[current_waypoint]
            cost_from_start = cost_to_current + costs_from_current
            is_closer_from_here = cost_from_start < min_costs
            # Record waypoints which are best accessed from current
            children = numpy.flatnonzero(is_closer_from_here)
            waypoint_parents.update({child: current_waypoint for child in children})
            # Update global minimum costs when route is better from this waypoint
            min_costs = numpy.where(is_closer_from_here, cost_from_start, min_costs)
            # Select unvisited waypoint with least cost to reach
            is_unvisited = numpy.isin(waypoints, list(unvisited_waypoints))
            unvisited_costs = numpy.where(is_unvisited, min_costs, numpy.inf)
            current_waypoint = numpy.argmin(unvisited_costs)

        # Build the route by traversing the parents backwards
        reverse_route = [end_waypoint]
        current_waypoint = end_waypoint
        while current_waypoint != start_waypoint:
            current_waypoint = waypoint_parents[current_waypoint]
            reverse_route.append(current_waypoint)

        # Return route the correct way around
        return reverse_route[-1::-1]

    return create_route
