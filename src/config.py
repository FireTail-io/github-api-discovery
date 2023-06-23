from abc import ABC
from dataclasses import dataclass, field
from github.Repository import Repository as GithubRepository


class AccountConfig(ABC):
    skip_public_repositories: bool = False
    skip_archived_repositories: bool = False
    skip_forks: bool = False

    def skip_repo(self, repository: GithubRepository) -> bool:
        if self.skip_public_repositories and repository.visibility == "public":
            return True

        if self.skip_archived_repositories and repository.archived:
            return True

        if self.skip_forks and repository.fork:
            return True

        return False


@dataclass
class OrgConfig(AccountConfig):
    skip_internal_repositories: bool = False

    def skip_repo(self, repository: GithubRepository) -> bool:
        super_skip = super().skip_repo(repository)
        if super_skip:
            return True

        if self.skip_internal_repositories and repository.visibility == "internal":
            return True

        return False


@dataclass
class UserConfig(AccountConfig):
    skip_private_repositories: bool = False

    def skip_repo(self, repository: GithubRepository) -> bool:
        super_skip = super().skip_repo(repository)
        if super_skip:
            return True

        if self.skip_private_repositories and repository.visibility == "private":
            return True

        return False


@dataclass
class Config:
    organisations: dict[str, OrgConfig | None] | list[str] | None = field(default_factory=dict[str, OrgConfig])
    users: dict[str, UserConfig | None] | list[str] | None = field(default_factory=dict[str, UserConfig])
    repositories: dict[str, str] | None = field(default_factory=dict)

    def __post_init__(self):
        if type(self.organisations) == dict:
            self.organisations = {
                organisation: config if config is not None else OrgConfig()
                for organisation, config in self.organisations.items()
            }
        elif type(self.organisations) == list:
            self.organisations = {organisation: OrgConfig() for organisation in self.organisations}
        elif self.organisations is None:
            self.organisations = {}

        if type(self.users) == dict:
            self.users = {user: config if config is not None else UserConfig() for user, config in self.users.items()}
        elif type(self.users) == list:
            self.users = {user: UserConfig() for user in self.users}
        elif self.users is None:
            self.users = {}

        if self.repositories is None:
            self.repositories = {}

    def skip_repo(self, repository: GithubRepository) -> bool:
        return self.repositories.get(repository.full_name) != "include"
