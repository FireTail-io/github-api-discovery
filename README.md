# API Discovery from Github Repositories

This Docker image will discover APIs in your GitHub account by scanning for openapi/swagger specifications in your repositories, as well as generating them via static code analysis. It will create an API per repository, and potentially multiple collections for that API, in the FireTail SaaS Platform.



## Tests

The tests can be run using the provided Dockerfile:

```bash
docker build --rm -t firetail-io/github-api-discovery:test-python -f build_setup/Dockerfile . --target test-python
```

Tests for the Golang analyser can also be run separately using the provided Dockerfile to yield a html coverage report:

```bash
docker build --rm -t firetail-io/github-api-discovery:test-golang -f build_setup/Dockerfile . --target test-golang
docker run --rm --entrypoint cat firetail-io/github-api-discovery:test-golang coverage.html > golang-coverage.html
```



## Building

You can build the image yourself by cloning the repository and using the following docker command:

```bash
git clone git@github.com:FireTail-io/github-api-discovery.git
cd github-api-discovery
docker build --rm -t firetail-io/github-api-discovery:latest -f build_setup/Dockerfile . --target runtime
```



## Running

Running the image requires two environment variables, `GITHUB_TOKEN` and `FIRETAIL_APP_TOKEN`. You can find a full list of environment variables used by the scanner below.

You may run the image using the following docker command:

```bash
export GITHUB_TOKEN=YOUR_GITHUB_TOKEN
export FIRETAIL_APP_TOKEN=YOUR_FIRETAIL_APP_TOKEN
docker run --rm -e GITHUB_TOKEN=${GITHUB_TOKEN} -e FIRETAIL_APP_TOKEN=${FIRETAIL_APP_TOKEN} firetail-io/github-api-discovery:latest
```

| Variable Name        | Description                                                  | Required? | Default                                          |
| -------------------- | ------------------------------------------------------------ | --------- | ------------------------------------------------ |
| `GITHUB_TOKEN`       | A classic GitHub personal access token.                      | Yes ✅     | None                                             |
| `FIRETAIL_APP_TOKEN` | An app token from the Firetail SaaS.                         | Yes ✅     | None                                             |
| `FIRETAIL_API_URL`   | The URL of the Firetail SaaS' API.                           | No ❌      | `"https://api.saas.eu-west-1.prod.firetail.app"` |
| `LOGGING_LEVEL`      | The logging level provided to python's [logging](https://docs.python.org/3/library/logging.html#logging-levels) library. | No ❌      | `"INFO"`                                         |

