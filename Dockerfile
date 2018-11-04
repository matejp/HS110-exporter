FROM python:2.7-alpine

RUN mkdir /app
ADD hs110-exporter.py /app

# ENTRYPOINT ["/usr/bin/dumb-init"]
CMD ["/app/hs110-exporter.py"]