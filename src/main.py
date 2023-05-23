from typing import Callable
import github
from github import Github as GithubClient
from github.ContentFile import ContentFile as GithubContentFile
from github.Repository import Repository as GithubRepository

from env import GITHUB_TOKEN
from openapi.validation import is_openapi_spec
from static_analysis import get_language_analysers
from utils import respect_rate_limit


def scan_file(
    file: GithubContentFile, github_client: GithubClient, language_analysers: list[Callable[[str, str], set[str]]]
) -> tuple[set[str], dict[str, str]]:
    file_path = respect_rate_limit(lambda: file.path, github_client)

    IGNORED_FILE_PATH_PREFIXES = (".github", "__test", "test", "tests", ".env", "node_modules/", "example")
    if file_path.startswith(IGNORED_FILE_PATH_PREFIXES):
        return set(), {}

    IGNORED_FILE_PATH_SUBSTRINGS = ["test/"]
    if any([ignored_file_path in file_path for ignored_file_path in IGNORED_FILE_PATH_SUBSTRINGS]):
        return set(), {}

    file_contents = respect_rate_limit(lambda: file.content, github_client)
    if file_contents is None:
        return set(), {}

    openapi_specs_discovered = {}
    frameworks_identified: set[str] = set()

    if is_openapi_spec(file.path, file_contents):
        openapi_specs_discovered[file_path] = file_contents

    for language_analyser in language_analysers:
        frameworks_identified.update(language_analyser(file_path, file_contents))

    return frameworks_identified, openapi_specs_discovered


def scan_repository(github_client: GithubClient, repository: GithubRepository) -> tuple[list[str], dict[str, str]]:
    openapi_specs_discovered: dict[str, str] = {}
    frameworks_identified: list[str] = []

    repository_languages = list(respect_rate_limit(repository.get_languages, github_client).keys())
    print(f"repository_languages: {repository_languages}")

    language_analysers = get_language_analysers(repository_languages)
    print(f"Got {len(language_analysers)} language analysers...")

    repository_contents = respect_rate_limit(lambda: repository.get_contents(""), github_client)
    if not isinstance(repository_contents, list):
        repository_contents = [repository_contents]
    print(f"Scanning {len(repository_contents)} files in repo...")

    for file in repository_contents:
        try:
            new_frameworks_identified, new_openapi_specs_discovered = scan_file(file, github_client, language_analysers)
        except github.GithubException as exception:
            print(f"Failed to scan file {file.path} from {repository.full_name}, exception raised: {exception}")
            continue

        frameworks_identified += new_frameworks_identified
        openapi_specs_discovered = {**openapi_specs_discovered, **new_openapi_specs_discovered}

    return frameworks_identified, openapi_specs_discovered


def get_repositories_to_scan(github_client: GithubClient) -> list[GithubRepository]:
    repositories_to_scan = []

    for repo in github_client.get_user().get_repos():
        if repo.fork:
            continue

        if repo.archived:
            continue

        repositories_to_scan.append(repo)

    return repositories_to_scan


def scan_with_token(github_token: str) -> None:
    github_client = github.Github(github_token)

    repositories_to_scan = get_repositories_to_scan(github_client)

    for repo in repositories_to_scan:
        print(f"Scanning {repo.full_name}...")

        try:
            frameworks_identified, openapi_specs_discovered = scan_repository(github_client, repo)

        except github.GithubException as exception:
            print(f"Failed to scan f{repo.full_name}, exception raised: {exception}")
            continue

        print(repo.full_name, frameworks_identified, openapi_specs_discovered)


def main():
    scan_with_token(GITHUB_TOKEN)


main()
