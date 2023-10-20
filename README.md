# API Discovery From GitHub Repositories

This Docker image will discover APIs in your GitHub organization/account by scanning for
OpenAPI/Swagger specifications in your repositories, as well as generating them via static code
analysis. It will create an API per repository, and potentially multiple collections for that API,
in the FireTail SaaS Platform.

## Requirements

- A 'classic' GitHub access token with `read:packages` scope
  - Fine-grained tokens do not currently support any `packages` scopes
    ([link](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry#authenticating-to-the-container-registry))
- Any type of GitHub access token with `read: contents` scope for the repos you wish to scan
  ([link](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens))
  - If you use a fine-grained GitHub access token scoped to specific repos, you will have to list
    them individually
- A FireTail app token ([link](https://www.firetail.io/docs/create-app-token))

## Configure The Scanner

Create a file named `config.yml` (not `.yaml`) from the following:

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

# List individual repositories to include or exclude explicitly - has higher
# precedence than scanning via users or orgs
repositories: # default []
  example-user/example-repository: exclude
  example-organisation/example-repository: include
```

Use the `repositories` block when using a fine-grained access token without access to all repos.

## Run the Scanner

Authenticate your docker CLI ([link](https://docs.docker.com/engine/reference/commandline/login/))

```shell
docker login \
  --username ${YOUR_GITHUB_USERNAME} \
  --password ${YOUR_GITHUB_CLASSIC_TOKEN} \
  ghcr.io
```

Start the scan

```shell
docker run --rm \
  --env GITHUB_TOKEN=${YOUR_GITHUB_TOKEN} \
  --env FIRETAIL_APP_TOKEN=${YOUR_FIRETAIL_APP_TOKEN} \
  --mount type=bind,source="${PWD}/config.yml",target=/config.yml,readonly \
  ghcr.io/firetail-io/firetail-code-repository-scanner:latest
```

## Container Environment Variables

Set via the `--env` flag when executing `docker run`

| Variable Name        | Description                                                                                     | Required? | Default                                        |
| -------------------- | ----------------------------------------------------------------------------------------------- | --------- | ---------------------------------------------- |
| `GITHUB_TOKEN`       | A GitHub access token                                                                           | Yes ✅    | None                                           |
| `FIRETAIL_APP_TOKEN` | A FireTail app token                                                                            | Yes ✅    | None                                           |
| `FIRETAIL_API_URL`   | The API URL for your FireTail SaaS instance                                                     | No ❌     | `https://api.saas.eu-west-1.prod.firetail.app` |
| `LOGGING_LEVEL`      | The scanner's verbosity ([link](https://docs.python.org/3/library/logging.html#logging-levels)) | No ❌     | `INFO`                                         |
