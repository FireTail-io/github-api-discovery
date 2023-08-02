# src/get_num_square.py
import os
import datetime
from dataclasses import dataclass, asdict
import requests
import time
import json

from openapi.validation import parse_resolve_and_validate_openapi_spec
from static_analysis import LANGUAGE_ANALYSERS
from utils import upload_api_spec_to_firetail, logger


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


@dataclass
class FireTailRequestBody:
    collection_uuid: str
    spec_data: dict
    spec_type: str
    context: GitHubContext | None = None


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
        # TODO: a much more helpful error message here
        raise Exception(f"File at {api_spec_location} is not a valid OpenAPI spec")
    return openapi_spec


def handler():
    FIRETAIL_API_TOKEN = os.environ.get("FIRETAIL_API_TOKEN")
    if FIRETAIL_API_TOKEN is None:
        raise Exception("Missing environment variable 'FIRETAIL_API_TOKEN")
    FIRETAIL_API_URL = os.environ.get("FIRETAIL_API_URL", "https://api.saas.eu-west-1.prod.firetail.app")

    CONTEXT = os.environ.get("CONTEXT")
    if CONTEXT is not None:
        CONTEXT = json.loads(CONTEXT)
        CONTEXT = GitHubContext(
            sha=CONTEXT.get("sha", ""),
            repositoryId=CONTEXT.get("repository_id", ""),
            repositoryName=CONTEXT.get("event", {}).get("repository", {}).get("name", ""),
            repositoryOwner=CONTEXT.get("repository_owner", ""),
            ref=CONTEXT.get("ref", ""),
            headCommitUsername=CONTEXT.get("event", {}).get("head_commit", {}).get("author", {}).get("username", ""),
            actor=CONTEXT.get("actor", ""),
            actorId=CONTEXT.get("actor_id", ""),
            workflowRef=CONTEXT.get("workflow_ref", ""),
            eventName=CONTEXT.get("event_name", ""),
            private=CONTEXT.get("event", {}).get("repository", {}).get("private"),
            runId=CONTEXT.get("run_id"),
            timeTriggered=int(time.time() * 1000 * 1000),
            timeTriggeredUTCString=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            file_urls=[],
        )

    # If API_SPEC_LOCATION is set then we upload the OpenAPI spec at that location
    COLLECTION_UUID = os.environ.get("COLLECTION_UUID")
    API_SPEC_LOCATION = os.environ.get("API_SPEC_LOCATION")
    if API_SPEC_LOCATION is None:
        logger.info("API_SPEC_LOCATION is not set, skipping direct upload step.")
    elif COLLECTION_UUID is None:
        logger.info("COLLECTION_UUID is not set, skipping direct upload step.")
    else:
        # If we have a CONTEXT then we can add the API_SPEC_LOCATION to the file_urls
        if CONTEXT is not None:
            CONTEXT.file_urls.append(API_SPEC_LOCATION)

        OPENAPI_SPEC = load_openapi_spec(API_SPEC_LOCATION)

        FIRETAIL_API_RESPONSE = requests.post(
            url=f"{FIRETAIL_API_URL}/code_repository/spec",
            json=asdict(
                FireTailRequestBody(
                    collection_uuid=COLLECTION_UUID,
                    spec_data=OPENAPI_SPEC,
                    spec_type=get_spec_type(OPENAPI_SPEC),
                    context=CONTEXT,
                )
            ),
            headers={"x-ft-api-key": FIRETAIL_API_TOKEN},
        )
        if FIRETAIL_API_RESPONSE.status_code not in {201, 409}:
            raise Exception(f"Failed to send FireTail API Spec. {FIRETAIL_API_RESPONSE.text}")

        logger.info(f"Successfully uploaded OpenAPI spec to Firetail: {API_SPEC_LOCATION}")

    API_UUID = os.environ.get("API_UUID")
    if API_UUID is None:
        logger.info("API_UUID is not set, skipping static analysis step.")
        return

    STATIC_ANALYSIS_ROOT_DIR = os.environ.get("STATIC_ANALYSIS_ROOT_DIR", "/")
    STATIC_ANALYSIS_LANGUAGES = map(
        lambda v: v.strip(), os.environ.get("STATIC_ANALYSIS_LANGUAGES", "Python,Golang,Javascript").split(",")
    )

    logger.info(f"Statically analysing files under {STATIC_ANALYSIS_ROOT_DIR}...")

    for path, _, filenames in os.walk(STATIC_ANALYSIS_ROOT_DIR):
        for filename in filenames:
            FULL_PATH = f"{path}/{filename}"
            logger.info(f"Statically analysing {FULL_PATH}...")

            try:
                FILE_CONTENTS = open(FULL_PATH, "r").read()
            except Exception as e:  # noqa: E722
                logger.critical(f"{FULL_PATH}: Could not read, exception: {e}")
                continue

            # Check if the file is an openapi spec first. If it is, there's no point doing expensive static analysis.
            OPENAPI_SPEC = parse_resolve_and_validate_openapi_spec(FULL_PATH, lambda: FILE_CONTENTS)
            if OPENAPI_SPEC is not None:
                logger.info(f"{FULL_PATH}: Detected OpenAPI spec, uploading to Firetail...")
                upload_api_spec_to_firetail(
                    source=FULL_PATH,
                    openapi_spec=json.dumps(OPENAPI_SPEC, indent=2),
                    api_uuid=API_UUID,
                    firetail_api_url=FIRETAIL_API_URL,
                    firetail_api_token=FIRETAIL_API_TOKEN,
                )
                continue

            for language, language_analysers in LANGUAGE_ANALYSERS.items():
                if language not in STATIC_ANALYSIS_LANGUAGES:
                    continue

                for language_analyser in language_analysers:
                    _, openapi_specs_from_analysis = language_analyser(FULL_PATH, FILE_CONTENTS)

                    for openapi_spec_source, OPENAPI_SPEC in openapi_specs_from_analysis.items():
                        logger.info(f"{FULL_PATH}: Created OpenAPI spec via {language} static analysis...")
                        upload_api_spec_to_firetail(
                            source=openapi_spec_source,
                            openapi_spec=json.dumps(OPENAPI_SPEC, indent=2),
                            api_uuid=API_UUID,
                            firetail_api_url=FIRETAIL_API_URL,
                            firetail_api_token=FIRETAIL_API_TOKEN,
                        )


if __name__ == "__main__":
    handler()
