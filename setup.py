# coding=utf-8
import sys
from setuptools import find_packages
from setuptools import setup

assert sys.version_info[0] == 3 and sys.version_info[1] >= 5, "steem requires Python 3.5 or newer"

# yapf: disable
setup(
    name='steem',
    version='0.1',
    description='Official Python STEEM Library',
    packages=find_packages(),
    setup_requires=['pytest-runner'],
    tests_require=['pytest',
                   'pep8',
                   'pytest-pylint',
                   'yapf',
                   'sphinx',
                   'recommonmark',
                   'sphinxcontrib-restbuilder',
                   'sphinxcontrib-programoutput',
                   'pytest-console-scripts'],

    install_requires=[
        'requests==2.11.1',
        'ujson',
        'urllib3',
        'certifi',
        'maya',
        'toolz',
        'funcy',
        'yapf',
    ],
    entry_points={
        'console_scripts': [
            'steem=steem.cli:sbds',
            'populate=sbds.storages.db.scripts.populate:populate'
        ]
    })
