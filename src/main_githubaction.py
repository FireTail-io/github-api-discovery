import datetime
import json
import os
import time
import uuid

import requests

from openapi.validation import parse_resolve_and_validate_openapi_spec
from static_analysis import LANGUAGE_ANALYSERS
from utils import (
    GitHubContext,
    get_api_uuid_from_api_token,
    load_openapi_spec,
    logger,
    upload_api_spec_to_firetail_collection,
    upload_discovered_api_spec_to_firetail,
)


def handler():
    firetail_api_token = os.environ.get("FIRETAIL_API_TOKEN")
    if firetail_api_token is None:
        raise Exception("Missing environment variable 'FIRETAIL_API_TOKEN")
    firetail_api_url = os.environ.get("FIRETAIL_API_URL", "https://api.saas.eu-west-1.prod.firetail.app")
    external_uuids = []
    last_time = time.time()
    context = os.environ.get("CONTEXT")
    if context:
        context = get_context(context)

    # If API_SPEC_LOCATION is set then we upload the OpenAPI spec at that location
    collection_uuid = os.environ.get("COLLECTION_UUID")
    org_uuid = os.environ.get("ORGANIZATION_UUID")
    api_spec_location = os.environ.get("API_SPEC_LOCATION")
    if api_spec_location is None:
        logger.info("API_SPEC_LOCATION is not set, skipping direct upload step.")
    elif collection_uuid is None:
        logger.info("COLLECTION_UUID is not set, skipping direct upload step.")
    else:
        # If we have a CONTEXT then we can add the API_SPEC_LOCATION to the file_urls
        if context is not None:
            context.file_urls.append(api_spec_location)

        openapi_spec = load_openapi_spec(api_spec_location)
        external_id = str(uuid.uuid4())
        upload_api_spec_to_firetail_collection(
            openapi_spec=openapi_spec,
            context=context,
            collection_uuid=collection_uuid,
            firetail_api_url=firetail_api_url,
            firetail_api_token=firetail_api_token,
            external_id=external_id,
        )
        last_time = time.time()
        external_uuids.append(external_id)
        logger.info(f"Successfully uploaded OpenAPI spec to Firetail: {api_spec_location}")

    static_analysis_root_dir = os.environ.get("STATIC_ANALYSIS_ROOT_DIR", "/")
    static_analysis_languages = map(
        lambda v: v.strip(), os.environ.get("STATIC_ANALYSIS_LANGUAGES", "Python,Golang,Javascript").split(",")
    )
    logger.info(f"Statically analysing files under {static_analysis_root_dir}...")
    for path, _, filenames in os.walk(static_analysis_root_dir):
        for filename in filenames:
            full_path = f"{path}/{filename}"
            logger.info(f"Statically analysing {full_path}...")
            try:
                file_contents = open(full_path, "r").read()
            except Exception as e:  # noqa: E722
                logger.critical(f"{full_path}: Could not read, exception: {e}")
                continue
            # Check if the file is an openapi spec first. If it is, there's no point doing expensive static analysis.
            openapi_spec = parse_resolve_and_validate_openapi_spec(full_path, lambda: file_contents)
            if openapi_spec is not None:
                logger.info(f"{full_path}: Detected OpenAPI spec, uploading to Firetail...")
                external_uuid = str(uuid.uuid4())
                upload_discovered_api_spec_to_firetail(
                    source=full_path,
                    openapi_spec=openapi_spec,
                    api_uuid=get_api_uuid_from_api_token(firetail_api_token),
                    firetail_api_url=firetail_api_url,
                    firetail_api_token=firetail_api_token,
                    external_id=external_uuid,
                )
                external_uuids.append(external_uuid)
                last_time = time.time()
                continue

            for language, language_analysers in LANGUAGE_ANALYSERS.items():
                if language not in static_analysis_languages:
                    continue

                for language_analyser in language_analysers:
                    _, openapi_specs_from_analysis = language_analyser(full_path, file_contents)
                    for openapi_spec_source, openapi_spec in openapi_specs_from_analysis.items():
                        logger.info(f"{full_path}: Created OpenAPI spec via {language} static analysis...")
                        external_uuid = str(uuid.uuid4())
                        upload_discovered_api_spec_to_firetail(
                            source=openapi_spec_source,
                            openapi_spec=openapi_spec,
                            api_uuid=get_api_uuid_from_api_token(firetail_api_token),
                            firetail_api_url=firetail_api_url,
                            firetail_api_token=firetail_api_token,
                            external_id=external_uuid,
                        )
                        external_uuids.append(external_uuid)
                        last_time = time.time()

    if not external_uuids:
        # We don't have anything else to check, just return.
        return
    # We have external IDs now check for finding counts
    wait_time = 60  # TODO: make this configurable
    while True:
        # we loop until we have elapsed the timeout
        if (time.time() - last_time) > wait_time:
            break

    for ex_id in external_uuids:
        if findings_breach_threshold(ex_id, org_uuid, firetail_api_token):
            raise "Error - This action found errors with your spec"


def get_context(context):
    context = json.loads(context)
    return GitHubContext(
        sha=context.get("sha", ""),
        repositoryId=context.get("repository_id", ""),
        repositoryName=context.get("event", {}).get("repository", {}).get("name", ""),
        repositoryOwner=context.get("repository_owner", ""),
        ref=context.get("ref", ""),
        headCommitUsername=context.get("event", {}).get("head_commit", {}).get("author", {}).get("username", ""),
        actor=context.get("actor", ""),
        actorId=context.get("actor_id", ""),
        workflowRef=context.get("workflow_ref", ""),
        eventName=context.get("event_name", ""),
        private=context.get("event", {}).get("repository", {}).get("private"),
        runId=context.get("run_id"),
        timeTriggered=int(time.time() * 1000 * 1000),
        timeTriggeredUTCString=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        file_urls=[],
    )


def get_thresholds() -> dict:
    critical = os.environ.get("CRITICAL_FINDING_THRESHOLD", 1)
    high = os.environ.get("HIGH_FINDING_THRESHOLD", 1)
    medium = os.environ.get("MEDIUM_FINDING_THRESHOLD", 4)
    low = os.environ.get("LOW_FINDING_THRESHOLD", 10)
    return {"CRITICAL": critical, "HIGH": high, "MEDIUM": medium, "LOW": low}


def findings_breach_threshold(ex_id: str, org_uuid: str, api_token: str):
    endpoint = f"/organisations/{org_uuid}/events/external-id/{ex_id}"
    event_resp = requests.get(endpoint, headers={"x-ft-api-key": api_token, "Content-Type": "application/json"})
    if event_resp.status_code != 200:  # pragma: nocover
        print("ERROR", {"message": "Non 200 response from events", "resp": event_resp})
    thresholds = get_thresholds()
    findings = event_resp.get("initialFindingSeverities", {})
    for level, limit in thresholds.items():
        if findings.get(level, 0) > limit:
            raise Exception(f"Findings breached limit: {findings}")


if __name__ == "__main__":
    handler()
