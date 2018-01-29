PROJECT := $(shell basename $(shell pwd))
PYTHON_FILES := steem steembase tests setup.py

default: docker_test

.PHONY: fmt init test docker_test

docker_test:
	docker build .

clean:
	rm -rf build/ dist/ *.egg-info .eggs/ .tox/ \
		.cache/ .coverage htmlcov src

test: clean
	pip3 install --upgrade pip
	pip3 install --upgrade pipenv
	pipenv install --three --dev
	pipenv install .
	pipenv run py.test

fmt:
	pipenv run yapf --recursive --in-place --style pep8 $(PYTHON_FILES)
	pipenv run pycodestyle $(PYTHON_FILES)

init:
	pip3 install --upgrade pip
	pip3 install --upgrade pipenv
	pipenv lock
	pipenv install --three --dev
	pipenv install .
