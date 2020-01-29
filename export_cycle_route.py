from typing import List, Dict, Tuple, Any

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
from open_cycle_export.route_processor.route_processor import (
    process_route_features,
    create_longest_route,
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


def main(recompute=True):

    route_area, route_type, route_number = "United Kingdom", "ncn", 22
    route_name = "uk_{}_{}".format(route_type, route_number)

    features = download_cycle_route(route_area, route_type, route_number)["features"]
    logger.info("downloaded %s features", len(features))

    # features = filter_features(features, create_bbox_polygon(*IOW_BBOX))
    # features = filter_features(features, Polygon(PETERSFIELD_ROUNDABOUT))
    # logger.warning("filtered features to %s entries", len(features))
    # route_name = "{}_filter_{}".format(route_name, len(features))
    # print(json.dumps(features, indent=4))

    line_strings = list(map(shapely.geometry.shape, map(get_geometry, features)))
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
    except FileNotFoundError:
        logger.info("Cache not loaded")
        result = process_route_features(features)
        waypoints, waypoint_distances, waypoint_connections, costs_matrix = result
        store_geometry(waypoints, waypoints_filename)
        store_json(waypoint_distances, waypoint_distances_filename)
        store_geometry(waypoint_connections, waypoint_connections_filename)
        store_json(costs_matrix, costs_matrix_filename)

    try:
        route_multi_line_string = load_route(route_name)
    except FileNotFoundError:
        inputs = waypoints, waypoint_distances, waypoint_connections, costs_matrix
        route_multi_line_string = create_longest_route(*inputs)
        store_route(route_multi_line_string, route_name)

    map_plotter = MapPlotter()
    map_plotter.plot_multi_line_string("Ways", ways_multi_line_string)
    map_plotter.plot_multi_line_string("Route", route_multi_line_string)
    map_plotter.plot_waypoints("Waypoints", original_waypoints)
    map_plotter.show(route_multi_line_string.centroid)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
