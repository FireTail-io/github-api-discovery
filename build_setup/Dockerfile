FROM golang:1.20.5-bullseye as build-golang
WORKDIR /src
COPY analysers/golang /src
RUN go build -buildmode=c-shared -o /dist/main.so .

FROM build-golang as test-golang
RUN go test -coverprofile=coverage.out ./...
RUN go tool cover -html coverage.out -o coverage.html

FROM python:3.11-bullseye as build-tree-sitter
WORKDIR /src
RUN apt-get update -y && apt-get upgrade -y
RUN git clone https://github.com/tree-sitter/tree-sitter-javascript
RUN python3 -m pip install tree_sitter
COPY analysers/tree-sitter/build.py build.py
RUN python3 build.py

FROM python:3.11-bullseye as build-python
WORKDIR /github-api-discovery/src
RUN apt-get update -y && apt-get upgrade -y
COPY --from=build-golang /dist/main.so /analysers/golang/main.so
COPY --from=build-tree-sitter /dist/languages.so /analysers/tree-sitter/languages.so
COPY build_setup/requirements.txt /build_setup/requirements.txt
RUN python3 -m pip install -r /build_setup/requirements.txt
COPY src/ /github-api-discovery/src
RUN rm -rf /build_setup

FROM build-python as test-python
WORKDIR /github-api-discovery
COPY setup.cfg /github-api-discovery/setup.cfg
RUN python3 -m pip install pytest pytest-cov
COPY tests/ /github-api-discovery/tests/
RUN pytest --cov /github-api-discovery --cov-report=xml:coverage.xml -vv -x

FROM build-python as runtime
RUN chmod +x /github-api-discovery/src/main.py
CMD [ "python", "/github-api-discovery/src/main.py" ]
