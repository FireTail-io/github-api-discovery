# API Discovery from Github Repositories

This Docker image will discover APIs in your GitHub account by scanning for openapi/swagger
specifications in your repositories, as well as generating them via static code analysis. It will
create an API per repository, and potentially multiple collections for that API, in the FireTail
SaaS Platform.

## Requirements

### To Pull The Image

- An access token with at least `read:packages` scope
  ([link](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry#authenticating-to-the-container-registry))

### To Scan Repos

- A `config.yml` file (not `config.yaml`)
- A 'classic' GitHub token with `xyz` permissions
  ([link](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic))
  - Can be the same as the token used to pull the image
- A FireTail app token ([link](https://www.firetail.io/docs/create-app-token))

## Running The Repo Scanner

### Pull The Image

Authenticate with your `read:packages` scoped token
([link](https://docs.docker.com/engine/reference/commandline/login/))

```shell
docker pull ghcr.io/firetail-io/firetail-code-repository-scanner:latest
```

### Configure The Scanner

- Create a `./config/config.yml` file from the following (not `config.yaml`)

```yaml
# List organisations to scan their repositories
organisations: # default []
  example-organisation:
    # Under each org, you can skip public, private, internal, archived or fork repositories
    skip_public_repositories: False # default False
    skip_private_repositories: False # default False
    skip_internal_repositories: False # default False
    skip_archived_repositories: False # default False
    skip_forks: False # default False

# List users to scan their repositories
users: # default []
  example-user:
    # Under each user, you can skip public, private, archived or fork repositories
    skip_public_repositories: False # default False
    skip_private_repositories: False # default False
    skip_archived_repositories: False # default False
    skip_forks: False # default False

# List individual repositories to include or exclude them explicitly from scanning.
# Has higher precedence than scanning via users or orgs.
repositories: # default []
  example-user/example-repository: exclude
  example-organisation/example-repository: include
```

### Scan Repos

```shell
docker run --rm \
  --env GITHUB_TOKEN=${YOUR_GITHUB_TOKEN} \
  --env FIRETAIL_APP_TOKEN=${YOUR_FIRETAIL_APP_TOKEN} \
  --mount type=bind,source="${PWD}"/config.yml,target=/config.yml,readonly \
  ghcr.io/firetail-io/firetail-code-repository-scanner:latest
```

## Environment Variables

| Variable Name        | Description                                                                                                              | Required? | Default                                        |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------ | --------- | ---------------------------------------------- |
| `GITHUB_TOKEN`       | A classic GitHub personal access token.                                                                                  | Yes ✅    | None                                           |
| `FIRETAIL_APP_TOKEN` | An app token from the Firetail SaaS.                                                                                     | Yes ✅    | None                                           |
| `FIRETAIL_API_URL`   | The URL of the Firetail SaaS API.                                                                                        | No ❌     | `https://api.saas.eu-west-1.prod.firetail.app` |
| `LOGGING_LEVEL`      | The logging level provided to Python's [logging](https://docs.python.org/3/library/logging.html#logging-levels) library. | No ❌     | `INFO`                                         |
