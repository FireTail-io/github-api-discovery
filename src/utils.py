import datetime
import logging
import time
from typing import Callable, TypeVar

import github
from github import Github as GithubClient
import requests

from env import LOGGING_LEVEL

logger = logging.Logger(name="Firetail GitHub Scanner", level=LOGGING_LEVEL)
logger_handler = logging.StreamHandler()
logger_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(logger_handler)

FuncReturnType = TypeVar("FuncReturnType")


def get_datestamp() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def respect_rate_limit(func: Callable[[], FuncReturnType], github_client: GithubClient) -> FuncReturnType:
    while True:
        try:
            return func()

        except github.RateLimitExceededException:
            sleep_duration = (github_client.get_rate_limit().core.reset - datetime.datetime.utcnow()).seconds + 1
            logger.warning(
                f"Rate limited calling {func}, core rate limit resets at "
                f"{github_client.get_rate_limit().core.reset.astimezone(datetime.timezone.utc).isoformat()}, "
                f"waiting {sleep_duration} second(s)..."
            )
            time.sleep(sleep_duration)


def upload_api_spec_to_firetail(
    source: str, openapi_spec: str, api_uuid: str, firetail_api_url: str, firetail_api_token: str
):
    upload_api_spec_response = requests.post(
        f"{firetail_api_url}/discovery/api-repository/{api_uuid}/appspec",
        headers={
            "x-ft-api-key": firetail_api_token,
            "Content-Type": "application/json",
        },
        json={
            "source": source,
            "appspec": openapi_spec,
        },
    )

    if upload_api_spec_response.status_code not in [201, 304]:
        raise Exception(f"Failed to send API Spec to FireTail. {upload_api_spec_response.text}")

    logger.info(
        f"Successfully created/updated {source} API spec in Firetail SaaS, response:"
        f" {upload_api_spec_response.text}"
    )
