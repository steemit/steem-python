import json
import click
from ..blockchain import Blockchain
from ..utils import prettydumps

@click.group()
def chain():
    """Query the Steem blockchain."""

@chain.command(name='info')
def info():
    blockchain = Blockchain(mode="head")
    info = blockchain.info()
    print(prettydumps(info))
