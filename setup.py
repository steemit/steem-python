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
EMAIL = 'john@steemit.com'
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
    'pytest-runner',
    'yapf',
    'autopep8'
]

BUILD_REQUIRED = [
    'twine',
    'pypandoc',
    'recommonmark'
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


class UploadCommand(Command):
    """Support setup.py upload."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

<<<<<<< HEAD
pfile = Project(chdir=False).parsed_pipfile
requirements = convert_deps_to_pip(pfile['packages'], r=False)
test_requirements = convert_deps_to_pip(pfile['dev-packages'], r=False)
=======
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass
>>>>>>> b9cb650c91bbe252d86578c67980efb4ec2f1b98

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
    version='0.18.3',
    description=DESCRIPTION,
    keywords=['steem', 'steemit', 'cryptocurrency', 'blockchain'],
    long_description=long_description,
    author=AUTHOR,
    author_email=EMAIL,
    url=URL,
    packages=find_packages(exclude=('tests','scripts')),
    entry_points={
            'console_scripts': [
                'piston=steem.cli:legacyentry',
                'steempy=steem.cli:legacyentry',
                'steemtail=steem.cli:steemtailentry',
            ],
    },
    install_requires=REQUIRED,
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
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7'
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Development Status :: 4 - Beta'
    ],
    # $ setup.py publish support.
    cmdclass={
        'upload': UploadCommand,
    },
)