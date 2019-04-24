FROM python:2.7-alpine3.9

RUN mkdir /app
ADD hs110-exporter.py /app

# Number of seconds between pulls
ARG PULL_TIME

# IP or hostname to get data from
ARG TARGET_IP

ENTRYPOINT ["python", "/app/hs110-exporter.py"]