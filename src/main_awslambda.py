import time

from scanning import scan
from utils import logger


def handler(event, context):
    logger.info(f"Invoked by event {event} in context {context}")

    start_time = time.time()
    repositories_scanned, openapi_specs_discovered = scan()
    scan_duration = time.time() - start_time

    logger.info(
        f"Scanned {repositories_scanned} repositories. "
        f"{openapi_specs_discovered} OpenAPI spec(s) discovered. "
        f"Scan took {round(scan_duration, ndigits=3)} second(s)"
    )

    return {
        "message": "Scan complete",
        "repositories_scanned": list(repositories_scanned),
        "openapi_specs_discovered": openapi_specs_discovered,
        "scan_duration": scan_duration,
    }
