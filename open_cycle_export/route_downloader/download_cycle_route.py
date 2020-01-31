import json

from open_cycle_export.route_downloader.query_overpass import query_overpass


def download_cycle_route(area_name, cycle_network, route_number, min_area_tags=16):

    query = """
        (
            area["name"="{area_name}"](if: count_tags() > {min_area_tags});
            area["name:en"="{area_name}"](if: count_tags() > {min_area_tags});
        )->.searchArea;
        (
            relation
                ["route"="bicycle"]
                ["network"="{cycle_network}"]
                ["ref"="{route_number}"]
                (area.searchArea);
            way(r);
        );
    """.format(
        area_name=area_name,
        cycle_network=cycle_network,
        route_number=route_number,
        min_area_tags=min_area_tags,
    )

    return query_overpass(query, "geom")


if __name__ == "__main__":
    cycle_route_data = download_cycle_route("England", "ncn", 22)
    print(json.dumps(cycle_route_data, indent=4))
