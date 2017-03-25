#!/usr/bin/env bash
python setup.py bdist_wheel --universal
python setup.py sdist bdist_wheel upload
