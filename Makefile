PROJECT := $(shell basename $(shell pwd))
MODULES := steem steembase tests

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
	pipenv run yapf --recursive --in-place --style pep8 $(MODULES)
	#pipenv run autopep8 --recursive --in-place $(MODULES)
	pipenv run pycodestyle $(MODULES)

init:
	pip3 install --upgrade pip
	pip3 install --upgrade pipenv
	pipenv lock
	pipenv install --three --dev
	pipenv install .
