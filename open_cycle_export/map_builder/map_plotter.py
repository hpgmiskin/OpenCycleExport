from typing import List

from shapely.geometry import LineString, MultiLineString

import plotly.express
import plotly.graph_objects


def plot_multi_line_string(multi_line_string: MultiLineString):

    origin = plotly.graph_objects.Scattermapbox(
        mode="markers",
        lon=[multi_line_string.centroid.x],
        lat=[multi_line_string.centroid.y],
        marker={"size": 10},
    )
    figure = plotly.graph_objects.Figure(origin)

    for line_string in multi_line_string:
        series = plotly.graph_objects.Scattermapbox(
            mode="lines",
            lon=[coord[0] for coord in line_string.coords],
            lat=[coord[1] for coord in line_string.coords],
        )
        figure.add_trace(series)

    figure.update_layout(
        mapbox={
            "center": {
                "lon": multi_line_string.centroid.x,
                "lat": multi_line_string.centroid.y,
            },
            "style": "stamen-terrain",
            "zoom": 10,
        }
    )

    figure.show()


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
