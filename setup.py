# coding=utf-8
import os
import sys

from setuptools import find_packages
from setuptools import setup

assert sys.version_info[0] == 3 and sys.version_info[1] >= 5, "steem requires Python 3.5 or newer"


def readme_file():
    return 'README.rst' if os.path.exists('README.rst') else 'README.md'


# yapf: disable
setup(
    name='steem',
    version='0.18.9',
    description='Official Python STEEM Library',
    long_description=open(readme_file()).read(),
    packages=find_packages(exclude=['scripts']),
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
        'appdirs',
        'ecdsa',
        'pylibscrypt',
        'scrypt',
        'pycrypto',
        'requests',
        'urllib3',
        'certifi',
        'ujson',
        'w3lib',
        'maya',
        'toolz',
        'funcy',
        'langdetect',
        'diff-match-patch',
        'prettytable',
        'voluptuous',
    ],
    entry_points={
        'console_scripts': [
            'steempy=steem.cli:legacy',
            'piston=steem.cli:legacy',
        ]
    })
