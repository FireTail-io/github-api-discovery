import time
from scan import scan
from utils import logger


def handler(event, context):
    logger.info(f"Invoked by event {event} in context {context}")

    start_time = time.time()
    repositories_scanned, openapi_specs_discovered = scan()
    scan_duration = time.time() - start_time

    logger.info(f"scan() returned in {round(scan_duration, ndigits=3)} second(s)")

    return {
        "message": "Scan complete",
        "repositories_scanned": repositories_scanned,
        "openapi_specs_discovered": openapi_specs_discovered,
        "scan_duration": scan_duration
    }
