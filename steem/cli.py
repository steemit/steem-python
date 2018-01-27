import argparse
import json
import logging
import os
import re
import sys

import pkg_resources
import steem as stm
from prettytable import PrettyTable
from steembase.storage import configStorage
from steembase.account import PrivateKey

from .account import Account
from .amount import Amount
from .block import Block
from .blockchain import Blockchain
from .dex import Dex
from .instance import shared_steemd_instance
from .post import Post
from .utils import construct_identifier, strfage
from .witness import Witness

availableConfigurationKeys = [
    "default_account",
    "default_vote_weight",
    "nodes",
]


def legacyentry():
    """
    Piston like cli application.
    This will be re-written as a @click app in the future.
    """
    global args

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Command line tool to interact with the Steem network")
    """
        Default settings for all tools
    """
    parser.add_argument(
        '--node',
        type=str,
        default=configStorage["node"],
        help='URL for public Steem API (default: "https://steemd.steemit.com")'
    )

    parser.add_argument(
        '--no-broadcast',
        '-d',
        action='store_true',
        help='Do not broadcast anything')
    parser.add_argument(
        '--no-wallet',
        '-p',
        action='store_true',
        help='Do not load the wallet')
    parser.add_argument(
        '--unsigned',
        '-x',
        action='store_true',
        help='Do not try to sign the transaction')
    parser.add_argument(
        '--expires',
        '-e',
        default=60,
        help='Expiration time in seconds (defaults to 30)')
    parser.add_argument(
        '--verbose', '-v', type=int, default=3, help='Verbosity')
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s {version}'.format(
            version=pkg_resources.require("steem")[0].version))

    subparsers = parser.add_subparsers(help='sub-command help')
    """
        Command "set"
    """
    setconfig = subparsers.add_parser('set', help='Set configuration')
    setconfig.add_argument(
        'key',
        type=str,
        choices=availableConfigurationKeys,
        help='Configuration key')
    setconfig.add_argument('value', type=str, help='Configuration value')
    setconfig.set_defaults(command="set")
    """
        Command "config"
    """
    configconfig = subparsers.add_parser(
        'config', help='Show local configuration')
    configconfig.set_defaults(command="config")
    """
        Command "info"
    """
    parser_info = subparsers.add_parser(
        'info', help='Show basic STEEM blockchain info')
    parser_info.set_defaults(command="info")
    parser_info.add_argument(
        'objects',
        nargs='*',
        type=str,
        help='General information about the blockchain, a block, an account'
        ' name, a post, a public key, ...')
    """
        Command "changewalletpassphrase"
    """
    changepasswordconfig = subparsers.add_parser(
        'changewalletpassphrase', help='Change wallet password')
    changepasswordconfig.set_defaults(command="changewalletpassphrase")
    """
        Command "addkey"
    """
    addkey = subparsers.add_parser(
        'addkey', help='Add a new key to the wallet')
    addkey.add_argument(
        '--unsafe-import-key',
        nargs='*',
        type=str,
        help='private key to import into the wallet (unsafe, unless you ' +
        'delete your shell history)')
    addkey.set_defaults(command="addkey")

    parsewif = subparsers.add_parser(
        'parsewif', help='Parse a WIF private key without importing')
    parsewif.add_argument(
        '--unsafe-import-key',
        nargs='*',
        type=str,
        help='WIF key to parse (unsafe, delete your bash history)')
    parsewif.set_defaults(command='parsewif')
    """
        Command "delkey"
    """
    delkey = subparsers.add_parser(
        'delkey', help='Delete keys from the wallet')
    delkey.add_argument(
        'pub',
        nargs='*',
        type=str,
        help='the public key to delete from the wallet')
    delkey.set_defaults(command="delkey")
    """
        Command "getkey"
    """
    getkey = subparsers.add_parser(
        'getkey', help='Dump the privatekey of a pubkey from the wallet')
    getkey.add_argument(
        'pub',
        type=str,
        help='the public key for which to show the private key')
    getkey.set_defaults(command="getkey")
    """
        Command "listkeys"
    """
    listkeys = subparsers.add_parser(
        'listkeys', help='List available keys in your wallet')
    listkeys.set_defaults(command="listkeys")
    """
        Command "listaccounts"
    """
    listaccounts = subparsers.add_parser(
        'listaccounts', help='List available accounts in your wallet')
    listaccounts.set_defaults(command="listaccounts")
    """
        Command "upvote"
    """
    parser_upvote = subparsers.add_parser('upvote', help='Upvote a post')
    parser_upvote.set_defaults(command="upvote")
    parser_upvote.add_argument(
        'post',
        type=str,
        help='@author/permlink-identifier of the post to upvote ' +
        'to (e.g. @xeroc/python-steem-0-1)')
    parser_upvote.add_argument(
        '--account',
        type=str,
        required=False,
        default=configStorage["default_account"],
        help='The voter account name')
    parser_upvote.add_argument(
        '--weight',
        type=float,
        default=configStorage["default_vote_weight"],
        required=False,
        help='Actual weight (from 0.1 to 100.0)')
    """
        Command "downvote"
    """
    parser_downvote = subparsers.add_parser('downvote', help='Downvote a post')
    parser_downvote.set_defaults(command="downvote")
    parser_downvote.add_argument(
        '--account',
        type=str,
        default=configStorage["default_account"],
        help='The voter account name')
    parser_downvote.add_argument(
        'post',
        type=str,
        help='@author/permlink-identifier of the post to downvote ' +
        'to (e.g. @xeroc/python-steem-0-1)')
    parser_downvote.add_argument(
        '--weight',
        type=float,
        default=configStorage["default_vote_weight"],
        required=False,
        help='Actual weight (from 0.1 to 100.0)')
    """
        Command "transfer"
    """
    parser_transfer = subparsers.add_parser('transfer', help='Transfer STEEM')
    parser_transfer.set_defaults(command="transfer")
    parser_transfer.add_argument('to', type=str, help='Recipient')
    parser_transfer.add_argument(
        'amount', type=float, help='Amount to transfer')
    parser_transfer.add_argument(
        'asset',
        type=str,
        choices=["STEEM", "SBD"],
        help='Asset to transfer (i.e. STEEM or SDB)')
    parser_transfer.add_argument(
        'memo', type=str, nargs="?", default="", help='Optional memo')
    parser_transfer.add_argument(
        '--account',
        type=str,
        required=False,
        default=configStorage["default_account"],
        help='Transfer from this account')
    """
        Command "powerup"
    """
    parser_powerup = subparsers.add_parser(
        'powerup', help='Power up (vest STEEM as STEEM POWER)')
    parser_powerup.set_defaults(command="powerup")
    parser_powerup.add_argument(
        'amount', type=str, help='Amount of VESTS to powerup')
    parser_powerup.add_argument(
        '--account',
        type=str,
        required=False,
        default=configStorage["default_account"],
        help='Powerup from this account')
    parser_powerup.add_argument(
        '--to',
        type=str,
        required=False,
        default=None,
        help='Powerup this account')
    """
        Command "powerdown"
    """
    parser_powerdown = subparsers.add_parser(
        'powerdown',
        help='Power down (start withdrawing STEEM from steem POWER)')
    parser_powerdown.set_defaults(command="powerdown")
    parser_powerdown.add_argument(
        'amount', type=str, help='Amount of VESTS to powerdown')
    parser_powerdown.add_argument(
        '--account',
        type=str,
        required=False,
        default=configStorage["default_account"],
        help='powerdown from this account')
    """
        Command "powerdownroute"
    """
    parser_powerdownroute = subparsers.add_parser(
        'powerdownroute', help='Setup a powerdown route')
    parser_powerdownroute.set_defaults(command="powerdownroute")
    parser_powerdownroute.add_argument(
        'to',
        type=str,
        default=configStorage["default_account"],
        help='The account receiving either VESTS/SteemPower or STEEM.')
    parser_powerdownroute.add_argument(
        '--percentage',
        type=float,
        default=100,
        help='The percent of the withdraw to go to the "to" account')
    parser_powerdownroute.add_argument(
        '--account',
        type=str,
        default=configStorage["default_account"],
        help='The account which is powering down')
    parser_powerdownroute.add_argument(
        '--auto_vest',
        action='store_true',
        help=('Set to true if the from account should receive the VESTS as'
              'VESTS, or false if it should receive them as STEEM.'))
    """
        Command "convert"
    """
    parser_convert = subparsers.add_parser(
        'convert',
        help='Convert STEEMDollars to Steem (takes a week to settle)')
    parser_convert.set_defaults(command="convert")
    parser_convert.add_argument(
        'amount', type=float, help='Amount of SBD to convert')
    parser_convert.add_argument(
        '--account',
        type=str,
        required=False,
        default=configStorage["default_account"],
        help='Convert from this account')
    """
        Command "balance"
    """
    parser_balance = subparsers.add_parser(
        'balance', help='Show the balance of one more more accounts')
    parser_balance.set_defaults(command="balance")
    parser_balance.add_argument(
        'account',
        type=str,
        nargs="*",
        default=configStorage["default_account"],
        help='balance of these account (multiple accounts allowed)')
    """
        Command "interest"
    """
    interest = subparsers.add_parser(
        'interest', help='Get information about interest payment')
    interest.set_defaults(command="interest")
    interest.add_argument(
        'account',
        type=str,
        nargs="*",
        default=configStorage["default_account"],
        help='Inspect these accounts')
    """
        Command "permissions"
    """
    parser_permissions = subparsers.add_parser(
        'permissions', help='Show permissions of an account')
    parser_permissions.set_defaults(command="permissions")
    parser_permissions.add_argument(
        'account',
        type=str,
        nargs="?",
        default=configStorage["default_account"],
        help='Account to show permissions for')
    """
        Command "allow"
    """
    parser_allow = subparsers.add_parser(
        'allow', help='Allow an account/key to interact with your account')
    parser_allow.set_defaults(command="allow")
    parser_allow.add_argument(
        '--account',
        type=str,
        nargs="?",
        default=configStorage["default_account"],
        help='The account to allow action for')
    parser_allow.add_argument(
        'foreign_account',
        type=str,
        nargs="?",
        help='The account or key that will be allowed to interact with ' +
        'your account')
    parser_allow.add_argument(
        '--permission',
        type=str,
        default="posting",
        choices=["owner", "posting", "active"],
        help='The permission to grant (defaults to "posting")')
    parser_allow.add_argument(
        '--weight',
        type=int,
        default=None,
        help=('The weight to use instead of the (full) threshold. '
              'If the weight is smaller than the threshold, '
              'additional signatures are required'))
    parser_allow.add_argument(
        '--threshold',
        type=int,
        default=None,
        help=('The permission\'s threshold that needs to be reached '
              'by signatures to be able to interact'))
    """
        Command "disallow"
    """
    parser_disallow = subparsers.add_parser(
        'disallow',
        help='Remove allowance an account/key to interact with your account')
    parser_disallow.set_defaults(command="disallow")
    parser_disallow.add_argument(
        '--account',
        type=str,
        nargs="?",
        default=configStorage["default_account"],
        help='The account to disallow action for')
    parser_disallow.add_argument(
        'foreign_account',
        type=str,
        help='The account or key whose allowance to interact as your ' +
        'account will be removed')
    parser_disallow.add_argument(
        '--permission',
        type=str,
        default="posting",
        choices=["owner", "posting", "active"],
        help='The permission to remove (defaults to "posting")')
    parser_disallow.add_argument(
        '--threshold',
        type=int,
        default=None,
        help=('The permission\'s threshold that needs to be reached '
              'by signatures to be able to interact'))
    """
        Command "newaccount"
    """
    parser_newaccount = subparsers.add_parser(
        'newaccount', help='Create a new account')
    parser_newaccount.set_defaults(command="newaccount")
    parser_newaccount.add_argument(
        'accountname', type=str, help='New account name')
    parser_newaccount.add_argument(
        '--account',
        type=str,
        required=False,
        default=configStorage["default_account"],
        help='Account that pays the fee')
    parser_newaccount.add_argument(
        '--fee',
        type=str,
        required=False,
        default='0 STEEM',
        help='Base Fee to pay. Delegate the rest.')
    """
        Command "importaccount"
    """
    parser_importaccount = subparsers.add_parser(
        'importaccount', help='Import an account using a passphrase')
    parser_importaccount.set_defaults(command="importaccount")
    parser_importaccount.add_argument('account', type=str, help='Account name')
    parser_importaccount.add_argument(
        '--roles',
        type=str,
        nargs="*",
        default=["active", "posting", "memo"],  # no owner
        help='Import specified keys (owner, active, posting, memo)')
    """
        Command "updateMemoKey"
    """
    parser_updateMemoKey = subparsers.add_parser(
        'updatememokey', help='Update an account\'s memo key')
    parser_updateMemoKey.set_defaults(command="updatememokey")
    parser_updateMemoKey.add_argument(
        '--account',
        type=str,
        nargs="?",
        default=configStorage["default_account"],
        help='The account to updateMemoKey action for')
    parser_updateMemoKey.add_argument(
        '--key', type=str, default=None, help='The new memo key')
    """
        Command "approvewitness"
    """
    parser_approvewitness = subparsers.add_parser(
        'approvewitness', help='Approve a witnesses')
    parser_approvewitness.set_defaults(command="approvewitness")
    parser_approvewitness.add_argument(
        'witness', type=str, help='Witness to approve')
    parser_approvewitness.add_argument(
        '--account',
        type=str,
        required=False,
        default=configStorage["default_account"],
        help='Your account')
    """
        Command "disapprovewitness"
    """
    parser_disapprovewitness = subparsers.add_parser(
        'disapprovewitness', help='Disapprove a witnesses')
    parser_disapprovewitness.set_defaults(command="disapprovewitness")
    parser_disapprovewitness.add_argument(
        'witness', type=str, help='Witness to disapprove')
    parser_disapprovewitness.add_argument(
        '--account',
        type=str,
        required=False,
        default=configStorage["default_account"],
        help='Your account')
    """
        Command "sign"
    """
    parser_sign = subparsers.add_parser(
        'sign',
        help='Sign a provided transaction with available and required keys')
    parser_sign.set_defaults(command="sign")
    parser_sign.add_argument(
        '--file',
        type=str,
        required=False,
        help='Load transaction from file. If "-", read from ' +
        'stdin (defaults to "-")')
    """
        Command "broadcast"
    """
    parser_broadcast = subparsers.add_parser(
        'broadcast', help='broadcast a signed transaction')
    parser_broadcast.set_defaults(command="broadcast")
    parser_broadcast.add_argument(
        '--file',
        type=str,
        required=False,
        help='Load transaction from file. If "-", read from ' +
        'stdin (defaults to "-")')
    """
        Command "orderbook"
    """
    orderbook = subparsers.add_parser(
        'orderbook', help='Obtain orderbook of the internal market')
    orderbook.set_defaults(command="orderbook")
    orderbook.add_argument(
        '--chart',
        action='store_true',
        help="Enable charting (requires matplotlib)")
    """
        Command "buy"
    """
    parser_buy = subparsers.add_parser(
        'buy', help='Buy STEEM or SBD from the internal market')
    parser_buy.set_defaults(command="buy")
    parser_buy.add_argument('amount', type=float, help='Amount to buy')
    parser_buy.add_argument(
        'asset',
        type=str,
        choices=["STEEM", "SBD"],
        help='Asset to buy (i.e. STEEM or SDB)')
    parser_buy.add_argument(
        'price', type=float, help='Limit buy price denoted in (SBD per STEEM)')
    parser_buy.add_argument(
        '--account',
        type=str,
        required=False,
        default=configStorage["default_account"],
        help='Buy with this account (defaults to "default_account")')
    """
        Command "sell"
    """
    parser_sell = subparsers.add_parser(
        'sell', help='Sell STEEM or SBD from the internal market')
    parser_sell.set_defaults(command="sell")
    parser_sell.add_argument('amount', type=float, help='Amount to sell')
    parser_sell.add_argument(
        'asset',
        type=str,
        choices=["STEEM", "SBD"],
        help='Asset to sell (i.e. STEEM or SDB)')
    parser_sell.add_argument(
        'price',
        type=float,
        help='Limit sell price denoted in (SBD per STEEM)')
    parser_sell.add_argument(
        '--account',
        type=str,
        required=False,
        default=configStorage["default_account"],
        help='Sell from this account (defaults to "default_account")')
    """
        Command "cancel"
    """
    parser_cancel = subparsers.add_parser(
        'cancel', help='Cancel order in the internal market')
    parser_cancel.set_defaults(command="cancel")
    parser_cancel.add_argument('orderid', type=int, help='Orderid')
    parser_cancel.add_argument(
        '--account',
        type=str,
        required=False,
        default=configStorage["default_account"],
        help='Cancel from this account (defaults to "default_account")')
    """
        Command "resteem"
    """
    parser_resteem = subparsers.add_parser(
        'resteem', help='Resteem an existing post')
    parser_resteem.set_defaults(command="resteem")
    parser_resteem.add_argument(
        'identifier',
        type=str,
        help='@author/permlink-identifier of the post to resteem')
    parser_resteem.add_argument(
        '--account',
        type=str,
        required=False,
        default=configStorage["default_account"],
        help='Resteem as this user (requires to have the ' +
        'key installed in the wallet)')
    """
        Command "follow"
    """
    parser_follow = subparsers.add_parser(
        'follow', help='Follow another account')
    parser_follow.set_defaults(command="follow")
    parser_follow.add_argument('follow', type=str, help='Account to follow')
    parser_follow.add_argument(
        '--account',
        type=str,
        required=False,
        default=configStorage["default_account"],
        help='Follow from this account')
    parser_follow.add_argument(
        '--what',
        type=str,
        required=False,
        nargs="*",
        default=["blog"],
        help='Follow these objects (defaults to "blog")')
    """
        Command "unfollow"
    """
    parser_unfollow = subparsers.add_parser(
        'unfollow', help='unfollow another account')
    parser_unfollow.set_defaults(command="unfollow")
    parser_unfollow.add_argument(
        'unfollow', type=str, help='Account to unfollow')
    parser_unfollow.add_argument(
        '--account',
        type=str,
        required=False,
        default=configStorage["default_account"],
        help='Unfollow from this account')
    parser_unfollow.add_argument(
        '--what',
        type=str,
        required=False,
        nargs="*",
        default=[],
        help='Unfollow these objects (defaults to "blog")')
    """
        Command "setprofile"
    """
    parser_setprofile = subparsers.add_parser(
        'setprofile', help='Set a variable in an account\'s profile')
    parser_setprofile.set_defaults(command="setprofile")
    parser_setprofile.add_argument(
        '--account',
        type=str,
        required=False,
        default=configStorage["default_account"],
        help='setprofile as this user (requires to have the key ' +
        'installed in the wallet)')
    parser_setprofile_a = parser_setprofile.add_argument_group(
        'Multiple keys at once')
    parser_setprofile_a.add_argument(
        '--pair', type=str, nargs='*', help='"Key=Value" pairs')
    parser_setprofile_b = parser_setprofile.add_argument_group(
        'Just a single key')
    parser_setprofile_b.add_argument(
        'variable', type=str, nargs='?', help='Variable to set')
    parser_setprofile_b.add_argument(
        'value', type=str, nargs='?', help='Value to set')
    """
        Command "delprofile"
    """
    parser_delprofile = subparsers.add_parser(
        'delprofile', help='Set a variable in an account\'s profile')
    parser_delprofile.set_defaults(command="delprofile")
    parser_delprofile.add_argument(
        '--account',
        type=str,
        required=False,
        default=configStorage["default_account"],
        help='delprofile as this user (requires to have the ' +
        'key installed in the wallet)')
    parser_delprofile.add_argument(
        'variable', type=str, nargs='*', help='Variable to set')
    """
        Command "witnessupdate"
    """
    parser_witnessprops = subparsers.add_parser(
        'witnessupdate', help='Change witness properties')
    parser_witnessprops.set_defaults(command="witnessupdate")
    parser_witnessprops.add_argument(
        '--witness',
        type=str,
        default=configStorage["default_account"],
        help='Witness name')
    parser_witnessprops.add_argument(
        '--maximum_block_size',
        type=float,
        required=False,
        help='Max block size')
    parser_witnessprops.add_argument(
        '--account_creation_fee',
        type=float,
        required=False,
        help='Account creation fee')
    parser_witnessprops.add_argument(
        '--sbd_interest_rate',
        type=float,
        required=False,
        help='SBD interest rate in percent')
    parser_witnessprops.add_argument(
        '--url', type=str, required=False, help='Witness URL')
    parser_witnessprops.add_argument(
        '--signing_key', type=str, required=False, help='Signing Key')
    """
        Command "witnesscreate"
    """
    parser_witnesscreate = subparsers.add_parser(
        'witnesscreate', help='Create a witness')
    parser_witnesscreate.set_defaults(command="witnesscreate")
    parser_witnesscreate.add_argument('witness', type=str, help='Witness name')
    parser_witnesscreate.add_argument(
        'signing_key', type=str, help='Signing Key')
    parser_witnesscreate.add_argument(
        '--maximum_block_size',
        type=float,
        default="65536",
        help='Max block size')
    parser_witnesscreate.add_argument(
        '--account_creation_fee',
        type=float,
        default=30,
        help='Account creation fee')
    parser_witnesscreate.add_argument(
        '--sbd_interest_rate',
        type=float,
        default=0.0,
        help='SBD interest rate in percent')
    parser_witnesscreate.add_argument(
        '--url', type=str, default="", help='Witness URL')
    """
        Parse Arguments
    """
    args = parser.parse_args()

    # Logging
    log = logging.getLogger(__name__)
    verbosity = ["critical", "error", "warn", "info", "debug"][int(
        min(args.verbose, 4))]
    log.setLevel(getattr(logging, verbosity.upper()))
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, verbosity.upper()))
    ch.setFormatter(formatter)
    log.addHandler(ch)

    # GrapheneAPI logging
    if args.verbose > 4:
        verbosity = ["critical", "error", "warn", "info", "debug"][int(
            min((args.verbose - 4), 4))]
        gphlog = logging.getLogger("graphenebase")
        gphlog.setLevel(getattr(logging, verbosity.upper()))
        gphlog.addHandler(ch)
    if args.verbose > 8:
        verbosity = ["critical", "error", "warn", "info", "debug"][int(
            min((args.verbose - 8), 4))]
        gphlog = logging.getLogger("grapheneapi")
        gphlog.setLevel(getattr(logging, verbosity.upper()))
        gphlog.addHandler(ch)

    if not hasattr(args, "command"):
        parser.print_help()
        sys.exit(2)

    # initialize STEEM instance
    options = {
        "node": args.node,
        "unsigned": args.unsigned,
        "expires": args.expires
    }
    if args.command == "sign":
        options.update({"offline": True})
    if args.no_wallet:
        options.update({"wif": []})

    steem = stm.Steem(no_broadcast=args.no_broadcast, **options)

    if args.command == "set":
        if (args.key in ["default_account"] and args.value[0] == "@"):
            args.value = args.value[1:]
        configStorage[args.key] = args.value

    elif args.command == "config":
        t = PrettyTable(["Key", "Value"])
        t.align = "l"
        for key in configStorage:
            # hide internal config data
            if key in availableConfigurationKeys:
                t.add_row([key, configStorage[key]])
        print(t)

    elif args.command == "info":
        if not args.objects:
            t = PrettyTable(["Key", "Value"])
            t.align = "l"
            blockchain = Blockchain(mode="head")
            info = blockchain.info()
            median_price = steem.get_current_median_history_price()
            steem_per_mvest = (
                Amount(info["total_vesting_fund_steem"]).amount /
                (Amount(info["total_vesting_shares"]).amount / 1e6))
            price = (Amount(median_price["base"]).amount / Amount(
                median_price["quote"]).amount)
            for key in info:
                t.add_row([key, info[key]])
            t.add_row(["steem per mvest", steem_per_mvest])
            t.add_row(["internal price", price])
            print(t.get_string(sortby="Key"))

        for obj in args.objects:
            # Block
            if re.match("^[0-9]*$", obj):
                block = Block(obj)
                if block:
                    t = PrettyTable(["Key", "Value"])
                    t.align = "l"
                    for key in sorted(block):
                        value = block[key]
                        if key == "transactions":
                            value = json.dumps(value, indent=4)
                        t.add_row([key, value])
                    print(t)
                else:
                    print("Block number %s unknown" % obj)
            # Account name
            elif re.match("^[a-zA-Z0-9\-\._]{2,16}$", obj):
                from math import log10
                account = Account(obj)
                t = PrettyTable(["Key", "Value"])
                t.align = "l"
                for key in sorted(account):
                    value = account[key]
                    if key == "json_metadata":
                        value = json.dumps(json.loads(value or "{}"), indent=4)
                    if key in ["posting", "witness_votes", "active", "owner"]:
                        value = json.dumps(value, indent=4)
                    if key == "reputation" and int(value) > 0:
                        value = int(value)
                        rep = (max(log10(value) - 9, 0) * 9 + 25 if value > 0
                               else max(log10(-value) - 9, 0) * -9 + 25)
                        value = "{:.2f} ({:d})".format(rep, value)
                    t.add_row([key, value])
                print(t)

                # witness available?
                try:
                    witness = Witness(obj)
                    t = PrettyTable(["Key", "Value"])
                    t.align = "l"
                    for key in sorted(witness):
                        value = witness[key]
                        if key in ["props", "sbd_exchange_rate"]:
                            value = json.dumps(value, indent=4)
                        t.add_row([key, value])
                    print(t)
                except:  # noqa FIXME(sneak)
                    pass
            # Public Key
            elif re.match("^STM.{48,55}$", obj):
                account = steem.commit.wallet.getAccountFromPublicKey(obj)
                if account:
                    t = PrettyTable(["Account"])
                    t.align = "l"
                    t.add_row([account])
                    print(t)
                else:
                    print("Public Key not known" % obj)
            # Post identifier
            elif re.match(".*@.{3,16}/.*$", obj):
                post = Post(obj)
                if post:
                    t = PrettyTable(["Key", "Value"])
                    t.align = "l"
                    for key in sorted(post):
                        value = post[key]
                        if (key in ["tags", "json_metadata", "active_votes"]):
                            value = json.dumps(value, indent=4)
                        t.add_row([key, value])
                    print(t)
                else:
                    print("Post now known" % obj)
            else:
                print("Couldn't identify object to read")

    elif args.command == "changewalletpassphrase":
        steem.commit.wallet.changePassphrase()

    elif args.command == "addkey":
        if args.unsafe_import_key:
            for key in args.unsafe_import_key:
                try:
                    steem.commit.wallet.addPrivateKey(key)
                except Exception as e:
                    print(str(e))
        else:
            import getpass
            while True:
                wifkey = getpass.getpass('Private Key (wif) [Enter to quit]:')
                if not wifkey:
                    break
                try:
                    steem.commit.wallet.addPrivateKey(wifkey)
                except Exception as e:
                    print(str(e))
                    continue

                installed_keys = steem.commit.wallet.getPublicKeys()
                if len(installed_keys) == 1:
                    name = steem.commit.wallet.getAccountFromPublicKey(
                        installed_keys[0])
                    print("=" * 30)
                    print("Would you like to make %s a default user?" % name)
                    print()
                    print("You can set it with with:")
                    print("    steempy set default_account <account>")
                    print("=" * 30)

    elif args.command == "delkey":
        if confirm("Are you sure you want to delete keys from your wallet?\n"
                   "This step is IRREVERSIBLE! If you don't have a backup, "
                   "You may lose access to your account!"):
            for pub in args.pub:
                steem.commit.wallet.removePrivateKeyFromPublicKey(pub)

    elif args.command == "parsewif":
        if args.unsafe_import_key:
            for key in args.unsafe_import_key:
                try:
                    print(PrivateKey(key).pubkey)
                except Exception as e:
                    print(str(e))
        else:
            import getpass
            while True:
                wifkey = getpass.getpass('Private Key (wif) [Enter to quit:')
                if not wifkey:
                    break
                try:
                    print(PrivateKey(wifkey).pubkey)
                except Exception as e:
                    print(str(e))
                    continue
    elif args.command == "getkey":
        print(steem.commit.wallet.getPrivateKeyForPublicKey(args.pub))

    elif args.command == "listkeys":
        t = PrettyTable(["Available Key"])
        t.align = "l"
        for key in steem.commit.wallet.getPublicKeys():
            t.add_row([key])
        print(t)

    elif args.command == "listaccounts":
        t = PrettyTable(["Name", "Type", "Available Key"])
        t.align = "l"
        for account in steem.commit.wallet.getAccounts():
            t.add_row([
                account["name"] or "n/a", account["type"] or "n/a",
                account["pubkey"]
            ])
        print(t)

    elif args.command == "upvote" or args.command == "downvote":
        post = Post(args.post)
        if args.command == "downvote":
            weight = -float(args.weight)
        else:
            weight = +float(args.weight)
        if not args.account:
            print("Not voter provided!")
            return
        print_json(post.vote(weight, voter=args.account))

    elif args.command == "transfer":
        print_json(
            steem.commit.transfer(
                args.to,
                args.amount,
                args.asset,
                memo=args.memo,
                account=args.account))

    elif args.command == "powerup":
        print_json(
            steem.commit.transfer_to_vesting(
                args.amount, account=args.account, to=args.to))

    elif args.command == "powerdown":
        print_json(
            steem.commit.withdraw_vesting(
                args.amount,
                account=args.account,
            ))

    elif args.command == "convert":
        print_json(steem.commit.convert(
            args.amount,
            account=args.account,
        ))

    elif args.command == "powerdownroute":
        print_json(
            steem.commit.set_withdraw_vesting_route(
                args.to,
                percentage=args.percentage,
                account=args.account,
                auto_vest=args.auto_vest))

    elif args.command == "balance":
        if args.account and isinstance(args.account, list):
            for account in args.account:
                a = Account(account)

                print("\n@%s" % a.name)
                t = PrettyTable(["Account", "STEEM", "SBD", "VESTS"])
                t.align = "r"
                t.add_row([
                    'Available',
                    a.balances['available']['STEEM'],
                    a.balances['available']['SBD'],
                    a.balances['available']['VESTS'],
                ])
                t.add_row([
                    'Rewards',
                    a.balances['rewards']['STEEM'],
                    a.balances['rewards']['SBD'],
                    a.balances['rewards']['VESTS'],
                ])
                t.add_row([
                    'Savings',
                    a.balances['savings']['STEEM'],
                    a.balances['savings']['SBD'],
                    'N/A',
                ])
                t.add_row([
                    'TOTAL',
                    a.balances['total']['STEEM'],
                    a.balances['total']['SBD'],
                    a.balances['total']['VESTS'],
                ])
                print(t)
        else:
            print("Please specify an account: steempy balance <account>")

    elif args.command == "interest":
        t = PrettyTable([
            "Account", "Last Interest Payment", "Next Payment",
            "Interest rate", "Interest"
        ])
        t.align = "r"
        if isinstance(args.account, str):
            args.account = [args.account]
        for a in args.account:
            i = steem.commit.interest(a)

            t.add_row([
                a,
                i["last_payment"],
                "in %s" % strfage(i["next_payment_duration"]),
                "%.1f%%" % i["interest_rate"],
                "%.3f %s" % (i["interest"], "SBD"),
            ])
        print(t)

    elif args.command == "permissions":
        account = Account(args.account)
        print_permissions(account)

    elif args.command == "allow":
        if not args.foreign_account:
            from steembase.account import PasswordKey
            pwd = get_terminal(
                text="Password for Key Derivation: ", confirm=True)
            args.foreign_account = format(
                PasswordKey(args.account, pwd, args.permission).get_public(),
                "STM")
        print_json(
            steem.commit.allow(
                args.foreign_account,
                weight=args.weight,
                account=args.account,
                permission=args.permission,
                threshold=args.threshold))

    elif args.command == "disallow":
        print_json(
            steem.commit.disallow(
                args.foreign_account,
                account=args.account,
                permission=args.permission,
                threshold=args.threshold))

    elif args.command == "updatememokey":
        if not args.key:
            # Loop until both match
            from steembase.account import PasswordKey
            pw = get_terminal(
                text="Password for Memo Key: ",
                confirm=True,
                allowedempty=False)
            memo_key = PasswordKey(args.account, pw, "memo")
            args.key = format(memo_key.get_public_key(), "STM")
            memo_privkey = memo_key.get_private_key()
            # Add the key to the wallet
            if not args.no_broadcast:
                steem.commit.wallet.addPrivateKey(memo_privkey)
        print_json(
            steem.commit.update_memo_key(args.key, account=args.account))

    elif args.command == "newaccount":
        import getpass
        while True:
            pw = getpass.getpass("New Account Passphrase: ")
            if not pw:
                print("You cannot chosen an empty password!")
                continue
            else:
                pwck = getpass.getpass("Confirm New Account Passphrase: ")
                if pw == pwck:
                    break
                else:
                    print("Given Passphrases do not match!")
        print_json(
            steem.commit.create_account(
                args.accountname,
                creator=args.account,
                password=pw,
                delegation_fee_steem=args.fee,
            ))

    elif args.command == "importaccount":
        from steembase.account import PasswordKey
        import getpass
        password = getpass.getpass("Account Passphrase: ")
        account = Account(args.account)
        imported = False

        if "owner" in args.roles:
            owner_key = PasswordKey(args.account, password, role="owner")
            owner_pubkey = format(owner_key.get_public_key(), "STM")
            if owner_pubkey in [x[0] for x in account["owner"]["key_auths"]]:
                print("Importing owner key!")
                owner_privkey = owner_key.get_private_key()
                steem.commit.wallet.addPrivateKey(owner_privkey)
                imported = True

        if "active" in args.roles:
            active_key = PasswordKey(args.account, password, role="active")
            active_pubkey = format(active_key.get_public_key(), "STM")
            if active_pubkey in [x[0] for x in account["active"]["key_auths"]]:
                print("Importing active key!")
                active_privkey = active_key.get_private_key()
                steem.commit.wallet.addPrivateKey(active_privkey)
                imported = True

        if "posting" in args.roles:
            posting_key = PasswordKey(args.account, password, role="posting")
            posting_pubkey = format(posting_key.get_public_key(), "STM")
            if posting_pubkey in [
                    x[0] for x in account["posting"]["key_auths"]
            ]:
                print("Importing posting key!")
                posting_privkey = posting_key.get_private_key()
                steem.commit.wallet.addPrivateKey(posting_privkey)
                imported = True

        if "memo" in args.roles:
            memo_key = PasswordKey(args.account, password, role="memo")
            memo_pubkey = format(memo_key.get_public_key(), "STM")
            if memo_pubkey == account["memo_key"]:
                print("Importing memo key!")
                memo_privkey = memo_key.get_private_key()
                steem.commit.wallet.addPrivateKey(memo_privkey)
                imported = True

        if not imported:
            print("No matching key(s) found. Password correct?")

    elif args.command == "sign":
        if args.file and args.file != "-":
            if not os.path.isfile(args.file):
                raise Exception("File %s does not exist!" % args.file)
            with open(args.file) as fp:
                tx = fp.read()
        else:
            tx = sys.stdin.read()
        tx = eval(tx)
        print_json(steem.commit.sign(tx))

    elif args.command == "broadcast":
        if args.file and args.file != "-":
            if not os.path.isfile(args.file):
                raise Exception("File %s does not exist!" % args.file)
            with open(args.file) as fp:
                tx = fp.read()
        else:
            tx = sys.stdin.read()
        tx = eval(tx)
        steem.commit.broadcast(tx)

    elif args.command == "buy":
        if args.asset == "SBD":
            price = 1.0 / args.price
        else:
            price = args.price
        dex = Dex(steem)
        print_json(
            dex.buy(args.amount, args.asset, price, account=args.account))

    elif args.command == "sell":
        if args.asset == "SBD":
            price = 1.0 / args.price
        else:
            price = args.price
        dex = Dex(steem)
        print_json(
            dex.sell(args.amount, args.asset, price, account=args.account))

    elif args.command == "cancel":
        dex = Dex(steem)
        print_json(dex.cancel(args.orderid))

    elif args.command == "approvewitness":
        print_json(
            steem.commit.approve_witness(args.witness, account=args.account))

    elif args.command == "disapprovewitness":
        print_json(
            steem.commit.disapprove_witness(
                args.witness, account=args.account))

    elif args.command == "resteem":
        print_json(steem.commit.resteem(args.identifier, account=args.account))

    elif args.command == "follow":
        print_json(
            steem.commit.follow(
                args.follow, what=args.what, account=args.account))

    elif args.command == "unfollow":
        print_json(
            steem.commit.unfollow(
                args.unfollow, what=args.what, account=args.account))

    elif args.command == "setprofile":
        from .profile import Profile
        keys = []
        values = []
        if args.pair:
            for pair in args.pair:
                key, value = pair.split("=")
                keys.append(key)
                values.append(value)
        if args.variable and args.value:
            keys.append(args.variable)
            values.append(args.value)

        profile = Profile(keys, values)

        account = Account(args.account)
        account["json_metadata"] = Profile(account["json_metadata"]
                                           if account["json_metadata"] else {})
        account["json_metadata"].update(profile)

        print_json(
            steem.commit.update_account_profile(
                account["json_metadata"], account=args.account))

    elif args.command == "delprofile":
        from .profile import Profile
        account = Account(args.account)
        account["json_metadata"] = Profile(account["json_metadata"])

        for var in args.variable:
            account["json_metadata"].remove(var)

        print_json(
            steem.commit.update_account_profile(
                account["json_metadata"], account=args.account))

    elif args.command == "witnessupdate":

        witness = Witness(args.witness)
        props = witness["props"]
        if args.account_creation_fee:
            props["account_creation_fee"] = str(
                Amount("%f STEEM" % args.account_creation_fee))
        if args.maximum_block_size:
            props["maximum_block_size"] = args.maximum_block_size
        if args.sbd_interest_rate:
            props["sbd_interest_rate"] = int(args.sbd_interest_rate * 100)

        print_json(
            steem.commit.witness_update(
                args.signing_key or witness["signing_key"],
                args.url or witness["url"],
                props,
                account=args.witness))

    elif args.command == "witnesscreate":
        props = {
            "account_creation_fee":
            str(Amount("%f STEEM" % args.account_creation_fee)),
            "maximum_block_size":
            args.maximum_block_size,
            "sbd_interest_rate":
            int(args.sbd_interest_rate * 100)
        }
        print_json(
            steem.commit.witness_update(
                args.signing_key, args.url, props, account=args.witness))

    else:
        print("No valid command given")


