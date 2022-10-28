FROM python:3.10-slim-bullseye

RUN apt-get -y update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY . /opt

RUN pip install -e /opt/

ENTRYPOINT  ["dggs_tbx"]