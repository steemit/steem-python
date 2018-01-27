PROJECT := $(shell basename $(shell pwd))

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
	pipenv run yapf --recursive --in-place --style pep8 $(PROJECT)
	pipenv run autopep8 --recursive --in-place $(PROJECT)

init:
	pip3 install --upgrade pip
	pip3 install --upgrade pipenv
	pipenv lock
	pipenv install --three --dev
	pipenv install .
