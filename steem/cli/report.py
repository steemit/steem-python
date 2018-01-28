import click
import json
import requests
import time
from decimal import Decimal
from ..account import Account
from ..amount import Amount
from ..blockchain import Blockchain
from ..coinmarketcap import fetch_historic_steem_prices
from ..utils import prettydumps

@click.group()
def report():
    """Generate reports from the blockchain's history."""

@click.command()
@click.option('--username',help='username to fetch history for',
        required=True)
def trades(username):
    """Report on internal market trade activity."""
    dhistprice = fetch_historic_steem_prices()

    account = Account(username)
    history = list(
        account.get_account_history(-1, 10000, filter_by='fill_order')
    )

    report = convert_ops_to_report(history)

    for row in report:
        row.append(float(dhistprice[row[0]]))
        if row[4]['asset'] == 'STEEM':
            row.append(float(
                Decimal(dhistprice[row[0]]) * Decimal(row[4]['amount'])
            ))
        if row[6]['asset'] == 'STEEM':
            row.append(float(
                Decimal(dhistprice[row[0]]) * Decimal(row[6]['amount'])
            ))

    click.echo(prettydumps(report))
    #blockchain = Blockchain(mode="head")
    #info = blockchain.info()
    #click.echo(prettydumps(info))


def convert_ops_to_report(ops):
    output = []
    for op in ops:
        rec = []
        rec.append(str(op['timestamp'])[:10])
        rec.append(op['trx_id'])
        rec.append(op['timestamp'])
        rec.append(op['current_owner'])
        rec.append(Amount(op['current_pays']))
        rec.append(op['open_owner'])
        rec.append(Amount(op['open_pays']))
        output.append(rec)
    return output

report.add_command(trades)
