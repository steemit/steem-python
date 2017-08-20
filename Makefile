ROOT_DIR := .
DOCS_DIR := $(ROOT_DIR)/docs
DOCS_BUILD_DIR := $(DOCS_DIR)/_build

PROJECT_NAME := steem-python
PROJECT_DOCKER_TAG := steemit/$(PROJECT_NAME)


default: install-global

.PHONY: docker-image build-without-docker test-without-lint test-pylint test-without-build install-pipenv install-global clean clean-build

docker-image: clean
	docker build -t $(PROJECT_DOCKER_TAG) .

Pipfile.lock: Pipfile
	pipenv lock --three --hashes

requirements.txt: Pipfile.lock
	pipenv lock -r >requirements.txt

build-without-docker: requirements.txt Pipfile.lock
	mkdir -p build/wheel
	pipenv install --three --dev
	pipenv run python3.5 scripts/doc_rst_convert.py
	pipenv run python3.5 setup.py build
	rm README.rst

test: test-without-build

test-without-build: test-without-lint test-pylint

test-without-lint:
	py.test tests

test-pylint:
	py.test --pylint -m pylint sbds

clean: clean-build clean-pyc

clean-build:
	rm -fr build/ dist/ *.egg-info .eggs/ .tox/ __pycache__/ .cache/ .coverage htmlcov src

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

install-pipenv: clean
	pipenv run pip3.5 install -e .

install-global: clean
	python3.5 scripts/doc_rst_convert.py
	pip3.5 install -e .

pypi:
	python3.5 scripts/doc_rst_convert.py
	python3.5 setup.py bdist_wheel --universal
	python3.5 setup.py sdist bdist_wheel upload
	rm README.rst
