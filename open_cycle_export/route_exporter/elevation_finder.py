from typing import List, Tuple

import re
import json
import logging

import requests

logger = logging.getLogger(__name__)


def find_elevations(coordinates: List[Tuple[float, float]]) -> List[float]:
    endpoint = "https://api.open-elevation.com/api/v1/lookup"
    request = requests.post(
        endpoint,
        {
            "locations": [
                {"latitude": latitude, "longitude": longitude}
                for (longitude, latitude) in coordinates
            ]
        },
    )
    try:
        response = request.json()
        return [result["elevation"] for result in response["results"]]
    except TimeoutError:
        logger.error("Elevation not found - Timeout error")
        return []
    except requests.exceptions.ConnectionError:
        logger.error("Elevation not found - Connection error")
        return []
    except json.decoder.JSONDecodeError:
        error = re.search(r"<title>(.*)</title>", request.text)
        logger.error("Elevation not found - %s", error.group(1))
        return []
