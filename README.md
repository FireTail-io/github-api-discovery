# API Discovery from Github Repositories

This docker image will discover APIs in your account and try to extract openapi/swagger specifications. It will create the api and discovered collections in FireTails SaaS Platform

Required:
  - GitHub token
  - Firetail app token



## Build

```BASH
docker build --rm -t firetail-io/github-api-discovery:latest -f build_setup/Dockerfile .
```



## Run

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

