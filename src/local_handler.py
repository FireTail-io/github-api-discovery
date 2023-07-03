import time
from scanning import scan
from utils import logger


def handler():
    start_time = time.time()
    repositories_scanned, openapi_specs_discovered = scan()
    scan_duration = time.time() - start_time

    if len(repositories_scanned) == 0:
        logger.warn(
            f"Scanned 0 repositories. Check your config.yml & access token permissions. "
            f"Scan took {round(scan_duration, ndigits=3)} second(s)"
        )
        return

    logger.info(
        f"Scanned {len(repositories_scanned)} repositories: {', '.join(repositories_scanned)}. "
        f"{openapi_specs_discovered} OpenAPI spec(s) discovered. "
        f"Scan took {round(scan_duration, ndigits=3)} second(s)"
    )


handler()
