import datetime
import requests
import jwt
import datetime
import github
import base64
import yaml
import json
import traceback
from prance import ResolvingParser
from prance.util.resolver import RESOLVE_INTERNAL


class SpecDataValidationError(Exception):
    pass

def is_spec_valid(spec_data: dict) -> bool:
    parser = ResolvingParser(
        spec_string=json.dumps(spec_data), resolve_types=RESOLVE_INTERNAL, backend="openapi-spec-validator", lazy=True
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

request_session = requests.session()
GITHUB_URL = "https://api.github.com/"


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
        "iss": gh_app_id
    }
    return jwt.encode(payload=payload, key=key, algorithm="RS256")



def get_repositories(token):
    response = request_session.get(url=f"{GITHUB_URL}user/org", headers={
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Accept": "application/vnd.github+json"
    })
    return response

def get_meta(token):
    response = request_session.get(url=f"{GITHUB_URL}user/orgs", headers={
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Accept": "application/vnd.github+json"
    })
    return response

def get_token_from_install(token, installation_id):
    response = request_session.post(url=f"{GITHUB_URL}app/installations/{installation_id}/access_tokens", headers={
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Accept": "application/vnd.github+json"
    })
    return response

def installation_repositories(token, installation_id):
    response = request_session.post(url=f"{GITHUB_URL}installation/repositories", headers={
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Accept": "application/vnd.github+json"
    })
    return response

def list_repos(token, repo_name):
    g = github.Github(token)
    print(token)
    user = g.get_user()
    print("here", user.organizations_url)
    repos = user.get_repos()
    for repo in repos:
        print("Repository: ", repo.name)
        print("Description: ", repo.description)
        print("URL: ", repo.url)
        print("")
    return repos

def get_repo_languages(token, repo_name):
    repo_name = repo_name.lower()
    response = request_session.get(url=f"{GITHUB_URL}repos/{repo_name}/languages", headers={
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Accept": "application/vnd.github+json"
    })
    return response

def get_files_in_repo(github_object, repo_name):
    repo = github_object.get_repo(repo_name)
    contents = repo.get_contents("")
    file_list = []
    while len(contents) > 0:
        file_content = contents.pop(0)
        if file_content.type == 'dir':
            contents.extend(repo.get_contents(file_content.path))
        else:
            file_list.append(file_content.path)
    return file_list


def read_file_contents(github_object, repo_name, file_path):
    repo = github_object.get_repo(repo_name)
    a = repo.get_contents(file_path)
    if file_path.endswith((".yaml", ".yml")):
        print(base64.b64decode(a.content))
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


PYTHON_IMPORTS = ["flask", "fastapi", "scarlette", "django", "firetail", "gevent"]


def process_repo(token, repo_name):
    specs_discovered = {}
    frameworks_identified = []
    github_object = github.Github(token)
    languages = get_repo_languages(token, repo_name).json()
    files = get_files_in_repo(github_object, repo_name)
    for file_path in files:
        if file_path.startswith((".github", "test", "tests")):
            continue
        if spec_data := detect_openapi_specs(github_object, repo_name, file_path):
            specs_discovered[file_path] = spec_data
        if 'Python' in languages and file_path.endswith(".py"):
            file_contents = read_file_contents(github_object, repo_name, file_path)
            frameworks_identified += identify_api_framework(file_contents)
    frameworks_identified = list(dict.fromkeys(frameworks_identified))
    return frameworks_identified, specs_discovered


def detect_openapi_specs(github_object, repo_name, file_path):
    print(file_path)
    if file_path != "src/app-spec.yaml":
        return False
    if file_path.endswith(".json"):
        file_contents = read_file_contents(github_object, repo_name, file_path)
        try:
            file_dict = json.loads(file_contents)
            return resolve_and_validate_spec_data(file_dict)
        except Exception as e:
            print(str(e))
            return False
            
    if file_path.endswith((".yaml", ".yml")):
        file_contents = read_file_contents(github_object, repo_name, file_path)
        print(file_contents)
        if isinstance(file_contents, str):
            try:
                file_dict = yaml.safe_load(file_contents)
                return resolve_and_validate_spec_data(file_dict)
            except Exception as e:
                print(str(e))
                print(traceback.format_exc())
                return False
        return file_contents
        

        
        
    
