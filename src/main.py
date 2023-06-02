import base64
import github
from github import Github as GithubClient
from github.ContentFile import ContentFile as GithubContentFile
from github.Repository import Repository as GithubRepository
import requests

from env import FIRETAIL_API_URL, FIRETAIL_APP_TOKEN, GITHUB_TOKEN
from openapi.validation import parse_resolve_and_validate_openapi_spec
from static_analysis import ANALYSER_TYPE, get_language_analysers
from utils import respect_rate_limit


def scan_file(
    file: GithubContentFile, github_client: GithubClient, language_analysers: list[ANALYSER_TYPE]
) -> tuple[set[str], dict[str, str]]:
    file_path = respect_rate_limit(lambda: file.path, github_client)

    def get_file_contents():
        encoded_content = respect_rate_limit(lambda: file.content, github_client)
        if encoded_content is None:
            return ""
        return base64.b64decode(encoded_content)

    openapi_specs_discovered = {}
    frameworks_identified: set[str] = set()

    valid_openapi_spec = parse_resolve_and_validate_openapi_spec(file.path, get_file_contents)

    if valid_openapi_spec is not None:
        openapi_specs_discovered[file_path] = valid_openapi_spec

    for language_analyser in language_analysers:
        frameworks, _ = language_analyser(file_path, get_file_contents())
        frameworks_identified.update(frameworks)

    return frameworks_identified, openapi_specs_discovered


def scan_repository_recursive(
    repository: GithubRepository,
    github_client: GithubClient,
    language_analysers,
    path: str = "",
) -> tuple[set[str], dict[str, str]]:
    frameworks_identified: set[str] = set()
    openapi_specs_discovered: dict[str, str] = {}

    IGNORED_FILE_PATH_PREFIXES = (
        ".github",
        "__test",
        "test",
        "tests",
        ".env",
        "node_modules/",
        # "example",
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
    print(f"ℹ️ {repository.full_name}: Scanning {len(repository_contents)} files in /{path}...")

    for file in repository_contents:
        if file.type == "dir":
            new_frameworks_identified, new_openapi_specs_discovered = scan_repository_recursive(
                repository, github_client, language_analysers, path=file.path
            )
        else:
            try:
                new_frameworks_identified, new_openapi_specs_discovered = scan_file(
                    file, github_client, language_analysers
                )
            except github.GithubException as exception:
                print(f"❗️ Failed to scan file {file.path} from {repository.full_name}, exception raised: {exception}")
                continue

        frameworks_identified.update(new_frameworks_identified)
        openapi_specs_discovered = {**openapi_specs_discovered, **new_openapi_specs_discovered}

    return frameworks_identified, openapi_specs_discovered


def scan_repository(github_client: GithubClient, repository: GithubRepository) -> tuple[set[str], dict[str, str]]:
    repository_languages = list(respect_rate_limit(repository.get_languages, github_client).keys())
    print(f"ℹ️ {repository.full_name}: Languages detected: {', '.join(repository_languages)}")

    language_analysers = get_language_analysers(repository_languages)
    print(f"ℹ️ {repository.full_name}: Got {len(language_analysers)} language analysers...")

    return scan_repository_recursive(repository, github_client, language_analysers)


def get_repositories_to_scan(github_client: GithubClient) -> list[GithubRepository]:
    repositories_to_scan = []

    for repo in github_client.get_user().get_repos():
        if repo.archived:
            continue

        repositories_to_scan.append(repo)

    return repositories_to_scan


def scan_with_token(github_token: str) -> None:
    github_client = github.Github(github_token)

    repositories_to_scan = get_repositories_to_scan(github_client)

    for repo in repositories_to_scan:
        print(f"ℹ️ {repo.full_name}: Scanning...")

        try:
            frameworks_identified, openapi_specs_discovered = scan_repository(github_client, repo)

        except github.GithubException as exception:
            print(f"❗️ {repo.full_name}: Failed to scan, exception raised: {exception}")
            continue

        if len(openapi_specs_discovered) == 0:
            print(f"ℹ️ {repo.full_name}: Scan complete. No APIs discovered.")
            continue

        print(
            f"ℹ️ {repo.full_name}: Scan complete. {len(openapi_specs_discovered)} OpenAPI API(s) discovered or"
            " generated from static analysis."
        )
        create_api_response = requests.post(
            f"{FIRETAIL_API_URL}/discovery/api-repository",
            headers={
                "x-ft-app-key": FIRETAIL_APP_TOKEN,
                "Content-Type": "application/json",
            },
            json={
                "full_name": repo.full_name,
                "id": f"github:{repo.id}",
            },
        )
        if create_api_response.status_code != 200:
            print(f"❗️ {repo.full_name}: Failed to create API in SaaS, response: {create_api_response.text}")
            continue

        print(
            f"✅ {repo.full_name}: Successfully created/updated API in Firetail SaaS, response:"
            f" {create_api_response.text}"
        )

        api_uuid = create_api_response.json()["api"]["UUID"]

        for source, openapi_spec in openapi_specs_discovered.items():
            upload_api_spec_response = requests.post(
                f"{FIRETAIL_API_URL}/discovery/api-repository/{api_uuid}/appspec",
                headers={
                    "x-ft-app-key": FIRETAIL_APP_TOKEN,
                    "Content-Type": "application/json",
                },
                json={
                    "source": source,
                    "appspec": openapi_spec,
                },
            )

            if upload_api_spec_response.status_code != 201:
                print(
                    f"❗️ {repo.full_name}: Failed to upload OpenAPI spec {source} to SaaS, response:"
                    f" {upload_api_spec_response.text}"
                )
                continue

            print(
                f"✅ {repo.full_name}: Successfully created/updated {source} API spec in Firetail SaaS, response:"
                f" {upload_api_spec_response.text}"
            )


def main():
    scan_with_token(GITHUB_TOKEN)


main()
