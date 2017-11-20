#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Note: To use the 'upload' functionality of this file, you must:
#   $ pip install twine

import io
import os
import sys
from shutil import rmtree

from setuptools import find_packages, setup, Command

# Package meta-data.
NAME = 'steem'
DESCRIPTION = 'Official python steem library.'
URL = 'https://github.com/steemit/steem-python'
EMAIL = 'python@steemit.com'
AUTHOR = 'Steemit'

# What packages are required for this module to be executed?
REQUIRED = [
    'appdirs',
    'certifi',
    'ecdsa>=0.13',
    'funcy',
    'prettytable',
    'pycrypto>=1.9.1',
    'pylibscrypt>=1.6.1',
    'scrypt>=0.8.0',
    'toolz',
    'ujson',
    'urllib3',
    'voluptuous'
]
TEST_REQUIRED = [
    'pep8',
    'pytest',
    'pytest-pylint',
    'pytest-xdist',
    'pytest-runner'
]

BUILD_REQUIRED = [
    'twine',
    'pypandoc',
    'wheel',
    'setuptools',
    'sphinx',
    'sphinx_rtd_theme'
]
# The rest you shouldn't have to touch too much :)
# ------------------------------------------------
# Except, perhaps the License and Trove Classifiers!
# If you do change the License, remember to change the Trove Classifier for that!

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.rst' is present in your MANIFEST.in file!
with io.open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = '\n' + f.read()

# Load the package's __version__.py module as a dictionary.
about = {}
with open(os.path.join(here, NAME, '__version__.py')) as f:
    exec(f.read(), about)


class UploadCommand(Command):
    """Support setup.py upload."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds…')
            rmtree(os.path.join(here, 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel (universal) distribution…')
        os.system('{0} setup.py sdist bdist_wheel --universal'.format(sys.executable))

        self.status('Uploading the package to PyPi via Twine…')
        os.system('twine upload dist/*')

        sys.exit()


# Where the magic happens:
setup(
    name=NAME,
    version=about['__version__'],
    description=DESCRIPTION,
    long_description=long_description,
    author=AUTHOR,
    author_email=EMAIL,
    url=URL,
    packages=find_packages(exclude=('tests','scripts')),
    entry_points={
        'console_scripts': ['piston = steem.cli:legacy',
                             'steempy = steem.cli:legacy',
                             'steemtail = steem.steemtail:main'
                             ],
    },
    install_requires=REQUIRED,
    python_requires='>=3.6',
    extras_require={
        'dev': TEST_REQUIRED + BUILD_REQUIRED,
        'build': BUILD_REQUIRED,
        'test': TEST_REQUIRED
    },
    tests_require=TEST_REQUIRED,
    include_package_data=True,
    license='MIT',
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython'
    ],
    # $ setup.py publish support.
    cmdclass={
        'upload': UploadCommand,
    },
)
