import base64

import github
import requests
from github import Github as GithubClient
from github.ContentFile import ContentFile as GithubContentFile
from github.GithubException import GithubException
from github.Repository import Repository as GithubRepository

from config import Config, OrgConfig, UserConfig  # type: ignore
from openapi.validation import parse_resolve_and_validate_openapi_spec
from static_analysis import ANALYSER_TYPE, get_language_analysers
from utils import logger, respect_rate_limit


def scan_file(
    file: GithubContentFile, github_client: GithubClient, language_analysers: list[ANALYSER_TYPE]
) -> tuple[set[str], dict[str, dict]]:
    file_path = respect_rate_limit(lambda: file.path, github_client)

    def get_file_contents():
        encoded_content = respect_rate_limit(lambda: file.content, github_client)
        if encoded_content is None:
            return ""
        return base64.b64decode(encoded_content)

    openapi_specs_discovered: dict[str, dict] = {}
    frameworks_identified: set[str] = set()

    valid_openapi_spec = parse_resolve_and_validate_openapi_spec(file.path, get_file_contents)

    if valid_openapi_spec is not None:
        openapi_specs_discovered[file_path] = valid_openapi_spec

    for language_analyser in language_analysers:
        frameworks, openapi_spec_from_analysis = language_analyser(file_path, get_file_contents())
        frameworks_identified.update(frameworks)
        openapi_specs_discovered = {**openapi_specs_discovered, **openapi_spec_from_analysis}

    return frameworks_identified, openapi_specs_discovered


def scan_repository_contents_recursive(
    repository: GithubRepository,
    github_client: GithubClient,
    language_analysers,
    path: str = "",
) -> tuple[set[str], dict[str, dict]]:
    frameworks_identified: set[str] = set()
    openapi_specs_discovered: dict[str, dict] = {}

    IGNORED_FILE_PATH_PREFIXES = (
        ".github",
        "__test",
        "test",
        "tests",
        ".env",
        "node_modules/",
        "example",
        ".pytest_cache/",
        ".coverage",
    )
    if path.startswith(IGNORED_FILE_PATH_PREFIXES):
        return set(), {}

    IGNORED_FILE_PATH_SUBSTRINGS = ["test/"]
    if any([ignored_file_path in path for ignored_file_path in IGNORED_FILE_PATH_SUBSTRINGS]):
        return set(), {}

    repository_contents = respect_rate_limit(lambda: repository.get_contents(path), github_client)
    if not isinstance(repository_contents, list):
        repository_contents = [repository_contents]
    logger.info(f"{repository.full_name}: Scanning {len(repository_contents)} file(s) in /{path}")

    for file in repository_contents:
        if file.type == "dir":
            new_frameworks_identified, new_openapi_specs_discovered = scan_repository_contents_recursive(
                repository, github_client, language_analysers, path=file.path
            )
        else:
            try:
                new_frameworks_identified, new_openapi_specs_discovered = scan_file(
                    file, github_client, language_analysers
                )
            except github.GithubException as exception:
                logger.warning(
                    f"Failed to scan file {file.path} from {repository.full_name}, exception raised: {exception}"
                )
                continue

        frameworks_identified.update(new_frameworks_identified)
        openapi_specs_discovered = {**openapi_specs_discovered, **new_openapi_specs_discovered}

    return frameworks_identified, openapi_specs_discovered


def scan_repository_contents(
    github_client: GithubClient, repository: GithubRepository
) -> tuple[set[str], dict[str, dict]]:
    repository_languages = list(respect_rate_limit(repository.get_languages, github_client).keys())
    logger.info(f"{repository.full_name}: Language(s) detected: {', '.join(repository_languages)}")

    language_analysers = get_language_analysers(repository_languages)
    logger.info(f"{repository.full_name}: Got {len(language_analysers)} language analyser(s)")

    return scan_repository_contents_recursive(repository, github_client, language_analysers)


