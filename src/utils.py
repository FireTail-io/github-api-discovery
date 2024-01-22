import datetime
import logging
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Callable, TypeVar

import github
import requests
from github import Github as GithubClient

from env import LOGGING_LEVEL
from openapi.validation import parse_resolve_and_validate_openapi_spec

logger = logging.Logger(name="Firetail GitHub Scanner", level=LOGGING_LEVEL)
logger_handler = logging.StreamHandler()
logger_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(logger_handler)

FuncReturnType = TypeVar("FuncReturnType")


@dataclass
class GitHubContext:
    sha: str
    repositoryName: str
    repositoryId: str
    repositoryOwner: str
    ref: str
    headCommitUsername: str
    actor: str
    actorId: str
    workflowRef: str
    eventName: str
    private: bool
    runId: str
    timeTriggered: int
    timeTriggeredUTCString: str
    file_urls: list[str]
    external_id: str


def get_api_uuid_from_api_token(api_token: str) -> str:
    # Using the uuid lib here to make sure it's a valid UUID
    try:
        return str(uuid.UUID("-".join(api_token.split("-")[2:7])))
    except:  # noqa: E722
        raise Exception("Failed to extract API UUID from API token")


def get_spec_type(spec_data: dict) -> str:
    if spec_data.get("openapi", "").startswith("3.1"):
        return "OAS3.1"
    if spec_data.get("swagger"):
        return "SWAGGER2"
    return "OAS3.0"


def load_openapi_spec(api_spec_location: str) -> dict:
    try:
        openapi_spec = parse_resolve_and_validate_openapi_spec(
            api_spec_location, lambda: open(api_spec_location, "r").read()
        )
    except FileNotFoundError:
        raise Exception(f"Could not find OpenAPI spec at {api_spec_location}")
    if openapi_spec is None:
        raise Exception(f"File at {api_spec_location} is not a valid OpenAPI spec")
    return openapi_spec


def get_datestamp() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def respect_rate_limit(func: Callable[[], FuncReturnType], github_client: GithubClient) -> FuncReturnType:
    while True:
        try:
            return func()
        except github.RateLimitExceededException:  # pragma: no cover
            sleep_duration = (github_client.get_rate_limit().core.reset - datetime.datetime.utcnow()).seconds + 1
            logger.warning(
                f"Rate limited calling {func}, core rate limit resets at "
                f"{github_client.get_rate_limit().core.reset.astimezone(datetime.timezone.utc).isoformat()}, "
                f"waiting {sleep_duration} second(s)..."
            )
            time.sleep(sleep_duration)


@dataclass
class FireTailRequestBody:
    collection_uuid: str
    spec_data: dict
    spec_type: str
    context: GitHubContext | None = None


def upload_api_spec_to_firetail_collection(
    openapi_spec: dict,
    context: GitHubContext | None,
    collection_uuid: str,
    firetail_api_url: str,
    firetail_api_token: str,
):
    request_body = {
        "collection_uuid": collection_uuid,
        "spec_data": openapi_spec,
        "spec_type": get_spec_type(openapi_spec),
        "context": asdict(context),
    }
    firetail_api_response = requests.post(
        url=f"{firetail_api_url}/code_repository/spec",
        json=asdict(
            FireTailRequestBody(
                collection_uuid=collection_uuid,
                spec_data=openapi_spec,
                spec_type=get_spec_type(openapi_spec),
                context=context,
            )
        ),
        headers={"x-ft-api-key": firetail_api_token},
    )
    if firetail_api_response.status_code not in {201, 409}:
        raise Exception(f"Failed to send FireTail API Spec. {firetail_api_response.text}")


def upload_discovered_api_spec_to_firetail(
    source: str, openapi_spec: dict, api_uuid: str, firetail_api_url: str, firetail_api_token: str
):
    upload_api_spec_response = requests.post(
        f"{firetail_api_url}/discovery/api-repository/{api_uuid}/appspec",
        headers={
            "x-ft-api-key": firetail_api_token,
            "Content-Type": "application/json",
        },
        json={"source": source, "appspec": openapi_spec},
    )

    if upload_api_spec_response.status_code not in [201, 304]:
        raise Exception(f"Failed to send API Spec to FireTail. {upload_api_spec_response.text}")

    logger.info(
        f"Successfully created/updated {source} API spec in Firetail SaaS, response:"
        f" {upload_api_spec_response.text}"
    )
