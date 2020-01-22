from shapely.geometry import LineString

import geopandas

# http://geopandas.org/projections.html
# https://spatialreference.org/ref/epsg/27700/


def main():
    lon_lat_series = geopandas.GeoSeries(
        LineString([(-0.127758, 51.507351), (-0.062218, 51.521301)]),
        crs={"epsg": 4326},
    )
    print(lon_lat_series)
    osgb_series = lon_lat_series.to_crs(epsg=27700)
    print(osgb_series)


if __name__ == "__main__":
    main()
