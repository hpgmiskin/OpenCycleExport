import json

from open_cycle_export.route_downloader.query_overpass import query_overpass


def download_places(area_name, places=["town", "city"], min_area_tags=16):

    area_name = "United Kingdom" if area_name == "Great Britain" else area_name

    query = """
        (
            area["name"="{area_name}"](if: count_tags() > {min_area_tags});
            area["name:en"="{area_name}"](if: count_tags() > {min_area_tags});
        )->.searchArea;
        (
            node["place"~"{place_query}"](area.searchArea);
        );
    """.format(
        area_name=area_name, place_query="|".join(places), min_area_tags=min_area_tags
    )

    return query_overpass(query, "geom")


if __name__ == "__main__":
    places = download_places("Isle of Wight")
    # places = download_places("Great Britain")
    # places = download_places("United Kingdom")
    print([feature["properties"]["name"] for feature in places["features"]])
    # print(json.dumps(places, indent=4))
