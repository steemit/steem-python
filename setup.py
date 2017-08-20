# coding=utf-8
import os
import sys

from setuptools import find_packages
from setuptools import setup

import package_meta # this is a simple tool for loading metadata from Pipfile and other places

assert sys.version_info[0] == package_meta.required_python_major and sys.version_info[1] >= package_meta.required_python_minor, "%s requires Python %s or newer" % (package_meta.package_name, package_meta.required_python_ver)

# yapf: disable
setup(setup_requires=package_meta.dev_requirements,
      install_requires=package_meta.default_requirements,
      tests_require=package_meta.default_requirements+package_meta.dev_requirements)
