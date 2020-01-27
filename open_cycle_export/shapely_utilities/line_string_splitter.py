from typing import List

import shapely.ops

from shapely.geometry.base import BaseGeometry
from shapely.geometry import Point, MultiPoint, LineString, MultiLineString


def filter_contained_points(line: LineString, points: List[Point]) -> List[Point]:
    return [point for point in points if line.contains(point)]


def split_line_at_points(line: LineString, points: List[Point]):
    "Reccursively split the line at all the break points"

    contained_points = filter_contained_points(line, points)
    if len(contained_points) < 1:
        return [line]

    split_lines = []
    break_point = contained_points[0]
    line_segments = shapely.ops.split(line, break_point)
    for line_segment in line_segments:
        remaining_points = contained_points[1:]
        segment_split_lines = split_line_at_points(line_segment, remaining_points)
        split_lines.extend(segment_split_lines)
    return split_lines


def extract_line_points(line_string: LineString) -> List[Point]:
    return [Point(*line_string.coords[0]), Point(*line_string.coords[-1])]


def find_intersection_points(
    intersection_geometries: List[BaseGeometry],
) -> List[Point]:
    intersection_points: List[Point] = []
    for intersection_geometry in intersection_geometries:
        if isinstance(intersection_geometry, Point):
            intersection_points.append(intersection_geometry)
        elif isinstance(intersection_geometry, MultiPoint):
            intersection_points.extend(list(intersection_geometry))
        elif isinstance(intersection_geometry, LineString):
            intersection_points.extend(extract_line_points(intersection_geometry))
        elif isinstance(intersection_geometry, MultiLineString):
            for line_string in intersection_geometry:
                intersection_points.extend(extract_line_points(line_string))
        else:
            geometry_type = type(intersection_geometry)
            raise ValueError("Instance {} not valid intersection".format(geometry_type))
    return intersection_points


def split_line_by_intersecting_lines(
    line: LineString, intersecting_lines: List[LineString]
) -> List[LineString]:
    # pretty_geometry_print("line", line)
    # pretty_geometry_print("intersecting_lines", intersecting_lines)
    intersection_geometries = map(line.intersection, intersecting_lines)
    intersection_points = find_intersection_points(intersection_geometries)
    # pretty_geometry_print("intersection_points", intersection_points)
    return split_line_at_points(line, intersection_points)
