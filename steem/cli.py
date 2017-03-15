import click
from click import echo

context_settings = dict(help_option_names=['-h', '--help'])


@click.group(context_settings=context_settings)
def cli(ctx, **kwargs):
    ctx.obj = {}
    for k, v in kwargs.items():
        ctx.obj[k] = v
    echo()
