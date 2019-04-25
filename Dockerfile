FROM python:2.7-alpine3.9

RUN mkdir /app
ADD hs110-exporter.py /app

# Number of seconds between pulls
ARG PULL_TIME
ENV PULL_TIME=$PULL_TIME

# IP or hostname to get data from
ARG TARGET_IP
ENV TARGET_IP=$TARGET_IP

# port number to expose the prometheus metrics on
ARG EXPOSE_PORT
ENV EXPOSE_PORT=$EXPOSE_PORT

EXPOSE $EXPOSE_PORT

ENTRYPOINT ["python", "/app/hs110-exporter.py"]