import time
from typing import Callable, TypeVar
import github
from github import Github as GithubClient


FuncReturnType = TypeVar("FuncReturnType")


def respect_rate_limit(func: Callable[[], FuncReturnType], github_client: GithubClient) -> FuncReturnType:
    while True:
        try:
            return func()

        except github.RateLimitExceededException:
            rate_limit = github_client.get_rate_limit()
            print(f"Rate limited calling {func}, waiting {rate_limit.core} second(s)...")
            time.sleep(rate_limit.core)
