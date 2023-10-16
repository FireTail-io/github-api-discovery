from unittest.mock import patch

import pytest
from _consts import (
    ALL_MOCK_REPOS,
    ALL_ORG_FLAGS,
    ALL_USER_FLAGS,
    MOCK_REPOSITORY_ARCHIVED,
    MOCK_REPOSITORY_FORK,
    MOCK_REPOSITORY_INTERNAL,
    MOCK_REPOSITORY_PRIVATE,
    MOCK_REPOSITORY_PUBLIC,
)
from _utils import powerset
from dacite import from_dict
from github import Github as GithubClient
from github.AuthenticatedUser import AuthenticatedUser as GithubUser
from github.Organization import Organization as GithubOrganisation
from github.Repository import Repository as GithubRepository

from config import Config, OrgConfig, UserConfig
from scanning import (
    get_repos_to_scan_with_config,
    get_repos_to_scan_without_config,
    get_repositories_of_organisation,
    get_repositories_of_user,
)


@pytest.mark.parametrize("org_repos", powerset(ALL_MOCK_REPOS))
def test_get_repos_to_scan_without_config(org_repos):
    class PatchedGithubOrganisation(GithubOrganisation):
        def get_repos(*_):
            return org_repos

    PATCHED_ORGANISATION = PatchedGithubOrganisation(
        requester=None,  # type: ignore
        headers={},
        attributes={"url": "PATCHED_GITHUB_ORGANISATION_URL"},
        completed=True,
    )

    class PatchedGithubUser(GithubUser):
        def __init__(self):
            pass

        def get_orgs(*_):
            return [PATCHED_ORGANISATION]

    class PatchedGithubClient(GithubClient):
        def get_user(self):
            return PatchedGithubUser()

        def get_organization(*_):
            return PATCHED_ORGANISATION

    # The expected behavious is that the scanner should get all of the orgs the user belongs to, and then all of the
    # repos belonging to those orgs.
    repos_to_scan = get_repos_to_scan_without_config(PatchedGithubClient())  # type: ignore

    assert repos_to_scan == set(org_repos)


def test_get_repos_to_scan_with_config_empty():
    TEST_CONFIG = Config()
    repos_to_scan = get_repos_to_scan_with_config(None, TEST_CONFIG)  # type: ignore
    assert repos_to_scan == set()


@pytest.mark.parametrize("included_repos", powerset(ALL_MOCK_REPOS))
def test_get_repos_to_scan_with_config_with_specific_repos_included(included_repos: set[GithubRepository]):
    TEST_CONFIG = Config(repositories={repo.full_name: "include" for repo in included_repos})

    class PatchedGithubClient(GithubClient):
        def get_repo(self, repo_name: str):
            return {repo.full_name: repo for repo in included_repos}[repo_name]

    repos_to_scan = get_repos_to_scan_with_config(PatchedGithubClient(), TEST_CONFIG)

    assert repos_to_scan == set(included_repos)


@pytest.mark.parametrize("enabled_flags", powerset(ALL_ORG_FLAGS))
def test_get_repositories_of_organisation_with_flags(enabled_flags):
    TEST_ORG_CONFIG = from_dict(OrgConfig, {flag: True for flag in enabled_flags})

    class PatchedGithubOrganisation(GithubOrganisation):
        def __init__(self):
            pass

        def get_repos(*_):
            return ALL_MOCK_REPOS

    class PatchedGithubClient(GithubClient):
        def get_organization(*_):
            return PatchedGithubOrganisation()

    repos_to_scan = get_repositories_of_organisation(PatchedGithubClient(), "MOCK_ORGANISATION", TEST_ORG_CONFIG)

    REPOS_EXCLUDED_BY_FLAG = {
        "skip_public_repositories": {MOCK_REPOSITORY_PUBLIC},  # type: ignore
        "skip_archived_repositories": {MOCK_REPOSITORY_ARCHIVED},  # type: ignore
        "skip_forks": {MOCK_REPOSITORY_FORK},  # type: ignore
        "skip_private_repositories": {MOCK_REPOSITORY_PRIVATE},  # type: ignore
        "skip_internal_repositories": {MOCK_REPOSITORY_INTERNAL},  # type: ignore
    }

    assert repos_to_scan == ALL_MOCK_REPOS - set().union(*[REPOS_EXCLUDED_BY_FLAG[flag] for flag in enabled_flags])


