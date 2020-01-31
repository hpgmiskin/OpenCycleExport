from typing import List, Tuple

import logging

import shapely.geometry
from shapely.geometry import Point, LineString, Polygon, MultiLineString

from open_cycle_export.map_builder.map_plotter import MapPlotter

from open_cycle_export.route_downloader.download_cycle_route import download_cycle_route

logger = logging.getLogger(__name__)

DORKING_ONE_WAY = [
    [-0.3257845, 51.2368652],
    [-0.3257014, 51.2362128],
    [-0.3247304, 51.2362649],
    [-0.3247157, 51.2364504],
    [-0.3247398, 51.236898],
    [-0.3257845, 51.2368652],
]

PETERSFIELD_ROUNDABOUT = [
    [-0.9434456, 50.9970774],
    [-0.9435448, 50.9966503],
    [-0.9427268, 50.9966385],
    [-0.9427429, 50.9970774],
    [-0.9434456, 50.9970774],
]

PORTSMOUTH_HARBOUR = [
    [-1.1104691, 50.8004678],
    [-1.1109412, 50.7951649],
    [-1.0973156, 50.7950971],
    [-1.0971654, 50.8005085],
    [-1.1104691, 50.8004678],
]


def filter_lines(lines: List[LineString], polygon: Polygon):
    filtered_lines = []
    for line in lines:
        if polygon.contains(line):
            filtered_lines.append(line)
        elif polygon.intersects(line):
            filtered_lines.append(polygon.intersection(line))
    return filtered_lines


def display_example(
    lines: List[LineString],
    polygon_coordinates: List[Tuple[float, float]],
    zoom: int = 16,
):
    """Display working example"""

    filter_polygon = Polygon(polygon_coordinates)

    lines = filter_lines(lines, filter_polygon)
    ways = MultiLineString(lines)

    map_plotter = MapPlotter()

    for line in lines:
        map_plotter.plot_line_string("Way", line)

    map_plotter.show(ways.centroid, zoom)


def main():
    logger.info("download cycle route 22")
    features = download_cycle_route("England", "ncn", 22)["features"]
    lines = [shapely.geometry.shape(feature["geometry"]) for feature in features]
    display_example(lines, PETERSFIELD_ROUNDABOUT, 19)
    display_example(lines, PORTSMOUTH_HARBOUR, 16)
    display_example(lines, DORKING_ONE_WAY, 18)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
