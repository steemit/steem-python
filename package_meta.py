""" Some magic to grab requirements and stuff from Pipfile.lock (if it exists)
    If not found, grabs from requirements.txt, if not found there grabs from Pipfile
    Pipfile is loaded first, then Pipfile.lock or requirements.txt can override

    Sticking it all here means end users don't need to have Pipfile and pipenv installed
"""
import json
import os

from setuptools.config import read_configuration

import configparser

from pip.req import parse_requirements
from pip.download import PipSession

global required_python_ver
global default_requirements
global dev_requirements
global source_code_path
global pipfile_lock_data
global pipfile_path
global lockfile_path
global requires_file_path
global pipfile_data
global setup_cfg_path
global setup_cfg_data
global package_name
global package_ver

source_code_path = os.path.dirname(os.path.realpath(__file__))
pipfile_path       = '%s/Pipfile' % source_code_path
lockfile_path      = '%s/Pipfile.lock' % source_code_path
requires_file_path = '%s/requirements.txt' % source_code_path
setup_cfg_path     = '%s/setup.cfg' % source_code_path

setup_cfg_data = read_configuration(setup_cfg_path,ignore_option_errors=True)

pipfile_data = configparser.ConfigParser()

pipfile_data.read(pipfile_path)

required_python_ver = pipfile_data['requires'].get('python_version','3.5')
default_requirements = []
dev_requirements = []

for package_name in pipfile_data['packages']:
    package_ver = pipfile_data['packages'].get(package_name)
    if package_ver=='*':
       default_requirements.append(package_name)
    else:
       default_requirements.append('%s==%s' % (package_name,str(package_ver)))

for package_name in pipfile_data['dev-packages']:
    package_ver = pipfile_data['packages'].get(package_name)
    if package_ver==None:
       dev_requirements.append(package_name)
    else:
       dev_requirements.append('%s==%s' % (package_name,str(package_ver)))

if os.path.exists(lockfile_path):
   with open(lockfile_path) as lockfile:
        lockfile_data = json.load(lockfile)

   required_python_ver = lockfile_data['_meta']['requires']['python_version']
   default_requirements = []
   for k,v in lockfile_data['default'].items():
       default_requirements.append('%s%s' % (k,v['version']))
else:
   required_python_ver = '3.6'
   default_requirements = [str(ir.req) for ir in parse_requirements(requires_file_path,session=PipSession())]

required_python_major,required_python_minor = [int(x) for x in required_python_ver.split('.')[:2]]


package_name = setup_cfg_data['metadata']['name']
package_ver  = setup_cfg_data['metadata']['version']


if __name__=='__main__':
   print('Required python version: %s' % required_python_ver)
   print('Required default packages:')
   for package_name in default_requirements:
       print('\t%s' % package_name)
   print('Required development packages:')
   for package_name in dev_requirements:
       print('\t%s' % package_name)
