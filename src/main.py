import datetime
import requests
import jwt
import datetime
import github
import base64
import yaml
import json
from prance import ResolvingParser
from prance.util.resolver import RESOLVE_INTERNAL
import time

from consts import (REQUEST_SESSION, PYTHON_IMPORTS, GITHUB_URL)


class SpecDataValidationError(Exception):
    pass


def is_spec_valid(spec_data: dict) -> bool:
    parser = ResolvingParser(
        spec_string=json.dumps(spec_data),
        resolve_types=RESOLVE_INTERNAL,
        backend="openapi-spec-validator",
        lazy=True,
    )
    try:
        parser.parse()
    except Exception:
        # In the future, maybe we can provide some proper details here.
        return False
    return True


def resolve_and_validate_spec_data(spec_data: dict) -> dict:
    if not is_spec_valid(spec_data):
        raise SpecDataValidationError()

    return spec_data


def load_key(key_path):
    with open(key_path, "r") as key_file:
        key = key_file.read()
    return key


def get_auth_token(gh_app_id: str, key_path: str):
    key = load_key(key_path)
    now = int(datetime.datetime.now().timestamp())
    payload = {
        "iat": now - 60,
        "exp": now + 60 * 8,  # expire after 8 minutes
        "iss": gh_app_id,
    }
    return jwt.encode(payload=payload, key=key, algorithm="RS256")


def get_repositories(token):
    response = REQUEST_SESSION.get(
        url=f"{GITHUB_URL}user/org",
        headers={
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Accept": "application/vnd.github+json",
        },
    )
    return response


def get_meta(token):
    response = REQUEST_SESSION.get(
        url=f"{GITHUB_URL}user/orgs",
        headers={
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Accept": "application/vnd.github+json",
        },
    )
    return response


def get_token_from_install(token, installation_id):
    response = REQUEST_SESSION.post(
        url=f"{GITHUB_URL}app/installations/{installation_id}/access_tokens",
        headers={
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Accept": "application/vnd.github+json",
        },
    )
    return response


def installation_repositories(token, installation_id):
    response = REQUEST_SESSION.post(
        url=f"{GITHUB_URL}installation/repositories",
        headers={
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Accept": "application/vnd.github+json",
        },
    )
    return response


def get_repo_languages(token, repo_name):
    repo_name = repo_name.lower()
    response = REQUEST_SESSION.get(
        url=f"{GITHUB_URL}repos/{repo_name}/languages",
        headers={
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Accept": "application/vnd.github+json",
        },
    )
    return response


def get_files_in_repo(github_object, repo_name):
    try:
        repo = github_object.get_repo(repo_name)
    except requests.exceptions.ConnectTimeout:
        time.sleep(10)
        repo = github_object.get_repo(repo_name)
    try:
        contents = repo.get_contents("")
    except requests.exceptions.ConnectTimeout:
        time.sleep(10)
        contents = repo.get_contents("")

    file_list = []
    while len(contents) > 0:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(repo.get_contents(file_content.path))
        else:
            file_list.append(file_content.path)
    return file_list


def read_file_contents(github_object, repo_name, file_path):
    repo = github_object.get_repo(repo_name)
    a = repo.get_contents(file_path)
    return base64.b64decode(a.content).decode().replace("\\r", "").replace("\\n", "\n")


def identify_api_framework(contents):
    imports_discovered = []
    for module in PYTHON_IMPORTS:
        if f"{module}" not in contents:
            continue
        if f"from {module}" in contents:
            imports_discovered.append(module)
        if f"import {module}" in contents:
            if module not in imports_discovered:
                imports_discovered.append(module)
    return imports_discovered


def list_orgs_for_user(token):
    repos = []
    github_object = github.Github(token)
    for repo in github_object.get_user().get_repos():
        if repo.fork:
            continue
        if repo.archived:
            continue
        repos.append(repo.full_name)
    return repos


def process_repo(token: str, repo_name: str):
    specs_discovered = {}
    frameworks_identified = []
    github_object = github.Github(token)
    languages = get_repo_languages(token, repo_name).json()
    time.sleep(10)
    try:
        files = get_files_in_repo(github_object, repo_name)
    except github.GithubException:
        return [], {}
    for file_path in files:
        if file_path.startswith((".github", "__test", "test", "tests", ".env", "node_modules/", "example")):
            continue
        if file_path.contains(("/test", "")):
            continue
        if spec_data := detect_openapi_specs(github_object, repo_name, file_path):
            specs_discovered[file_path] = spec_data
        if "Python" in languages and file_path.endswith(".py"):
            file_contents = read_file_contents(
                github_object, repo_name, file_path)
            frameworks_identified += identify_api_framework(file_contents)
    frameworks_identified = list(dict.fromkeys(frameworks_identified))
    return frameworks_identified, specs_discovered


def detect_openapi_specs(github_object, repo_name, file_path):
    if file_path.endswith(".json"):
        file_contents = read_file_contents(github_object, repo_name, file_path)
        try:
            file_dict = json.loads(file_contents)
            return resolve_and_validate_spec_data(file_dict)
        except Exception:
            # print(str(e))
            return False

    if file_path.endswith((".yaml", ".yml")):
        file_contents = read_file_contents(github_object, repo_name, file_path)
        if isinstance(file_contents, str):
            try:
                file_dict = yaml.safe_load(file_contents)
                return resolve_and_validate_spec_data(file_dict)
            except Exception:
                # print(str(e))
                # print(traceback.format_exc())
                return False
        return file_contents


def process_all_repos(token):
    gh_repositories = list_orgs_for_user(token)

    for repo in gh_repositories:
        api_details = process_repo(token, repo)
        print(repo, api_details)


def main():
    pass
