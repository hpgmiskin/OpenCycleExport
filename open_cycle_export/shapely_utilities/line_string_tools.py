from shapely.geometry import LineString


def reverse_line_string(line_string: LineString):
    return LineString(line_string.coords[-1::-1])
