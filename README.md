# Zipper
![ziper](resources/zipper.jpg)

Handle file zipping for DataMap.

## Prerequisites

- Docker
- Docker Compose

## Environment Setup

**Use Makefile targets to make your life easier!**

### To run in docker

1. Start docker containers

```sh
make ENV={env} docker-run
```

2. If you need to delete the docker containers

```sh
make ENV={env} docker-down
```

Obs.: this will delete the containers, but not the images generated nor the database data, since it uses a docker 
volume to persistently storage data.

### To run locally

1. Start the application

```sh
make ENV={env} python-run
```

### Unit tests

We are using [unittest](https://docs.python.org/3/library/unittest.html). See examples at https://docs.python.org/3/library/unittest.html

To run all tests from command line, use:

```sh
python -m unittest discover -p "*_test.py"
```

or:

```sh
make ENV=local python-test
```

To generage the code coverage reports, use:
```sh
# Run the tests and generage the .coverage file
coverage run -m unittest discover -p "*_test.py"

# Print the coverage report on console
coverage report

# Generate the coverage report in html
coverage html
```

### Deploying

> **WARNING:** The current deployment process causes downtime for services.

```sh
# Connect to USP infra
ssh datamap@143.107.102.162 -p 5010

# Navegate to the project folder
cd zipper

# Get the last (main) branch version
git pull

# Start python virtual env
python3 -m venv venv
. venv/bin/activate

# Install libraries
make ENV={env} python-pip-install

# Deactivate python virtual env
deactivate

# Refresh and deploy the last docker image.
make docker-deployment
```

### Accessing the application in prod

* Backend: `https://datamap.pcs.usp.br/zipper/api/v1/docs`

### Metrics

Prometheus metrics are served on port `9095` at `/metrics`. The port is only exposed on the docker network, never
published to the host; `9093` stays the API. The names follow the platform metric contract (gatekeeper RFC 005):

* HTTP: `datamap_http_requests_total`, `datamap_http_request_duration_seconds`, `datamap_http_request_size_bytes`,
  `datamap_http_response_size_bytes`, `datamap_http_requests_in_progress`. `route` is the route template; the
  health check (`GET /api/v1/health-check/`) is not counted.
* Zipping: `datamap_zip_jobs_total{outcome=success|failed|empty}`, `datamap_zip_jobs_in_progress`,
  `datamap_zip_duration_seconds`, `datamap_zip_input_bytes_total`, `datamap_zip_output_bytes_total`.

Uvicorn runs several workers, so the container sets `PROMETHEUS_MULTIPROC_DIR`, empties it at start, and runs
`python -m app.metrics_server` as one separate process that sums every worker's files. Without that variable
(local runs, tests) the metrics use the ordinary in-process registry.

### Linter and Formatting

This projects uses [Ruff](https://github.com/astral-sh/ruff) to manage code style, linter and formatting.

* To check code style problems: `ruff check`
* To auto-fix some problems: `ruff check --fix`
* To format files: `ruff format`