def scan_repository(
    github_client: GithubClient, repo: GithubRepository, firetail_app_token: str, firetail_api_url: str
):
    logger.info(f"{repo.full_name}: Scanning {repo.html_url}")

    try:
        frameworks_identified, openapi_specs_discovered = scan_repository_contents(github_client, repo)

    except github.GithubException as exception:
        logger.warning(f"{repo.full_name}: Failed to scan, exception raised: {exception}")
        return

    logger.info(f"{repo.full_name}: {len(frameworks_identified)} frameworks identified.")

    if len(openapi_specs_discovered) == 0:
        logger.info(f"{repo.full_name}: Scan complete. No APIs discovered.")
        return

    logger.info(
        f"{repo.full_name}: Scan complete. {len(openapi_specs_discovered)} OpenAPI API(s) discovered or"
        " generated from static analysis."
    )
    create_api_response = requests.post(
        f"{firetail_api_url}/discovery/api-repository",
        headers={
            "x-ft-app-key": firetail_app_token,
            "Content-Type": "application/json",
        },
        json={
            "full_name": repo.full_name,
            "id": f"github:{repo.id}",
        },
    )
    if create_api_response.status_code != 200:
        logger.critical(f"{repo.full_name}: Failed to create API in SaaS, response: {create_api_response.text}")
        return

    logger.info(
        f"{repo.full_name}: Successfully created/updated API in Firetail SaaS, response:"
        f" {create_api_response.text}"
    )

    api_uuid = create_api_response.json()["api"]["UUID"]

    for source, openapi_spec in openapi_specs_discovered.items():
        upload_api_spec_response = requests.post(
            f"{firetail_api_url}/discovery/api-repository/{api_uuid}/appspec",
            headers={
                "x-ft-app-key": firetail_app_token,
                "Content-Type": "application/json",
            },
            json={
                "source": source,
                "appspec": openapi_spec,
            },
        )

        if upload_api_spec_response.status_code not in [201, 304]:
            logger.critical(
                f"{repo.full_name}: Failed to upload OpenAPI spec {source} to SaaS, response:"
                f" {upload_api_spec_response.text}"
            )
            continue

        logger.info(
            f"{repo.full_name}: Successfully created/updated {source} API spec in Firetail SaaS, response:"
            f" {upload_api_spec_response.text}"
        )


def get_repositories_of_user(github_client: GithubClient, username: str, config: UserConfig) -> set[GithubRepository]:
    repositories_to_scan = set()

    for repo in github_client.get_user(username).get_repos():
        if not config.skip_repo(repo):
            repositories_to_scan.add(repo)

    return repositories_to_scan


def get_repositories_of_organisation(
    github_client: GithubClient, org_name: str, config: OrgConfig
) -> set[GithubRepository]:
    repositories_to_scan = set()

    try:
        for repo in github_client.get_organization(org_name).get_repos():
            if not config.skip_repo(repo):
                repositories_to_scan.add(repo)
    except GithubException as github_exception:
        if github_exception.status == 403:
            logger.warn(
                f"{org_name}: Received a 403 response from GitHub when listing this organisation's repositories. Your"
                " GitHub token may not have access to this organisation."
            )
        else:
            logger.warn(f"{org_name}: Received a {github_exception.status} response when listing repos.")

    return repositories_to_scan


def scan_with_token(github_token: str, firetail_app_token: str, firetail_api_url: str, config: Config) -> None:
    github_client = github.Github(github_token)
    repositories_to_scan = set()

    # Get all of the repos belonging to users in the config
    for user, user_config in config.users.items():
        repositories_to_scan.update(get_repositories_of_user(github_client, user, user_config))

    # Get all of the repos beloning to orgs in the config
    for organisation, organisation_config in config.organisations.items():
        repositories_to_scan.update(get_repositories_of_organisation(
            github_client, organisation, organisation_config
        ))

    # Filter out any repos which have been explicitly excluded
    repositories_to_scan = set(filter(lambda repo: not config.skip_repo(repo), repositories_to_scan))

    # Get any repos that have been explicitly included
    for repo_name, skip_or_include in config.repositories.items():
        if skip_or_include != "include":
            continue

        try:
            repo = github_client.get_repo(repo_name)
        except GithubException as github_exception:
            match github_exception.status:
                case 403:
                    logger.warn(
                        f"{repo_name}: Received a 403 response from GitHub when attempting to get this repository. Your"
                        " token may not have access to this repository."
                    )
                case _:
                    logger.warn(f"{repo_name}: Received a {github_exception.status} response when getting repo")
            continue

        if repo is not None:
            repositories_to_scan.add(repo)

    if len(repositories_to_scan) == 0:
        logger.info("Could not find any repositories to scan. Check your config file and token's permissions.")
        return

    logger.info(
        f"Attempting to scan {len(repositories_to_scan)} "
        f"{'repositories' if len(repositories_to_scan) > 1 else 'repository'}: " +
        ", ".join([repo.full_name for repo in repositories_to_scan])
    )

    for repo in repositories_to_scan:
        scan_repository(github_client, repo, firetail_app_token, firetail_api_url)
