import json
import click
import os
from ..blockchain import Blockchain
from ..utils import prettydumps
from .. import __name__ as appname, __author__ as appauthor
from appdirs import user_config_dir


DEFAULT_CONFIG = {
    'output_format': 'json',
    'default_username': None,
}

@click.group()
def config():
    """Get and set configuration for this cli tool."""

@click.command()
def get(key):
    myconfig = get_configdict()
    click.echo(prettydumps(myconfig))

config.add_command(get)

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_configdict():
    CONFIG_DIR = user_config_dir(appname, appauthor)
    CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, 'config.json')

    ensure_dir(CONFIG_FILE_PATH)
    creating = True
    if os.path.exists(CONFIG_FILE_PATH):
        creating = False
    configdict = JsonDict(CONFIG_FILE_PATH, autosave=True)

    # populate default values in on-disk config if not present
    for key in DEFAULT_CONFIG.keys():
        if key not in configdict:
            configdict[key] = DEFAULT_CONFIG[key]
