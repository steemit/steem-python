default: run_tests_in_vagrant

.PHONY: run_tests_in_vagrant

run_tests_in_vagrant:
	vagrant destroy -f
	vagrant up

clean:
	rm -rf build/ dist/ *.egg-info .eggs/ .tox/ \
		__pycache__/ .cache/ .coverage htmlcov src
