from python:3.11-slim-bullseye as build
WORKDIR /app/src
RUN apt-get update -y && apt-get upgrade -y

copy src /app/src

RUN python3 -m pip install -r requirements.txt
