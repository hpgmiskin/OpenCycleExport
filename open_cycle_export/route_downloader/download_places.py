import json

from open_cycle_export.route_downloader.query_overpass import query_overpass


def download_places(search_area, places=["town", "city"]):

    search_area = "United Kingdom" if search_area == "Great Britain" else search_area

    query = """
        area["name"="{search_area}"]->.boundaryarea;
        (
            node["place"~"{place_query}"](area.boundaryarea);
        );
    """.format(
        search_area=search_area, place_query="|".join(places)
    )

    return query_overpass(query, "geom")


if __name__ == "__main__":
    # places = download_places("Isle of Wight")
    places = download_places("United Kingdom")
    print([feature["properties"]["name"] for feature in places["features"]])
    # print(json.dumps(places, indent=4))
