# -*- coding: utf-8 -*-
import click

from .chain import chain
from .identity import identity
from .config import config
from .report import report

@click.group(
    short_help='steem blockchain command line interface (CLI).'
)
def cli():
    """
    The steem CLI allows you to create, sign, and publish transactions on
    the Steem blockchain.
    """

cli.add_command(chain)
cli.add_command(identity)
cli.add_command(config)
cli.add_command(report)
