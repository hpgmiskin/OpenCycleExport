from typing import List, Dict, Tuple

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
from open_cycle_export.route_processor.route_processor import create_route
from open_cycle_export.shapely_utilities.immutable_point import ImmutablePoint

FILTER_FEATURES = False

logger = logging.getLogger(__name__)

get_geometry = operator.itemgetter("geometry")


def get_file_path(name: str, extension: str = "json"):
    filename = "{}.{}".format(name, extension)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), ".cache", filename)


def store_route(name: str, route: MultiLineString):
    file_path = get_file_path(name)
    route_data = shapely.geometry.mapping(route)
    json.dump(route_data, open(file_path, "w"))


def load_route(name: str):
    file_path = get_file_path(name)
    route_data = json.load(open(file_path))
    return shapely.geometry.shape(route_data)


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


def main(recompute=True):

    route_area, route_type, route_number = "United Kingdom", "ncn", 22
    route_name = "uk_{}_{}".format(route_type, route_number)

    features = download_cycle_route(route_area, route_type, route_number)["features"]
    logger.info("downloaded %s features", len(features))

    if FILTER_FEATURES:
        features = filter_features(features, create_bbox_polygon(*IOW_BBOX))
        features = filter_features(features, Polygon(PETERSFIELD_ROUNDABOUT))
        print(json.dumps(features, indent=4))

    line_strings = list(map(shapely.geometry.shape, map(get_geometry, features)))
    original_waypoints = [Point(line_string.coords[0]) for line_string in line_strings]
    ways_multi_line_string = shapely.ops.linemerge(line_strings)
    ways_multi_line_string = (
        ways_multi_line_string
        if isinstance(ways_multi_line_string, MultiLineString)
        else MultiLineString([ways_multi_line_string])
    )

    start_point = ImmutablePoint(-1.320715, 50.696457)
    end_point = ImmutablePoint(-0.170461, 51.324368)  # LONDON
    # end_point = ImmutablePoint(-1.159577, 50.73947)  # FERRY
    # end_point = ImmutablePoint(-1.299863, 50.701102)  # SMALL
    # end_point = ImmutablePoint(-1.31873, 50.696209)  # TINY

    if recompute:
        route_multi_line_string = create_route(features, start_point, end_point)
        store_route(route_name, route_multi_line_string)
        route_lines = list(route_multi_line_string.geoms)
        _start_point = Point(*route_lines[0].coords[0])
        _end_point = Point(*route_lines[-1].coords[-1])
        assert start_point == start_point
        assert end_point == end_point
    else:
        route_multi_line_string = load_route(route_name)

    map_plotter = MapPlotter()
    map_plotter.plot_multi_line_string("Ways", ways_multi_line_string)
    map_plotter.plot_multi_line_string("Route", route_multi_line_string)
    map_plotter.plot_waypoints("Waypoints", original_waypoints)
    map_plotter.plot_waypoints("Terminating", [start_point, end_point])
    map_plotter.show(route_multi_line_string.centroid)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
