from typing import List, Tuple, Iterator

import operator
import itertools

from shapely.geometry import Point, LineString, MultiLineString

import plotly.express
import plotly.graph_objects


def get_lat_lon(coords: Iterator[Tuple[float, float]]):
    coords_a, coords_b = itertools.tee(coords, 2)
    get_lon, get_lat = operator.itemgetter(0), operator.itemgetter(1)
    return dict(lon=list(map(get_lon, coords_a)), lat=list(map(get_lat, coords_b)))


class MapPlotter:

    figure: plotly.graph_objects.Figure

    def __init__(self):
        self.figure = plotly.graph_objects.Figure()

    def plot_multi_line_string(self, name: str, multi_line_string: MultiLineString):
        coords = itertools.chain(*[line.coords for line in multi_line_string])
        self._add_scattermapbox(name=name, mode="lines", **get_lat_lon(coords))

    def plot_waypoints(self, name: str, waypoints: List[Point]):
        coords = map(lambda point: (point.x, point.y), waypoints)
        self._add_scattermapbox(name=name, mode="markers", **get_lat_lon(coords))

    def show(self, center: Point):
        self.figure.update_layout(
            mapbox={
                "center": {"lon": center.x, "lat": center.y},
                "style": "stamen-terrain",
                "zoom": 10,
            }
        )
        self.figure.show()

    def _add_scattermapbox(self, **kwargs):
        trace = plotly.graph_objects.Scattermapbox(**kwargs)
        self.figure.add_trace(trace)


def plot_multi_line_string(multi_line_string: MultiLineString):
    map_plotter = MapPlotter()
    map_plotter.plot_multi_line_string("Ways", multi_line_string)
    waypoints = [Point(line.coords[0]) for line in multi_line_string]
    map_plotter.plot_waypoints("Waypoints", waypoints)
    map_plotter.show(multi_line_string.centroid)


def main():
    plot_multi_line_string(
        MultiLineString(
            (
                ((-0.127758, 51.507351), (-0.062218, 51.521301)),
                ((-0.062218, 51.521301), (-0.103056, 51.540096)),
            )
        )
    )


if __name__ == "__main__":
    main()
