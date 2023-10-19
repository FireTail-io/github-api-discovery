import uuid

import responses
from _consts import MOCK_APPSPEC_JSON_B64, MOCK_APPSPEC_YAML_B64, MOCK_FLASK_MAIN_PY_B64
from github import Github as GithubClient
from github.ContentFile import ContentFile
from github.Repository import Repository as GithubRepository

from scanning import scan_repositories


@responses.activate
def test_scan_repositories():
    MOCK_FIRETAIL_API_URL = "https://MOCK_FIRETAIL_API_URL"
    MOCK_API_UUID = str(uuid.uuid4())

    mock_repo_endpoint = responses.add(
        method="POST",
        url=f"{MOCK_FIRETAIL_API_URL}/discovery/api-repository",
        json={"api": {"UUID": MOCK_API_UUID}},
        status=200,
    )
    mock_appspec_endpoint = responses.add(
        method="POST",
        url=f"{MOCK_FIRETAIL_API_URL}/discovery/api-repository/{MOCK_API_UUID}/appspec",
        json={"message": "MOCK_RESPONSE"},
        status=201,
    )

    class PatchedGithubRepository(GithubRepository):
        def get_languages(self) -> dict[str, int]:
            return {"Python": 1}

        def get_contents(self, path):
            match path:
                case "":
                    return ContentFile(
                        requester=None,  # type: ignore
                        headers={},
                        attributes={"type": "dir", "path": "src"},
                        completed=True,
                    )
                case "src":
                    return [
                        ContentFile(
                            requester=None,  # type: ignore
                            headers={},
                            attributes={
                                "type": "file",
                                "path": "src/appspec.yaml",
                                "content": str(MOCK_APPSPEC_YAML_B64),
                            },
                            completed=True,
                        ),
                        ContentFile(
                            requester=None,  # type: ignore
                            headers={},
                            attributes={
                                "type": "file",
                                "path": "src/appspec.json",
                                "content": str(MOCK_APPSPEC_JSON_B64),
                            },
                            completed=True,
                        ),
                        ContentFile(
                            requester=None,  # type: ignore
                            headers={},
                            attributes={"type": "file", "path": "src/main.py", "content": str(MOCK_FLASK_MAIN_PY_B64)},
                            completed=True,
                        ),
                        ContentFile(
                            requester=None,  # type: ignore
                            headers={},
                            attributes={"type": "file", "path": "empty.py", "content": None},
                            completed=True,
                        ),
                    ]
                case _:
                    return []

    class PatchedGithubClient(GithubClient):
        pass

    specs_discovered = scan_repositories(
        PatchedGithubClient(),
        "",
        MOCK_FIRETAIL_API_URL,
        {
            PatchedGithubRepository(
                requester=None,  # type: ignore
                headers={},
                attributes={
                    "full_name": "PATCHED_GITHUB_REPOSITORY",
                    "url": "PATCHED_GITHUB_REPOSITORY_URL",
                    "id": 123456789,
                },
                completed=True,
            )
        },  # type: ignore
    )

    assert specs_discovered == 3
    assert mock_repo_endpoint.call_count == 1
    assert mock_appspec_endpoint.call_count == 3