@pytest.mark.parametrize("enabled_flags", powerset(ALL_USER_FLAGS))
def test_get_repositories_of_user_with_flags(enabled_flags):
    TEST_USER_CONFIG = from_dict(UserConfig, {flag: True for flag in enabled_flags})

    class PatchedGithubUser(GithubUser):
        def __init__(self):
            pass

        def get_repos(*_):
            return ALL_MOCK_REPOS

    class PatchedGithubClient(GithubClient):
        def get_user(*_):
            return PatchedGithubUser()

    repos_to_scan = get_repositories_of_user(PatchedGithubClient(), "MOCK_USER", TEST_USER_CONFIG)

    REPOS_EXCLUDED_BY_FLAG = {
        "skip_public_repositories": {MOCK_REPOSITORY_PUBLIC},  # type: ignore
        "skip_archived_repositories": {MOCK_REPOSITORY_ARCHIVED},  # type: ignore
        "skip_forks": {MOCK_REPOSITORY_FORK},  # type: ignore
        "skip_private_repositories": {MOCK_REPOSITORY_PRIVATE},  # type: ignore
    }

    assert repos_to_scan == ALL_MOCK_REPOS - set().union(*[REPOS_EXCLUDED_BY_FLAG[flag] for flag in enabled_flags])


@pytest.mark.parametrize("org_repos", powerset(ALL_MOCK_REPOS))
@patch("scanning.get_repositories_of_organisation", return_value=set())
def test_get_repos_to_scan_with_config_with_orgs_as_list(get_repositories_of_organisation_patch, org_repos):
    get_repositories_of_organisation_patch.return_value = org_repos
    TEST_CONFIG = Config(organisations=["MOCK_ORGANISATION"])
    repos_to_scan = get_repos_to_scan_with_config(None, TEST_CONFIG)  # type: ignore
    assert repos_to_scan == set(org_repos)


@pytest.mark.parametrize("user_repos", powerset(ALL_MOCK_REPOS))
@patch("scanning.get_repositories_of_user", return_value=set())
def test_get_repos_to_scan_with_config_with_users_as_list(get_repositories_of_user_patch, user_repos):
    get_repositories_of_user_patch.return_value = user_repos
    TEST_CONFIG = Config(users=["MOCK_USER"])
    repos_to_scan = get_repos_to_scan_with_config(None, TEST_CONFIG)  # type: ignore
    assert repos_to_scan == set(user_repos)


@pytest.mark.parametrize("excluded_repos", powerset(ALL_MOCK_REPOS))
@patch("scanning.get_repositories_of_organisation", return_value=ALL_MOCK_REPOS)
def test_get_repos_to_scan_with_config_always_excludes_repos_from_org(_, excluded_repos):
    TEST_CONFIG = Config(
        organisations={"MOCK_ORGANISATION": None}, repositories={repo.full_name: "exclude" for repo in excluded_repos}
    )

    repos_to_scan = get_repos_to_scan_with_config(None, TEST_CONFIG)  # type: ignore

    assert repos_to_scan == ALL_MOCK_REPOS - set(excluded_repos)


@pytest.mark.parametrize("excluded_repos", powerset(ALL_MOCK_REPOS))
@patch("scanning.get_repositories_of_user", return_value=ALL_MOCK_REPOS)
def test_get_repos_to_scan_with_config_always_excludes_repos_from_user(_, excluded_repos):
    TEST_CONFIG = Config(users={"MOCK_USER": None}, repositories={repo.full_name: "exclude" for repo in excluded_repos})

    repos_to_scan = get_repos_to_scan_with_config(None, TEST_CONFIG)  # type: ignore

    assert repos_to_scan == ALL_MOCK_REPOS - set(excluded_repos)
