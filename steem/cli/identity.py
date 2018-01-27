import json
import click

@click.group()
def identity():
    """Manage your persistent blockchain identities."""

@click.command(name='ls')
def ls():
    print("this lists your identities")
