FROM docker.io/python:3.11-bookworm

ENV DEBIAN_FRONTEND=noninteractive
ARG UID=1026
ARG GID=100
RUN useradd --create-home --no-log-init -u "${UID}" -g "${GID}" python

COPY ./src/photomover.py /usr/bin
RUN apt update && apt install -y exiftool && rm -rf /var/lib/apt/lists/*
RUN mkdir /usr/bin/Image-ExifTool
RUN ln -s /usr/bin/exiftool /usr/bin/Image-ExifTool
USER python

ENTRYPOINT ["python", "/usr/bin/photomover.py"]