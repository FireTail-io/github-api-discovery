import time
from scanning import scan
from utils import logger


def handler():
    start_time = time.time()
    repositories_scanned, openapi_specs_discovered = scan()
    scan_duration = time.time() - start_time

    logger.info(
        f"Scanned {repositories_scanned} repositories. "
        f"{openapi_specs_discovered} OpenAPI spec(s) discovered. "
        f"Scan took {round(scan_duration, ndigits=3)} second(s)"
    )


handler()
