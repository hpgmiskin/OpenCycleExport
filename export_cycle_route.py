from typing import List, Dict, Tuple, Any

import re
import json
import os.path
import logging
import operator

import shapely.ops
import shapely.geometry

from shapely.geometry import Point, LineString, MultiLineString, Polygon
from shapely.geometry.base import BaseGeometry

from open_cycle_export.map_builder.map_plotter import MapPlotter
from open_cycle_export.route_downloader.download_cycle_route import download_cycle_route
from open_cycle_export.route_downloader.download_towns import download_towns
from open_cycle_export.route_processor.route_processor import (
    process_route_features,
    find_furthest_waypoints,
    make_route_creator,
)
from open_cycle_export.shapely_utilities.immutable_point import ImmutablePoint
from open_cycle_export.shapely_utilities.geometry_encoder import GeometryEncoder

logger = logging.getLogger(__name__)

get_geometry = operator.itemgetter("geometry")


def get_file_path(name: str, extension: str = "json"):
    filename = "{}.{}".format(name, extension)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), ".cache", filename)


def store_json(data: Any, filename: str, **kwargs):
    file_path = get_file_path(filename)
    with open(file_path, "w") as open_file:
        json.dump(data, open_file, **kwargs)


def store_route(route: MultiLineString, filename: str):
    route_data = shapely.geometry.mapping(route)
    store_json(route_data, filename)


def store_geometry(geometry_data: Any, filename: str):
    store_json(geometry_data, filename, cls=GeometryEncoder)


def load_json(filename: str):
    file_path = get_file_path(filename)
    with open(file_path) as open_file:
        return json.load(open_file)


def load_route(name: str):
    route_data = load_json(name)
    return shapely.geometry.shape(route_data)


def load_waypoints(filename: str):
    return [ImmutablePoint(*point["coordinates"]) for point in load_json(filename)]


def load_waypoint_connections(filename: str):
    return [
        [
            None if connection is None else shapely.geometry.shape(connection)
            for connection in row
        ]
        for row in load_json(filename)
    ]


def create_bbox_polygon(min_x, min_y, max_x, max_y):
    return Polygon([(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)])


def filter_features(features: List[Dict], polygon: Polygon):
    return [
        feature
        for feature in features
        if shapely.geometry.shape(get_geometry(feature)).intersects(polygon)
    ]


IOW_BBOX = [-1.599259, 50.560611, -1.051316, 50.778640]
SMALL_BBOX = [-1.599259, 50.560611, -1.299863, 50.701102]
TINY_BBOX = [-1.599259, 50.560611, -1.31873, 50.696457]
PETERSFIELD_ROUNDABOUT = [
    (-0.9434456, 50.9970774),
    (-0.9435448, 50.9966503),
    (-0.9427268, 50.9966385),
    (-0.9427429, 50.9970774),
    (-0.9434456, 50.9970774),
]


def merge_line_strings(line_strings: List[LineString]):
    ways_multi_line_string = shapely.ops.linemerge(line_strings)
    if isinstance(ways_multi_line_string, MultiLineString):
        return ways_multi_line_string
    return MultiLineString([ways_multi_line_string])


def format_name(name: str):
    return re.sub(r"\s+", "", name).lower()


def closest_town_index_finder(town_points: List[ImmutablePoint]):
    town_indexes = list(range(len(town_points)))

    def find_closest_town_index(search_point: ImmutablePoint):
        return min(town_indexes, key=lambda i: search_point.distance(town_points[i]))

    return find_closest_town_index


