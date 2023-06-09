FROM golang:1.20.5-bullseye as build-golang
WORKDIR /src
COPY analysers/golang /src
RUN go build -buildmode=c-shared -o /dist/main.so .

FROM build-golang as test-golang
RUN go test -coverprofile=coverage.out ./...
RUN go tool cover -html coverage.out -o coverage.html

FROM python:3.11-slim-bullseye as build-python
WORKDIR /github-api-discovery/src
RUN apt-get update -y && apt-get upgrade -y
COPY --from=build-golang /dist/main.so /analysers/golang/main.so
COPY build_setup/requirements.txt /build_setup/requirements.txt
RUN python3 -m pip install -r /build_setup/requirements.txt
COPY src/ /github-api-discovery/src
RUN rm -rf /build_setup

FROM build-python as test-python
WORKDIR /github-api-discovery
COPY setup.cfg /github-api-discovery/setup.cfg
RUN python3 -m pip install pytest pytest-cov
COPY tests/ /github-api-discovery/tests/
RUN pytest --cov /github-api-discovery --cov-report=xml:coverage.xml

FROM build-python as runtime
RUN chmod +x /github-api-discovery/src/main.py
CMD [ "python", "/github-api-discovery/src/main.py" ]
