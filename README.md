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

### Running tests

Run `pytest`. This will execute all unit tests within `./tests` with the prefix `test_*.py`.

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

### Linter and Formatting

This projects uses [Ruff](https://github.com/astral-sh/ruff) to manage code style, linter and formatting.

* To check code style problems: `ruff check`
* To auto-fix some problems: `ruff check --fix`
* To format files: `ruff format`