def confirm(question, default="yes"):
    """ Confirmation dialog that requires *manual* input.

        :param str question: Question to ask the user
        :param str default: default answer
        :return: Choice of the user
        :rtype: bool

    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)
    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def get_terminal(text="Password", confirm=False, allowedempty=False):
    import getpass
    while True:
        pw = getpass.getpass(text)
        if not pw and not allowedempty:
            print("Cannot be empty!")
            continue
        else:
            if not confirm:
                break
            pwck = getpass.getpass("Confirm " + text)
            if pw == pwck:
                break
            else:
                print("Not matching!")
    return pw


def format_operation_details(op, memos=False):
    if op[0] == "vote":
        return "%s: %s" % (
            op[1]["voter"],
            construct_identifier(op[1]["author"], op[1]["permlink"]))
    elif op[0] == "comment":
        return "%s: %s" % (
            op[1]["author"],
            construct_identifier(op[1]["author"], op[1]["permlink"]))
    elif op[0] == "transfer":
        str_ = "%s -> %s %s" % (
            op[1]["from"],
            op[1]["to"],
            op[1]["amount"],
        )

        if memos:
            memo = op[1]["memo"]
            if len(memo) > 0 and memo[0] == "#":
                steem = shared_steemd_instance()
                # memo = steem.decode_memo(memo, op[1]["from"])
                memo = steem.decode_memo(memo, op)
            str_ += " (%s)" % memo
        return str_
    elif op[0] == "interest":
        return "%s" % (op[1]["interest"])
    else:
        return json.dumps(op[1], indent=4)


def print_permissions(account):
    t = PrettyTable(["Permission", "Threshold", "Key/Account"], hrules=0)
    t.align = "r"
    for permission in ["owner", "active", "posting"]:
        auths = []
        for type_ in ["account_auths", "key_auths"]:
            for authority in account[permission][type_]:
                auths.append("%s (%d)" % (authority[0], authority[1]))
        t.add_row([
            permission,
            account[permission]["weight_threshold"],
            "\n".join(auths),
        ])
    print(t)


def print_json(tx):
    if sys.stdout.isatty():
        print(json.dumps(tx, indent=4))
    else:
        # You're being piped or redirected
        print(tx)


# this is another console script entrypoint
# also this function sucks and should be taken out back and shot
def steemtailentry():
    parser = argparse.ArgumentParser(
        description="UNIX tail(1)-like tool for the steem blockchain")
    parser.add_argument(
        '-f',
        '--follow',
        help='Constantly stream output to stdout',
        action='store_true')
    parser.add_argument(
        '-n', '--lines', type=int, default=10, help='How many ops to show')
    parser.add_argument(
        '-j',
        '--json',
        help='Output as JSON instead of human-readable pretty-printed format',
        action='store_true')
    args = parser.parse_args(sys.argv[1:])

    b = Blockchain()
    stream = b.reliable_stream()

    op_count = 0
    if args.json:
        if not args.follow:
            sys.stdout.write('[')
    for op in stream:
        if args.json:
            sys.stdout.write('%s' % json.dumps(op))
        else:
            pprint.pprint(op)
        op_count += 1
        if not args.follow:
            if op_count > args.lines:
                if args.json:
                    sys.stdout.write(']')
                return
            else:
                if args.json:
                    sys.stdout.write(',')
