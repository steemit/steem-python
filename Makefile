ROOT_DIR := .
DOCS_DIR := $(ROOT_DIR)/docs
DOCS_BUILD_DIR := $(DOCS_DIR)/_build


default: build

.PHONY: test run test-without-lint test-pylint fmt test-without-build

build: test-without-build README.rst
	docker build -t steemit/sbds .

run:
	docker run steemit/sbds

test: test-without-build build

test-without-build: test-without-lint test-pylint

test-without-lint:
	py.test tests

test-pylint:
	py.test --pylint -m pylint sbds

fmt:
	yapf --recursive --in-place --style pep8 .
	autopep8 --recursive --in-place .

README.rst: docs/src/README.rst 
	cd $(DOCS_DIR) && $(MAKE) README

clean: clean-build clean-pyc

clean-build:
	rm -fr build/ dist/ *.egg-info .eggs/ .tox/ __pycache__/ .cache/ .coverage htmlcov src

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

install: clean
	pip install -e .