# src/get_num_square.py
import datetime
import json
import os
import time
import uuid

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

    context = os.environ.get("CONTEXT")
    if context:
        context = json.loads(context)
        context = GitHubContext(
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

    # If API_SPEC_LOCATION is set then we upload the OpenAPI spec at that location
    collection_uuid = os.environ.get("COLLECTION_UUID")
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

        upload_api_spec_to_firetail_collection(
            openapi_spec=openapi_spec,
            context=context,
            collection_uuid=collection_uuid,
            firetail_api_url=firetail_api_url,
            firetail_api_token=firetail_api_token,
        )

        logger.info(f"Successfully uploaded OpenAPI spec to Firetail: {api_spec_location}")

    static_analysis_root_dir = os.environ.get("STATIC_ANALYSIS_ROOT_DIR", "/")
    static_analysis_languages = map(
        lambda v: v.strip(), os.environ.get("STATIC_ANALYSIS_LANGUAGES", "Python,Golang,Javascript").split(",")
    )

    logger.info(f"Statically analysing files under {static_analysis_root_dir}...")
    external_uuids = []
    last_time = time.time()
    for path, _, filenames in os.walk(static_analysis_root_dir):
        for filename in filenames:
            full_path = f"{path}/{filename}"
            logger.info(f"Statically analysing {full_path}...")

            try:
                file_contents = open(full_path, "r").read()
            except Exception as e:  # noqa: E722
                logger.critical(f"{full_path}: Could not read, exception: {e}")
                continue
            last_time = time.time()
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
                    external_uuid=external_uuid,
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
                            external_uuid=external_uuid,
                        )
                        external_uuids.append(external_uuid)
                        last_time = time.time()

    if external_uuids == []:
        return
    # We have external IDs now check for finding counts
    wait_time = 60
    while True:
        # we loop until we have elapsed the timeout
        if (time.time() - last_time) > wait_time:
            break
    for ex_id in external_uuids:
        if has_findings_over_x(ex_id):
            raise "Error - This action found errors with your spec"


def has_findings_over_x(ex_ID):
    pass


if __name__ == "__main__":
    handler()
