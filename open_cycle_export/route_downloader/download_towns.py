import json

from open_cycle_export.route_downloader.query_overpass import query_overpass


def download_towns(search_area):

    query = """
        area["name"="{search_area}"]->.boundaryarea;
        (
            node(area.boundaryarea)["place"="town"];
        );
    """.format(
        search_area=search_area
    )

    return query_overpass(query, "geom")


if __name__ == "__main__":
    town_nodes = download_towns("Gloucestershire")
    print(json.dumps(town_nodes, indent=4))
