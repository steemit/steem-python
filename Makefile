ROOT_DIR := .
DOCS_DIR := $(ROOT_DIR)/docs
DOCS_BUILD_DIR := $(DOCS_DIR)/_build

PROJECT_NAME := steem-python
PROJECT_DOCKER_TAG := steemit/$(PROJECT_NAME)

PYTHON := python3.6

.PHONY: help
help:
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)


.PHONY: docker-image
docker-image: clean README.rst ## build docker image for testing
	docker build -t $(PROJECT_DOCKER_TAG) .

.PHONY: install
install: clean README.rst ## install dev environment
	-pipenv --rm
	touch Pipfile
	pipenv install --python $(PYTHON) --skip-lock
	if [[ $(shell uname) == 'Darwin' ]]; then \
	brew install openssl; \
	env LDFLAGS="-L$(shell brew --prefix openssl)/lib" CFLAGS="-I$(shell brew --prefix openssl)/include" pipenv run python setup.py develop; \
	else \
		pipenv run python setup.py develop; \
	fi
	pipenv run pip3 install -e .[dev]


README.rst: README.md
	pandoc --from=markdown --to=rst --output=$@ README.md

.PHONY: build
build: README.rst
	mkdir -p build/wheel
	pipenv run $(PYTHON) setup.py build
	rm README.rst

.PHONY: test-without-lint
test-without-lint:
	pipenv run $(PYTHON) setup.py pytest

.PHONY: test-pylint
test-pylint:
	pipenv run pytest -v --pylint steem steembase

.PHONY: clean
clean: clean-build clean-pyc

.PHONY: clean-build
clean-build:
	rm -fr build/ dist/ *.egg-info .eggs/ .tox/ __pycache__/ .cache/ .coverage htmlcov src README.rst

.PHONY: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

.PHONY: pypi
pypi:
	pipenv run $(PYTHON) scripts/doc_rst_convert.py
	pipenv run $(PYTHON) setup.py bdist_wheel --universal
	pipenv run $(PYTHON) setup.py sdist bdist_wheel upload
	rm README.rst
