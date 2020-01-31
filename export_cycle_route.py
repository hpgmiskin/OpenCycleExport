from typing import List, Dict, Tuple, Any

import re
import csv
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
from open_cycle_export.route_downloader.download_places import download_places

from open_cycle_export.route_exporter.elevation_finder import find_elevations
from open_cycle_export.route_exporter.route_exporter import generate_gpx_file

from open_cycle_export.route_processor.route_processor import (
    process_route_features,
    find_furthest_waypoints,
    make_route_creator,
)

from open_cycle_export.shapely_utilities.immutable_point import ImmutablePoint
from open_cycle_export.shapely_utilities.geometry_encoder import GeometryEncoder

logger = logging.getLogger(__name__)

get_geometry = operator.itemgetter("geometry")


def format_name(name: str, substitute=""):
    return re.sub(r"\W+", substitute, name).lower()


def get_file_path(name: str, folder: str, extension: str = "json"):
    filename = "{}.{}".format(name, extension)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), folder, filename)


def export_gpx_route(route: MultiLineString, filename: str):
    filename = format_name(filename, "_")
    file_path = get_file_path(filename, "routes", "gpx")
    coordinates = [coord for line in route for coord in line.coords]
    elevations = find_elevations(coordinates)
    gpx_data = generate_gpx_file(coordinates, elevations)
    with open(file_path, "w") as open_file:
        open_file.write(gpx_data)


def store_json(data: Any, filename: str, **kwargs):
    file_path = get_file_path(filename, ".cache")
    with open(file_path, "w") as open_file:
        json.dump(data, open_file, **kwargs)


def store_route(route: MultiLineString, filename: str):
    route_data = shapely.geometry.mapping(route)
    store_json(route_data, filename)


def store_geometry(geometry_data: Any, filename: str):
    store_json(geometry_data, filename, cls=GeometryEncoder)


def load_json(filename: str):
    file_path = get_file_path(filename, ".cache")
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


def merge_line_strings(line_strings: List[LineString]):
    ways_multi_line_string = shapely.ops.linemerge(line_strings)
    if isinstance(ways_multi_line_string, MultiLineString):
        return ways_multi_line_string
    return MultiLineString([ways_multi_line_string])


def closest_place_index_finder(place_points: List[ImmutablePoint]):
    place_indexes = list(range(len(place_points)))

    def find_closest_place_index(search_point: ImmutablePoint):
        return min(place_indexes, key=lambda i: search_point.distance(place_points[i]))

    return find_closest_place_index


def process_route_data(area, route_type, route_number):

    route_name = "{}_{}_{}".format(format_name(area), route_type, route_number)
    logger.info("process route %s", route_name)

    route_features = download_cycle_route(area, route_type, route_number)["features"]
    logger.info("downloaded %s route features", len(route_features))

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

    return (
        route_features,
        waypoints,
        waypoint_distances,
        waypoint_connections,
        costs_matrix,
    )


def plot_routes(route_features, routes):

    line_strings = list(map(shapely.geometry.shape, map(get_geometry, route_features)))
    ways_multi_line_string = merge_line_strings(line_strings)

    map_plotter = MapPlotter()

    for route_name, route_multi_line_string in routes:
        map_plotter.plot_multi_line_string(route_name, route_multi_line_string)

    map_plotter.show(ways_multi_line_string.centroid)


def abbreviate_area(area):
    words = re.split(r"\s+", area)
    return area[:2] if len(words) < 2 else "".join([word[0] for word in words])


def create_route(area, route_type, route_number, show_plot=False):

    process_route_data_results = process_route_data(area, route_type, route_number)
    route_features, *route_creator_inputs = process_route_data_results
    waypoints, waypoint_distances = route_creator_inputs[:2]

    place_features = download_places(area)["features"]
    logger.info("downloaded %s place features", len(place_features))

    place_names = [
        feature.get("properties", {}).get("name") for feature in place_features
    ]
    place_points = [
        ImmutablePoint(*feature.get("geometry", {}).get("coordinates"))
        for feature in place_features
    ]
    find_closest_place_index = closest_place_index_finder(place_points)

    route_creator = make_route_creator(*route_creator_inputs)

    point_a_index, point_b_index = find_furthest_waypoints(waypoint_distances)

    route_a_to_b = route_creator(point_a_index, point_b_index)
    route_b_to_a = route_creator(point_b_index, point_a_index)

    waypoint_a = waypoints[point_a_index]
    waypoint_b = waypoints[point_b_index]

    place_name_a = place_names[find_closest_place_index(waypoint_a)]
    place_name_b = place_names[find_closest_place_index(waypoint_b)]

    route_a_to_b_name = "{} - {} to {}".format(route_number, place_name_a, place_name_b)
    route_b_to_a_name = "{} - {} to {}".format(route_number, place_name_b, place_name_a)

    if show_plot:
        plot_routes(
            route_features,
            [(route_a_to_b_name, route_a_to_b), (route_b_to_a_name, route_b_to_a)],
        )

    logger.info("export gpx files for both directions")
    base_name = "{} {}".format(abbreviate_area(area), route_type)
    route_a_to_b_full_name = "{} {}".format(base_name, route_a_to_b_name)
    route_b_to_a_full_name = "{} {}".format(base_name, route_b_to_a_name)
    export_gpx_route(route_a_to_b, route_a_to_b_full_name)
    export_gpx_route(route_b_to_a, route_b_to_a_full_name)
    logger.info("route creation complete")


def get_csv_data(filename):
    with open(filename) as open_file:
        csv_file = csv.reader(open_file)
        return list(csv_file)[1:]


def create_all_routes(area=None):
    cycle_routes = get_csv_data("data/cycle_routes.csv")
    cycle_routes = (
        cycle_routes
        if area is None
        else [cycle_route for cycle_route in cycle_routes if cycle_route[0] == area]
    )
    for area, route_type, route_number in cycle_routes:
        logger.info("creating route %s %s %s", area, route_type, route_number)
        create_route(area, route_type, route_number)


def main():
    create_route("Belgium", "ncn", "F4", True)
    create_route("France", "ncn", "V87", True)
    create_route("Great Britain", "ncn", "1", True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
