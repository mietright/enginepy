.PHONY: format format-test check fix clean clean-build clean-pyc clean-test coverage install pylint pylint-quick pyre test publish uv-check publish isort isort-check docker-push docker-build migrate lint

APP_ENV ?= dev
VERSION := `cat VERSION`
package := enginepy
NAMESPACE := enginepy

DOCKER_BUILD_ARGS ?= "-q"

all: fix

.PHONY: clear-test-db create-cache-db clean-db .check-clear

help:
	@echo "clean - remove all build, test, coverage and Python artifacts"
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean-test - remove test and coverage artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "test-all - run tests on every Python version with tox"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "release - package and upload a release"
	@echo "dist - package"
	@echo "install - install the package to the active Python's site-packages"
	@echo "migrate - Execute a db migration"

clean: clean-build clean-pyc clean-test

clean-build:
	rm -rf build/ dist/ .eggs/
	find . \( -path "./.venv" -o -path "./.cache" \) -prune -o \
	       \( -name '*.egg-info' -o -name '*.egg' \) -exec rm -rf {} +

clean-pyc:
	rm -f pyrightconfig.json
	find . \( -path "./.venv" -o -path "./.cache" \) -prune -o \
	       \( -name '*.pyc' -o -name '*.pyo' -o -name '*~' -o -name 'flycheck_*' \) -exec rm -f {} +
	find . \( -path "./.venv" -o -path "./.cache" \) -prune -o \
	       \( -name '__pycache__' -o -name '.mypy_cache' -o -name '.pyre' \) -exec rm -rf {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -f coverage.xml
	rm -f report.xml

test:
	ENGINEPY_CONFIG=tests/data/test_config.yaml uv run py.test --cov=$(package) --verbose tests --cov-report=html --cov-report=term --cov-report xml:coverage.xml --cov-report=term-missing --junitxml=report.xml --asyncio-mode=auto

coverage:
	uv run coverage run --source $(package) setup.py test
	uv run coverage report -m
	uv run coverage html
	$(BROWSER) htmlcov/index.html

install: clean
	uv install

pylint-quick:
	uv run pylint --rcfile=.pylintrc $(package)  -E -r y

pylint:
	uv run pylint --rcfile=".pylintrc" $(package)

pyright:
	uv run pyright
lint: format-test isort-check ruff uv-check
check: lint pyright

pyre: pyre-check

pyre-check:
	uv run pyre --noninteractive check 2>/dev/null

format:
	uv run ruff format $(package)

format-test:
	uv run ruff format $(package) --check

uv-check:
	uv lock --locked --offline

publish: clean
	uv build
	uv publish

isort:
	uv run isort .
	uv run ruff check --select I $(package) tests --fix

isort-check:
	uv run ruff check --select I $(package) tests
	uv run isort --diff --check .

ruff:
	uv run ruff check

fix: format isort
	uv run ruff check --fix

.ONESHELL:
pyrightconfig:
	jq \
      --null-input \
      --arg venv "$$(basename $$(uv env info -p))" \
      --arg venvPath "$$(dirname $$(uv env info -p))" \
      '{ "venv": $$venv, "venvPath": $$venvPath }' \
      > pyrightconfig.json

rename:
	ack enginepy -l | xargs -i{} sed -r -i "s/enginepy/enginepy/g" {}
	ack Enginepy -i -l | xargs -i{} sed -r -i "s/Enginepy/Enginepy/g" {}
	ack ENGINEPY -i -l | xargs -i{} sed -r -i "s/ENGINEPY/ENGINEPY/g" {}

ipython:
	uv run ipython


docker-push: docker-build
	docker push img.conny.dev/conny/enginepy:latest

docker-build:
	docker build --network=host -t img.conny.dev/conny/enginepy:latest .
