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


def download_city_boundaries(area_name, min_area_tags=16):

    query = """
        (
            area["name"="{area_name}"](if: count_tags() > {min_area_tags});
            area["name:en"="{area_name}"](if: count_tags() > {min_area_tags});
        )->.searchArea;
        (
            area(area.searchArea)["place"="city"];
        );
    """.format(
        area_name=area_name, min_area_tags=min_area_tags
    )

    return query_overpass(query)

    # return [
    #     {
    #         "type": "feature",
    #         "properties": {
    #             key: value for key, value in element["tags"].items() if ":" not in key
    #         },
    #         "geometry": {
    #             "type": "Polygon",
    #             "coordinates": get_first_way_coordinates(element["members"]),
    #         },
    #     }
    #     for element in city_data["elements"]
    # ]


if __name__ == "__main__":
    city_features = download_city_boundaries("Gloucestershire")
    print(json.dumps(city_features))
