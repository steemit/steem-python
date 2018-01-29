#!/usr/bin/env python3
from pipenv.project import Project
from pipenv.utils import convert_deps_to_pip
from setuptools import setup, find_packages
import sys

if sys.version_info < (3, 0):
    sys.exit('Sorry, python2 is not yet supported. Please use python3.')

pfile = Project(chdir=False).parsed_pipfile
requirements = convert_deps_to_pip(pfile['packages'], r=False)
test_requirements = convert_deps_to_pip(pfile['dev-packages'], r=False)

setup(
    name='steem',
    version='0.18.103',
    description='Official Python Steem Library',
    # long_description = file: README.rst
    keywords=['steem', 'steemit', 'cryptocurrency', 'blockchain'],
    license='MIT',
    url='https://github.com/steemit/steem-python',
    maintainer='steemit_inc',
    maintainer_email='john@steemit.com',
    packages=find_packages(),
    setup_requires=[
        'pytest-runner',
        'pipenv',
    ],
    tests_require=test_requirements,
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'piston=steem.cli:legacyentry',
            'steempy=steem.cli:legacyentry',
            'steemtail=steem.cli:steemtailentry',
        ],
    },
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English', 'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Development Status :: 4 - Beta'
    ])
