import json

import shapely.ops
import shapely.geometry

from open_cycle_export.route_downloader.query_overpass import query_overpass


def get_coordinates(geometry):
    return [(coordinate["lon"], coordinate["lat"]) for coordinate in geometry]


def get_first_way_coordinates(members):
    for member in members:
        if member["type"] == "way":
            return get_coordinates(member["geometry"])


def download_city_boundaries(search_area):

    query = """
        area["name"="{search_area}"]->.boundaryarea;
        (
            relation(area.boundaryarea)["place"="city"];
        );
    """.format(
        search_area=search_area
    )

    city_data = query_overpass(query, verbosity="geom", responseformat="json")

    return [
        {
            "type": "feature",
            "properties": {
                key: value for key, value in element["tags"].items() if ":" not in key
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": get_first_way_coordinates(element["members"]),
            },
        }
        for element in city_data["elements"]
    ]


if __name__ == "__main__":
    city_features = download_cities("England")
    print(json.dumps(city_features))
