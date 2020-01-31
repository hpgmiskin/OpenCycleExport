import csv
import json
import operator

import requests

from open_cycle_export.route_downloader.query_overpass import query_overpass


def get_area(name: str):
    url = "https://nominatim.openstreetmap.org/search"
    query = "q={}&polygon_geojson=1&limit=1&format=json".format(name.lower())
    results = requests.get("{}?{}".format(url, query)).json()
    coordinates = results[0]["geojson"]["coordinates"]
    return " ".join(["{} {}".format(lat, lon) for (lon, lat) in coordinates])


def find_cycle_routes(area_name: str, min_area_tags: int = 16):

    query = """
        [out:csv("network","id","name","ref";true)];
        (
            area["name"="{area_name}"](if: count_tags() > {min_area_tags});
            area["name:en"="{area_name}"](if: count_tags() > {min_area_tags});
        )->.searchArea;
        (
            relation["route"="bicycle"]["network"="ncn"]["ref"](area.searchArea);
        );
        out;
    """.format(
        area_name=area_name, min_area_tags=min_area_tags
    )

    return query_overpass(query, build=False)


def store_cycle_routes(area_name):
    cycle_routes = find_cycle_routes(area_name)
    network_refs = list(set([(item[0], item[3]) for item in cycle_routes[1:]]))
    network_refs = sorted(network_refs, key=lambda item: "".join(item))
    filename = "data/{}_cycle_routes.csv".format(area_name.lower())
    with open(filename, "w") as open_file:
        csv_writer = csv.writer(open_file)
        csv_writer.writerow(["area", "type", "number"])
        for network_ref in network_refs:
            csv_writer.writerow([area_name, network_ref[0], network_ref[1]])


if __name__ == "__main__":
    store_cycle_routes("France")


# https://wiki.openstreetmap.org/wiki/Overpass_turbo/Extended_Overpass_Turbo_Queries
# https://nominatim.org/release-docs/develop/api/Search/
