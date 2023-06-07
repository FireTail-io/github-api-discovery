FROM golang:1.20.5-bullseye as build-golang

WORKDIR /src
COPY golang_analyser /src

RUN go build -buildmode=c-shared -o /dist/main.so .


FROM python:3.11-slim-bullseye as build-python

WORKDIR /github-api-discovery/src
RUN apt-get update -y && apt-get upgrade -y

COPY --from=build-golang /dist/main.so /golang_analyser/main.so
COPY src/ /github-api-discovery/src

COPY build_setup/requirements.txt /build_setup/requirements.txt
RUN python3 -m pip install -r /build_setup/requirements.txt
RUN rm -rf /build_setup


FROM build-python as test

WORKDIR /github-api-discovery

COPY tests/ /github-api-discovery/tests/
COPY setup.cfg /github-api-discovery/setup.cfg

RUN python3 -m pip install pytest

CMD [ "pytest" ]


FROM build-python as runtime

RUN chmod +x /github-api-discovery/src/main.py
CMD [ "python", "/github-api-discovery/src/main.py" ]
