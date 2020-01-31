from typing import Iterable, Tuple

import logging
import itertools

import gpxpy.gpx

logger = logging.getLogger(__name__)

Coordinate = Tuple[float, float]
Coordinates = Iterable[Coordinate]


def generate_gpx_file(coordinates: Coordinates, elevations: Iterable[float] = []):

    gpx = gpxpy.gpx.GPX()

    # Create first track in our GPX:
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)

    # Create track segment
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    # Add track points
    for iterable_item in itertools.zip_longest(coordinates, elevations):
        ((longitude, latitude), elevation) = iterable_item
        track_point = gpxpy.gpx.GPXTrackPoint(latitude, longitude, elevation)
        gpx_segment.points.append(track_point)

    return gpx.to_xml()
