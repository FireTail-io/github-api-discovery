import datetime
import logging
import time
from typing import Callable, TypeVar

import github
from github import Github as GithubClient

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
            sleep_duration = (datetime.datetime.utcnow() - github_client.get_rate_limit().core.reset).seconds
            logger.warning(f"Rate limited calling {func}, waiting {sleep_duration} second(s)")
            time.sleep(sleep_duration)
