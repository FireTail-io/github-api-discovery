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

```BASH
docker run --rm -e GH_TOKEN=${GH_TOKEN} firetail-io/github-api-discovery:latest
```