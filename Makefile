PROJECT := $(shell basename $(shell pwd))
PYTHON_FILES := steem steembase tests setup.py

.PHONY: clean test fmt install

clean:
	rm -rf build/ dist/ *.egg-info .eggs/ .tox/ \
		__pycache__/ .cache/ .coverage htmlcov src

test: clean
	python setup.py test

fmt:
	yapf --recursive --in-place --style pep8 $(PYTHON_FILES)
	pycodestyle $(PYTHON_FILES)

install:
	python setup.py install
