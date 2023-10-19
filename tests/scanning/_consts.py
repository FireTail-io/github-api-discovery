import base64

from github.Organization import Organization as GithubOrganisation
from github.Repository import Repository as GithubRepository

ALL_USER_FLAGS = {
    "skip_public_repositories",
    "skip_archived_repositories",
    "skip_forks",
    "skip_private_repositories",
}

ALL_ORG_FLAGS = ALL_USER_FLAGS.union({"skip_internal_repositories"})

MOCK_ORGANISATION = GithubOrganisation(
    requester=None, headers={}, attributes={"login": "MOCK_ORGANISATION"}, completed=True  # type: ignore
)

MOCK_REPOSITORY_PUBLIC = GithubRepository(
    requester=None,  # type: ignore
    headers={},
    attributes={"full_name": "MOCK_REPOSITORY_PUBLIC", "url": "MOCK_REPOSITORY_PUBLIC_URL", "visibility": "public"},
    completed=True,
)
MOCK_REPOSITORY_ARCHIVED = GithubRepository(
    requester=None,  # type: ignore
    headers={},
    attributes={"full_name": "MOCK_REPOSITORY_ARCHIVED", "url": "MOCK_REPOSITORY_ARCHIVED_URL", "archived": True},
    completed=True,
)
MOCK_REPOSITORY_FORK = GithubRepository(
    requester=None,  # type: ignore
    headers={},
    attributes={"full_name": "MOCK_REPOSITORY_FORK", "url": "MOCK_REPOSITORY_FORK_URL", "fork": True},
    completed=True,
)
MOCK_REPOSITORY_PRIVATE = GithubRepository(
    requester=None,  # type: ignore
    headers={},
    attributes={"full_name": "MOCK_REPOSITORY_PRIVATE", "url": "MOCK_REPOSITORY_PRIVATE_URL", "visibility": "private"},
    completed=True,
)
MOCK_REPOSITORY_INTERNAL = GithubRepository(
    requester=None,  # type: ignore
    headers={},
    attributes={
        "full_name": "MOCK_REPOSITORY_INTERNAL",
        "url": "MOCK_REPOSITORY_INTERNAL_URL",
        "visibility": "internal",
    },
    completed=True,
)
ALL_MOCK_REPOS = {
    MOCK_REPOSITORY_PUBLIC,  # type: ignore
    MOCK_REPOSITORY_ARCHIVED,  # type: ignore
    MOCK_REPOSITORY_FORK,  # type: ignore
    MOCK_REPOSITORY_PRIVATE,  # type: ignore
    MOCK_REPOSITORY_INTERNAL,  # type: ignore
}

MOCK_FLASK_MAIN_PY_B64 = base64.b64encode(
    """from flask import Flask

app = Flask(__name__)

@app.route("/", methods=["GET"])
def hello_world():
    return "<p>Hello, World!</p>"
""".encode(
        "utf-8"
    )
).decode()

MOCK_APPSPEC_YAML_B64 = base64.b64encode(
    """info:
  title: Static Analysis - Flask
  version: '2000-01-01 00:00:00'
openapi: 3.0.0
paths:
  /:
    get:
      responses:
        default:
          description: Discovered via static analysis""".encode(
        "utf-8"
    )
).decode()


MOCK_APPSPEC_JSON_B64 = base64.b64encode(
    """{
  "info": {
    "title": "Static Analysis - Flask",
    "version": "2000-01-01 00:00:00"
  },
  "openapi": "3.0.0",
  "paths": {
    "/": {
      "get": {
        "responses": {
          "default": {
            "description": "Discovered via static analysis"
          }
        }
      }
    }
  }
}""".encode(
        "utf-8"
    )
).decode()
