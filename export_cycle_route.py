import logging

from open_cycle_export.route_downloader.download_cycle_route import download_cycle_route
from open_cycle_export.route_processor.route_processor import create_route

logger = logging.getLogger(__name__)


def main():
    route_data = download_cycle_route("United Kingdom", "ncn", 22)
    logger.info("downloaded %s features", len(route_data["features"]))
    segments = create_route(route_data["features"])
    logger.info("found %s segments", len(segments))
    print(segments)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
