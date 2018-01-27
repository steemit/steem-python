import json
import click
from ..blockchain import Blockchain
from ..utils import prettydumps
from .. import __name__ as appname, __author__ as appauthor
from appdirs import user_config_dir

@click.group()
def config():
    """Get and set configuration for this cli tool."""

@click.command()
def get():
    print(user_config_dir(appname, appauthor) + "\n")

config.add_command(get)