def main(recompute=True):

    area, route_type, route_number = "England", "ncn", 13
    route_name = "{}_{}_{}".format(format_name(area), route_type, route_number)

    route_features = download_cycle_route(area, route_type, route_number)["features"]
    logger.info("downloaded %s route features", len(route_features))

    town_features = download_towns(area)["features"]
    logger.info("downloaded %s town features", len(town_features))

    # route_features = filter_features(route_features, create_bbox_polygon(*IOW_BBOX))
    # route_features = filter_features(route_features, Polygon(PETERSFIELD_ROUNDABOUT))
    # logger.warning("filtered features to %s entries", len(route_features))
    # route_name = "{}_filter_{}".format(route_name, len(route_features))
    # print(json.dumps(route_features, indent=4))

    town_names = [
        feature.get("properties", {}).get("name") for feature in town_features
    ]
    town_points = [
        ImmutablePoint(*feature.get("geometry", {}).get("coordinates"))
        for feature in town_features
    ]
    find_closest_town_index = closest_town_index_finder(town_points)

    line_strings = list(map(shapely.geometry.shape, map(get_geometry, route_features)))
    original_waypoints = [Point(line_string.coords[0]) for line_string in line_strings]
    ways_multi_line_string = merge_line_strings(line_strings)

    # # start_point = ImmutablePoint(-1.320715, 50.696457)
    # # end_point = ImmutablePoint(-0.170461, 51.324368)  # LONDON
    # # end_point = ImmutablePoint(-1.159577, 50.73947)  # FERRY
    # # end_point = ImmutablePoint(-1.299863, 50.701102)  # SMALL
    # # end_point = ImmutablePoint(-1.31873, 50.696209)  # TINY

    # # Route 13
    # start_point = ImmutablePoint(-0.074152, 51.506911)
    # end_point = ImmutablePoint(0.922066, 52.784473)

    # map_plotter = MapPlotter()
    # map_plotter.plot_multi_line_string("Ways", ways_multi_line_string)
    # map_plotter.plot_waypoints("Waypoints", original_waypoints)
    # map_plotter.show(ways_multi_line_string.centroid)

    waypoints_filename = "{}_waypoints".format(route_name)
    waypoint_distances_filename = "{}_waypoint_distances".format(route_name)
    waypoint_connections_filename = "{}_waypoint_connections".format(route_name)
    costs_matrix_filename = "{}_costs_matrix".format(route_name)

    try:
        waypoints = load_waypoints(waypoints_filename)
        waypoint_distances = load_json(waypoint_distances_filename)
        waypoint_connections = load_waypoint_connections(waypoint_connections_filename)
        costs_matrix = load_json(costs_matrix_filename)
        logger.info("using cached waypoints")
    except FileNotFoundError:
        logger.info("waypoint cache not found")
        result = process_route_features(route_features)
        waypoints, waypoint_distances, waypoint_connections, costs_matrix = result
        store_geometry(waypoints, waypoints_filename)
        store_json(waypoint_distances, waypoint_distances_filename)
        store_geometry(waypoint_connections, waypoint_connections_filename)
        store_json(costs_matrix, costs_matrix_filename)

    inputs = waypoints, waypoint_distances, waypoint_connections, costs_matrix
    route_creator = make_route_creator(*inputs)

    point_a_index, point_b_index = find_furthest_waypoints(waypoint_distances)

    route_a_to_b = route_creator(point_a_index, point_b_index)
    route_b_to_a = route_creator(point_b_index, point_a_index)

    waypoint_a = waypoints[point_a_index]
    waypoint_b = waypoints[point_b_index]

    waypoint_a_town_name = town_names[find_closest_town_index(waypoint_a)]
    waypoint_b_town_name = town_names[find_closest_town_index(waypoint_b)]

    route_a_to_b_name = "{} to {}".format(waypoint_a_town_name, waypoint_b_town_name)
    route_b_to_a_name = "{} to {}".format(waypoint_b_town_name, waypoint_a_town_name)

    map_plotter = MapPlotter()
    map_plotter.plot_multi_line_string("Ways", ways_multi_line_string)
    map_plotter.plot_multi_line_string(route_a_to_b_name, route_a_to_b)
    map_plotter.plot_multi_line_string(route_b_to_a_name, route_b_to_a)
    map_plotter.plot_waypoints("Waypoints", original_waypoints)
    map_plotter.show(ways_multi_line_string.centroid)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
