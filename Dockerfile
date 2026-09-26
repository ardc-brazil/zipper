FROM python:3.10.12-alpine as base

FROM base as builder

RUN mkdir /install
RUN apk update && apk add gcc python3-dev musl-dev libffi-dev
WORKDIR /install
COPY requirements.txt /requirements.txt
ARG ENV
COPY ${ENV}_config.yml /${ENV}_config.yml
RUN pip install --prefix=/install -r /requirements.txt

FROM base

COPY --from=builder /install /usr/local
COPY . /app
RUN apk --no-cache add libpq
WORKDIR /app
EXPOSE 9093 9095

ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus-multiproc

# Emptied before uvicorn forks; the metrics server is its own process so 9095 is bound once, not per worker.
CMD ["sh", "-c", "rm -rf \"$PROMETHEUS_MULTIPROC_DIR\" && mkdir -p \"$PROMETHEUS_MULTIPROC_DIR\" && { python -m app.metrics_server & } && exec uvicorn app:create_app --host 0.0.0.0 --port 9093 --workers 3"]
