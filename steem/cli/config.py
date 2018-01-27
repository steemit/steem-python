import json
import click
import os
from ..blockchain import Blockchain
from ..utils import prettydumps
from .. import __name__ as appname, __author__ as appauthor
from appdirs import user_config_dir

CONFIG_DIR = user_config_dir(appname, appauthor)
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, 'config.json')
NEW_CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, '.config.json.tmp')

@click.group()
def config():
    """Get and set configuration for this cli tool."""

@click.command()
def get():
    write_config_file({ "hello": "world", "foo": 42 })
    click.echo(prettydumps(read_config_file()))

def read_config_file():
    with open(CONFIG_FILE_PATH, 'r') as f:
        current_config = json.load(f)
    return current_config

def write_config_file(input):
    with open(NEW_CONFIG_FILE_PATH, 'w') as f:
        json.dump(input, f)
    os.rename(NEW_CONFIG_FILE_PATH, CONFIG_FILE_PATH)


config.add_command(get)
