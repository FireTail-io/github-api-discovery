from typing import List, Tuple
import github
from github import Github as GithubClient
from github.Repository import Repository as GithubRepository

from openapi.validation import is_openapi_spec
from static_analysis import get_language_analysers
from utils import respect_rate_limit


def get_repositories_to_scan(github_client: GithubClient) -> List[GithubRepository]:
    repositories_to_scan = []

    for repo in github_client.get_user().get_repos():
        if repo.fork:
            continue

        if repo.archived:
            continue

        repositories_to_scan.append(repo)

    return repositories_to_scan


def scan_repository(github_client: GithubClient, repository: GithubRepository) -> Tuple[List[str], dict[str, str]]:
    openapi_specs_discovered: dict[str, str] = {}
    frameworks_identified: list[str] = []

    repository_languages = respect_rate_limit(repository.get_languages, github_client)

    language_analysers = get_language_analysers(list(repository_languages.keys()))

    repository_contents = respect_rate_limit(lambda: repository.get_contents(""), github_client)
    if not isinstance(repository_contents, list):
        repository_contents = [repository_contents]

    for file in repository_contents:
        file_path = respect_rate_limit(lambda: file.path, github_client)

        IGNORED_FILE_PATH_PREFIXES = (".github", "__test", "test", "tests", ".env", "node_modules/", "example")
        if file_path.startswith(IGNORED_FILE_PATH_PREFIXES):
            continue

        IGNORED_FILE_PATH_SUBSTRINGS = ["test/"]
        if any([ignored_file_path in file_path for ignored_file_path in IGNORED_FILE_PATH_SUBSTRINGS]):
            continue

        file_contents = respect_rate_limit(lambda: file.content, github_client)
        if file_contents is None:
            continue

        if is_openapi_spec(file.path, file_contents):
            openapi_specs_discovered[file_path] = file_contents

        for language_analyser in language_analysers:
            frameworks_identified += language_analyser(file_path, file_contents)

    return frameworks_identified, openapi_specs_discovered


def scan_with_token(github_token: str):
    github_client = github.Github(github_token)

    repositories_to_scan = get_repositories_to_scan(github_client)

    for repo in repositories_to_scan:
        frameworks_identified, openapi_specs_discovered = scan_repository(github_token, repo.full_name)
        print(repo.full_name, frameworks_identified, openapi_specs_discovered)


def main():
    pass
