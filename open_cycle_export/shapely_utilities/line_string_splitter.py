from typing import List

import shapely.ops

from shapely.geometry import Point, LineString

from open_cycle_export.shapely_utilities.formatting_tools import pretty_geometry_print


def filter_contained_points(line: LineString, points: List[Point]) -> List[Point]:
    return [point for point in points if line.contains(point)]


def split_line_at_points(line: LineString, points: List[Point]):
    "Reccursively split the line at all the break points"

    contained_points = filter_contained_points(line, points)
    if len(contained_points) < 1:
        return [line]

    split_lines = []
    break_point = contained_points[0]
    for line_segment in shapely.ops.split(line, break_point):
        remaining_points = contained_points[1:]
        segment_split_lines = split_line_at_points(line_segment, remaining_points)
        split_lines.extend(segment_split_lines)
    return split_lines


def split_line_by_intersecting_lines(
    line: LineString, intersecting_lines: List[LineString]
) -> List[LineString]:
    intersection_points = map(line.intersection, intersecting_lines)
    return split_line_at_points(line, intersection_points)
