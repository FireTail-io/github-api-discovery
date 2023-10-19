# API Discovery from Github Repositories

This Docker image will discover APIs in your GitHub account by scanning for openapi/swagger specifications in your repositories, as well as generating them via static code analysis. It will create an API per repository, and potentially multiple collections for that API, in the FireTail SaaS Platform.

## Quickstart

First, clone this repo and build the scanner's image:

```bash
git clone git@github.com:FireTail-io/github-api-discovery.git
cd github-api-discovery
docker build \
  --tag firetail-io/github-api-discovery:latest \
  --file build_setup/Dockerfile \
  --target runtime \
  .
```

Make a copy of the provided [config-example.yml](./config-example.yml) and call it `config.yml`, then edit it for your use case.

```bash
cp config-example.yml config.yml
open config.yml
```

Running the image requires two environment variables to be set:

- `GITHUB_TOKEN`, [a classic GitHub personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic).
- `FIRETAIL_APP_TOKEN`, [a FireTail app token](https://www.firetail.io/docs/create-app-token).

Find a full list of environment variables under [Environment Variables](#environment-variables).

Once you have created a classic GitHub personal access token and a FireTail app token, you can run the scanner image:

```bash
docker run --rm \
  --env GITHUB_TOKEN=${YOUR_GITHUB_TOKEN} \
  --env FIRETAIL_APP_TOKEN=${YOUR_FIRETAIL_APP_TOKEN} \
  --mount type=bind,source="${PWD}"/config.yml,target=/config.yml,readonly \
  firetail-io/github-api-discovery:latest
```

## Tests

The tests can be run using the provided Dockerfile:

```bash
docker build --rm \
  --tag firetail-io/github-api-discovery:test-python \
  --file build_setup/Dockerfile \
  --target test-python \
  .
```

Tests for the Golang analyser can also be run separately using the provided Dockerfile to yield a html coverage report:

```bash
docker build \
  --tag firetail-io/github-api-discovery:test-golang \
  --file build_setup/Dockerfile \
  --target test-golang \
  .

docker run --rm \
  --volume ./coverage:/coverage \
  firetail-io/github-api-discovery:test-golang \
  cp coverage.html /coverage/golang-coverage.html
```

## Environment Variables

| Variable Name        | Description                                                                                                              | Required? | Default                                          |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------ | --------- | ------------------------------------------------ |
| `GITHUB_TOKEN`       | A classic GitHub personal access token.                                                                                  | Yes ✅    | None                                             |
| `FIRETAIL_APP_TOKEN` | An app token from the Firetail SaaS.                                                                                     | Yes ✅    | None                                             |
| `FIRETAIL_API_URL`   | The URL of the Firetail SaaS API.                                                                                       | No ❌     | `https://api.saas.eu-west-1.prod.firetail.app` |
| `LOGGING_LEVEL`      | The logging level provided to Python's [logging](https://docs.python.org/3/library/logging.html#logging-levels) library. | No ❌     | `INFO`                                         |
