from python:3.11-slim-bullseye as build
WORKDIR /app/src
RUN apt-get update -y && apt-get upgrade -y

copy src/ /app/src/
copy build_setup/requirements.txt /requirements.txt

RUN python3 -m pip install -r /requirements.txt
RUN chmod +x /app/src/main.py
CMD [ "python", "/app/src/main.py" ]

