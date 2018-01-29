import json
import logging
import random
import re
import voluptuous as vo
from datetime import datetime, timedelta
from funcy.colls import none
from funcy.flow import silent
from funcy.seqs import first
from steembase import memo
from steembase import operations
from steembase.account import PrivateKey, PublicKey
from steembase.exceptions import AccountExistsException, MissingKeyError
from steembase.storage import configStorage
from .account import Account
from .amount import Amount
from .converter import Converter
from .instance import shared_steemd_instance
from .transactionbuilder import TransactionBuilder
from .utils import (
    derive_permlink,
    fmt_time_string,
    keep_in_dict,
    resolve_identifier,
)
from .wallet import Wallet

log = logging.getLogger(__name__)

STEEMIT_100_PERCENT = 10000
STEEMIT_1_PERCENT = (STEEMIT_100_PERCENT / 100)

# TODO
# account_witness_proxy [active]
# account_update [owner, active]
# decline_voting_rights [owner]

# challenge_authority [posting]
# prove_authority [active, owner]
# request_account_recovery [active]
# change_recovery_account [owner]
# reset_account [active]
# set_reset_account [active, owner]

# escrow_transfer [active]
# escrow_dispute [active]
# escrow_release [active]
# escrow_approve [active]
# custom_binary [any]

# custom [active]
# delete_comment [posting]

# enable_content_editing_operation [active]


class Commit(object):
    """ Commit things to the Steem network.

        This class contains helper methods to construct, sign and broadcast
        common transactions, such as posting, voting, sending funds, etc.

        :param Steemd steemd: Steemd node to connect to*
        :param bool offline: Do **not** broadcast transactions! *(optional)*
        :param bool debug: Enable Debugging *(optional)*

        :param list,dict,string keys: Predefine the wif keys to shortcut the
        wallet database

        Three wallet operation modes are possible:

        * **Wallet Database**: Here, the steemlibs load the keys from the
          locally stored wallet SQLite database (see ``storage.py``).
          To use this mode, simply call ``Steem()`` without the
          ``keys`` parameter
        * **Providing Keys**: Here, you can provide the keys for
          your accounts manually. All you need to do is add the wif
          keys for the accounts you want to use as a simple array
          using the ``keys`` parameter to ``Steem()``.
        * **Force keys**: This more is for advanced users and
          requires that you know what you are doing. Here, the
          ``keys`` parameter is a dictionary that overwrite the
          ``active``, ``owner``, ``posting`` or ``memo`` keys for
          any account. This mode is only used for *foreign*
          signatures!

    """

    def __init__(self, steemd_instance=None, no_broadcast=False, **kwargs):
        self.steemd = steemd_instance or shared_steemd_instance()
        self.no_broadcast = no_broadcast
        self.unsigned = kwargs.get("unsigned", False)
        self.expiration = int(kwargs.get("expiration", 60))

        self.wallet = Wallet(self.steemd, **kwargs)

    def finalizeOp(self, ops, account, permission):
        """ This method obtains the required private keys if present in
            the wallet, finalizes the transaction, signs it and
            broadacasts it

            :param operation ops: The operation (or list of operaions) to
                broadcast

            :param operation account: The account that authorizes the
                operation
            :param string permission: The required permission for
                signing (active, owner, posting)

            ... note::

                If ``ops`` is a list of operation, they all need to be
                signable by the same key! Thus, you cannot combine ops
                that require active permission with ops that require
                posting permission. Neither can you use different
                accounts for different operations!
        """
        tx = TransactionBuilder(
            None,
            steemd_instance=self.steemd,
            wallet_instance=self.wallet,
            no_broadcast=self.no_broadcast,
            expiration=self.expiration)
        tx.appendOps(ops)

        if self.unsigned:
            tx.addSigningInformation(account, permission)
            return tx
        else:
            tx.appendSigner(account, permission)
            tx.sign()

        return tx.broadcast()

    def sign(self, unsigned_trx, wifs=[]):
        """ Sign a provided transaction witht he provided key(s)

            :param dict unsigned_trx: The transaction to be signed and returned
            :param string wifs: One or many wif keys to use for signing
                a transaction. If not present, the keys will be loaded
                from the wallet as defined in "missing_signatures" key
                of the transactizions.
        """
        tx = TransactionBuilder(
            unsigned_trx,
            steemd_instance=self.steemd,
            wallet_instance=self.wallet,
            no_broadcast=self.no_broadcast,
            expiration=self.expiration)
        tx.appendMissingSignatures(wifs)
        tx.sign()
        return tx.json()

    def broadcast(self, signed_trx):
        """ Broadcast a transaction to the Steem network

            :param tx signed_trx: Signed transaction to broadcast
        """
        tx = TransactionBuilder(
            signed_trx,
            steemd_instance=self.steemd,
            wallet_instance=self.wallet,
            no_broadcast=self.no_broadcast,
            expiration=self.expiration)
        return tx.broadcast()

    def post(self,
             title,
             body,
             author,
             permlink=None,
             reply_identifier=None,
             json_metadata=None,
             comment_options=None,
             community=None,
             tags=None,
             beneficiaries=None,
             self_vote=False):
        """ Create a new post.

        If this post is intended as a reply/comment, `reply_identifier` needs
        to be set with the identifier of the parent post/comment (eg.
        `@author/permlink`).

        Optionally you can also set json_metadata, comment_options and upvote
        the newly created post as an author.

        Setting category, tags or community will override the values provided
        in json_metadata and/or comment_options where appropriate.

        Args:

        title (str): Title of the post
        body (str): Body of the post/comment
        author (str): Account are you posting from
        permlink (str): Manually set the permlink (defaults to None).
            If left empty, it will be derived from title automatically.
        reply_identifier (str): Identifier of the parent post/comment (only
            if this post is a reply/comment).
        json_metadata (str, dict): JSON meta object that can be attached to
            the post.
        comment_options (str, dict): JSON options object that can be
            attached to the post.

        Example::
            comment_options = {
                'max_accepted_payout': '1000000.000 SBD',
                'percent_steem_dollars': 10000,
                'allow_votes': True,
                'allow_curation_rewards': True,
                'extensions': [[0, {
                    'beneficiaries': [
                        {'account': 'account1', 'weight': 5000},
                        {'account': 'account2', 'weight': 5000},
                    ]}
                ]]
            }

        community (str): (Optional) Name of the community we are posting
            into. This will also override the community specified in
            `json_metadata`.

        tags (str, list): (Optional) A list of tags (5 max) to go with the
            post. This will also override the tags specified in
            `json_metadata`. The first tag will be used as a 'category'. If
            provided as a string, it should be space separated.

        beneficiaries (list of dicts): (Optional) A list of beneficiaries
            for posting reward distribution. This argument overrides
            beneficiaries as specified in `comment_options`.

        For example, if we would like to split rewards between account1 and
        account2::

            beneficiaries = [
                {'account': 'account1', 'weight': 5000},
                {'account': 'account2', 'weight': 5000}
            ]

        self_vote (bool): (Optional) Upvote the post as author, right after
            posting.

        """

        # prepare json_metadata
        json_metadata = json_metadata or {}
        if isinstance(json_metadata, str):
            json_metadata = silent(json.loads)(json_metadata) or {}

        # override the community
        if community:
            json_metadata.update({'community': community})

        # deal with the category and tags
        if isinstance(tags, str):
            tags = list(set(filter(None, (re.split("[\W_]", tags)))))

        category = None
        tags = tags or json_metadata.get('tags', [])
        if tags:
            if len(tags) > 5:
                raise ValueError('Can only specify up to 5 tags per post.')

            # first tag should be a category
            category = tags[0]
            json_metadata.update({"tags": tags})

        # can't provide a category while replying to a post
        if reply_identifier and category:
            category = None

        # deal with replies/categories
        if reply_identifier:
            parent_author, parent_permlink = resolve_identifier(
                reply_identifier)
            if not permlink:
                permlink = derive_permlink(title, parent_permlink)
        elif category:
            parent_permlink = derive_permlink(category)
            parent_author = ""
            if not permlink:
                permlink = derive_permlink(title)
        else:
            parent_author = ""
            parent_permlink = ""
            if not permlink:
                permlink = derive_permlink(title)

        post_op = operations.Comment(
            **{
                "parent_author": parent_author,
                "parent_permlink": parent_permlink,
                "author": author,
                "permlink": permlink,
                "title": title,
                "body": body,
                "json_metadata": json_metadata
            })
        ops = [post_op]

        # if comment_options are used, add a new op to the transaction
        if comment_options or beneficiaries:
            options = keep_in_dict(comment_options or {}, [
                'max_accepted_payout', 'percent_steem_dollars', 'allow_votes',
                'allow_curation_rewards', 'extensions'
            ])
            # override beneficiaries extension
            if beneficiaries:
                # validate schema
                # or just simply vo.Schema([{'account': str, 'weight': int}])
                schema = vo.Schema([{
                    vo.Required('account'):
                    vo.All(str, vo.Length(max=16)),
                    vo.Required('weight', default=10000):
                    vo.All(int, vo.Range(min=1, max=10000))
                }])
                schema(beneficiaries)
                options['beneficiaries'] = beneficiaries

            default_max_payout = "1000000.000 SBD"
            comment_op = operations.CommentOptions(
                **{
                    "author":
                    author,
                    "permlink":
                    permlink,
                    "max_accepted_payout":
                    options.get("max_accepted_payout", default_max_payout),
                    "percent_steem_dollars":
                    int(options.get("percent_steem_dollars", 10000)),
                    "allow_votes":
                    options.get("allow_votes", True),
                    "allow_curation_rewards":
                    options.get("allow_curation_rewards", True),
                    "extensions":
                    options.get("extensions", []),
                    "beneficiaries":
                    options.get("beneficiaries"),
                })
            ops.append(comment_op)

        if self_vote:
            vote_op = operations.Vote(
                **{
                    'voter': author,
                    'author': author,
                    'permlink': permlink,
                    'weight': 10000,
                })
            ops.append(vote_op)

        return self.finalizeOp(ops, author, "posting")

    def vote(self, identifier, weight, account=None):
        """ Vote for a post

            :param str identifier: Identifier for the post to upvote Takes
                                   the form ``@author/permlink``
            :param float weight: Voting weight. Range: -100.0 - +100.0. May
                                 not be 0.0
            :param str account: Voter to use for voting. (Optional)

            If ``voter`` is not defines, the ``default_account`` will be taken
            or a ValueError will be raised

            .. code-block:: python

                steempy set default_account <account>
        """
        if not account:
            account = configStorage.get("default_account")
        if not account:
            raise ValueError("You need to provide a voter account")

        post_author, post_permlink = resolve_identifier(identifier)

        op = operations.Vote(
            **{
                "voter": account,
                "author": post_author,
                "permlink": post_permlink,
                "weight": int(weight * STEEMIT_1_PERCENT)
            })

        return self.finalizeOp(op, account, "posting")

    def create_account(
            self,
            account_name,
            json_meta=None,
            password=None,
            owner_key=None,
            active_key=None,
            posting_key=None,
            memo_key=None,
            additional_owner_keys=[],
            additional_active_keys=[],
            additional_posting_keys=[],
            additional_owner_accounts=[],
            additional_active_accounts=[],
            additional_posting_accounts=[],
            store_keys=True,
            store_owner_key=False,
            delegation_fee_steem='0 STEEM',
            creator=None,
    ):
        """ Create new account in Steem

            The brainkey/password can be used to recover all generated keys
            (see `steembase.account` for more details.

            By default, this call will use ``default_account`` to
            register a new name ``account_name`` with all keys being
            derived from a new brain key that will be returned. The
            corresponding keys will automatically be installed in the
            wallet.

            .. note:: Account creations cost a fee that is defined by
               the network. If you create an account, you will
               need to pay for that fee!

               **You can partially pay that fee by delegating VESTS.**

               To pay the fee in full in STEEM, leave
               ``delegation_fee_steem`` set to ``0 STEEM`` (Default).

               To pay the fee partially in STEEM, partially with delegated
               VESTS, set ``delegation_fee_steem`` to a value greater than ``1
               STEEM``. `Required VESTS will be calculated automatically.`

               To pay the fee with maximum amount of delegation, set
               ``delegation_fee_steem`` to ``1 STEEM``. `Required VESTS will be
               calculated automatically.`

            .. warning:: Don't call this method unless you know what
                          you are doing! Be sure to understand what this
                          method does and where to find the private keys
                          for your account.

        .. note:: Please note that this imports private keys (if password is
        present) into the wallet by default. However, it **does not import
        the owner key** unless `store_owner_key` is set to True (default
        False). Do NOT expect to be able to recover it from the wallet if
        you lose your password!

            :param str account_name: (**required**) new account name
            :param str json_meta: Optional meta data for the account
            :param str owner_key: Main owner key
            :param str active_key: Main active key
            :param str posting_key: Main posting key
            :param str memo_key: Main memo_key
            :param str password: Alternatively to providing keys, one
                                 can provide a password from which the
                                 keys will be derived
            :param list additional_owner_keys:  Additional owner public keys

            :param list additional_active_keys: Additional active public keys

            :param list additional_posting_keys: Additional posting public keys

            :param list additional_owner_accounts: Additional owner account
            names

            :param list additional_active_accounts: Additional active account
            names

            :param list additional_posting_accounts: Additional posting account
            names

            :param bool store_keys: Store new keys in the wallet (default:
            ``True``)

            :param bool store_owner_key: Store owner key in the wallet
            (default: ``False``)

            :param str delegation_fee_steem: (Optional) If set, `creator` pay a
            fee of this amount, and delegate the rest with VESTS (calculated
            automatically). Minimum: 1 STEEM. If left to 0 (Default), full fee
            is paid without VESTS delegation.

            :param str creator: which account should pay the registration fee
                                (defaults to ``default_account``)

        :raises AccountExistsException: if the account already exists on the
        blockchain

        """
        assert len(
            account_name) <= 16, "Account name must be at most 16 chars long"

        if not creator:
            creator = configStorage.get("default_account")
        if not creator:
            raise ValueError(
                "Not creator account given. Define it with " +
                "creator=x, or set the default_account using steempy")
        if password and (owner_key or posting_key or active_key or memo_key):
            raise ValueError("You cannot use 'password' AND provide keys!")

        # check if account already exists
        try:
            Account(account_name, steemd_instance=self.steemd)
        except:  # noqa FIXME(sneak)
            pass
        else:
            raise AccountExistsException

        " Generate new keys from password"
        from steembase.account import PasswordKey, PublicKey
        if password:
            posting_key = PasswordKey(account_name, password, role="posting")
            active_key = PasswordKey(account_name, password, role="active")
            owner_key = PasswordKey(account_name, password, role="owner")
            memo_key = PasswordKey(account_name, password, role="memo")
            posting_pubkey = posting_key.get_public_key()
            active_pubkey = active_key.get_public_key()
            owner_pubkey = owner_key.get_public_key()
            memo_pubkey = memo_key.get_public_key()
            posting_privkey = posting_key.get_private_key()
            active_privkey = active_key.get_private_key()
            owner_privkey = owner_key.get_private_key()
            memo_privkey = memo_key.get_private_key()
            # store private keys
            if store_keys:
                if store_owner_key:
                    self.wallet.addPrivateKey(owner_privkey)
                self.wallet.addPrivateKey(active_privkey)
                self.wallet.addPrivateKey(posting_privkey)
                self.wallet.addPrivateKey(memo_privkey)
        elif owner_key and posting_key and active_key and memo_key:
            posting_pubkey = PublicKey(
                posting_key, prefix=self.steemd.chain_params["prefix"])
            active_pubkey = PublicKey(
                active_key, prefix=self.steemd.chain_params["prefix"])
            owner_pubkey = PublicKey(
                owner_key, prefix=self.steemd.chain_params["prefix"])
            memo_pubkey = PublicKey(
                memo_key, prefix=self.steemd.chain_params["prefix"])
        else:
            raise ValueError(
                "Call incomplete! Provide either a password or public keys!")

        owner = format(owner_pubkey, self.steemd.chain_params["prefix"])
        active = format(active_pubkey, self.steemd.chain_params["prefix"])
        posting = format(posting_pubkey, self.steemd.chain_params["prefix"])
        memo = format(memo_pubkey, self.steemd.chain_params["prefix"])

        owner_key_authority = [[owner, 1]]
        active_key_authority = [[active, 1]]
        posting_key_authority = [[posting, 1]]
        owner_accounts_authority = []
        active_accounts_authority = []
        posting_accounts_authority = []

        # additional authorities
        for k in additional_owner_keys:
            owner_key_authority.append([k, 1])
        for k in additional_active_keys:
            active_key_authority.append([k, 1])
        for k in additional_posting_keys:
            posting_key_authority.append([k, 1])

        for k in additional_owner_accounts:
            owner_accounts_authority.append([k, 1])
        for k in additional_active_accounts:
            active_accounts_authority.append([k, 1])
        for k in additional_posting_accounts:
            posting_accounts_authority.append([k, 1])

        props = self.steemd.get_chain_properties()
        required_fee_steem = Amount(props["account_creation_fee"]).amount * 30

        required_fee_vests = 0
        delegation_fee_steem = Amount(delegation_fee_steem).amount
        if delegation_fee_steem:
            # creating accounts without delegation requires 30x
            # account_creation_fee creating account with delegation allows one
            # to use VESTS to pay the fee where the ratio must satisfy 1 STEEM
            # in fee == 5 STEEM in delegated VESTS

            delegated_sp_fee_mult = 5

            if delegation_fee_steem < 1:
                raise ValueError(
                    "When creating account with delegation, at least " +
                    "1 STEEM in fee must be paid.")

            # calculate required remaining fee in vests
            remaining_fee = required_fee_steem - delegation_fee_steem
            if remaining_fee > 0:
                required_sp = remaining_fee * delegated_sp_fee_mult
                required_fee_vests = Converter().sp_to_vests(required_sp) + 1

        s = {
            'creator': creator,
            'fee': '%s STEEM' % (delegation_fee_steem or required_fee_steem),
            'delegation': '%s VESTS' % required_fee_vests,
            'json_metadata': json_meta or {},
            'memo_key': memo,
            'new_account_name': account_name,
            'owner': {
                'account_auths': owner_accounts_authority,
                'key_auths': owner_key_authority,
                'weight_threshold': 1
            },
            'active': {
                'account_auths': active_accounts_authority,
                'key_auths': active_key_authority,
                'weight_threshold': 1
            },
            'posting': {
                'account_auths': posting_accounts_authority,
                'key_auths': posting_key_authority,
                'weight_threshold': 1
            },
            'prefix': self.steemd.chain_params["prefix"]
        }

        op = operations.AccountCreateWithDelegation(**s)

        return self.finalizeOp(op, creator, "active")

    def transfer(self, to, amount, asset, memo="", account=None):
        """ Transfer SBD or STEEM to another account.

            :param str to: Recipient

            :param float amount: Amount to transfer

            :param str asset: Asset to transfer (``SBD`` or ``STEEM``)

            :param str memo: (optional) Memo, may begin with `#` for encrypted
            messaging

            :param str account: (optional) the source account for the transfer
            if not ``default_account``

        """
        if not account:
            account = configStorage.get("default_account")
        if not account:
            raise ValueError("You need to provide an account")

        assert asset in ['STEEM', 'SBD']

        if memo and memo[0] == "#":
            from steembase import memo as Memo
            memo_wif = self.wallet.getMemoKeyForAccount(account)
            if not memo_wif:
                raise MissingKeyError("Memo key for %s missing!" % account)
            to_account = Account(to, steemd_instance=self.steemd)
            nonce = random.getrandbits(64)
            memo = Memo.encode_memo(
                PrivateKey(memo_wif),
                PublicKey(
                    to_account["memo_key"],
                    prefix=self.steemd.chain_params["prefix"]),
                nonce,
                memo,
                prefix=self.steemd.chain_params["prefix"])

        op = operations.Transfer(
            **{
                "from":
                account,
                "to":
                to,
                "amount":
                '{:.{prec}f} {asset}'.format(
                    float(amount), prec=3, asset=asset),
                "memo":
                memo
            })
        return self.finalizeOp(op, account, "active")

    def withdraw_vesting(self, amount, account=None):
        """ Withdraw VESTS from the vesting account.

            :param float amount: number of VESTS to withdraw over a period of
            104 weeks

            :param str account: (optional) the source account for the transfer
            if not ``default_account``

    """
        if not account:
            account = configStorage.get("default_account")
        if not account:
            raise ValueError("You need to provide an account")

        op = operations.WithdrawVesting(
            **{
                "account":
                account,
                "vesting_shares":
                '{:.{prec}f} {asset}'.format(
                    float(amount), prec=6, asset="VESTS"),
            })

        return self.finalizeOp(op, account, "active")

    def transfer_to_vesting(self, amount, to=None, account=None):
        """ Vest STEEM

        :param float amount: number of STEEM to vest

        :param str to: (optional) the source account for the transfer if not
        ``default_account``

        :param str account: (optional) the source account for the transfer
        if not ``default_account``

    """
        if not account:
            account = configStorage.get("default_account")
        if not account:
            raise ValueError("You need to provide an account")

        if not to:
            to = account  # powerup on the same account

        op = operations.TransferToVesting(
            **{
                "from":
                account,
                "to":
                to,
                "amount":
                '{:.{prec}f} {asset}'.format(
                    float(amount), prec=3, asset='STEEM')
            })

        return self.finalizeOp(op, account, "active")

    def convert(self, amount, account=None, request_id=None):
        """ Convert SteemDollars to Steem (takes one week to settle)

            :param float amount: number of VESTS to withdraw

            :param str account: (optional) the source account for the transfer
            if not ``default_account``

            :param str request_id: (optional) identifier for tracking the
            conversion`

        """
        if not account:
            account = configStorage.get("default_account")
        if not account:
            raise ValueError("You need to provide an account")

        if request_id:
            request_id = int(request_id)
        else:
            request_id = random.getrandbits(32)
        op = operations.Convert(
            **{
                "owner":
                account,
                "requestid":
                request_id,
                "amount":
                '{:.{prec}f} {asset}'.format(
                    float(amount), prec=3, asset='SBD')
            })

        return self.finalizeOp(op, account, "active")

    def transfer_to_savings(self, amount, asset, memo, to=None, account=None):
        """ Transfer SBD or STEEM into a 'savings' account.

            :param float amount: STEEM or SBD amount
            :param float asset: 'STEEM' or 'SBD'
            :param str memo: (optional) Memo
            :param str to: (optional) the source account for the transfer if
            not ``default_account``
            :param str account: (optional) the source account for the transfer
            if not ``default_account``
        """
        assert asset in ['STEEM', 'SBD']

        if not account:
            account = configStorage.get("default_account")
        if not account:
            raise ValueError("You need to provide an account")

        if not to:
            to = account  # move to savings on same account

        op = operations.TransferToSavings(
            **{
                "from":
                account,
                "to":
                to,
                "amount":
                '{:.{prec}f} {asset}'.format(
                    float(amount), prec=3, asset=asset),
                "memo":
                memo,
            })
        return self.finalizeOp(op, account, "active")

    def transfer_from_savings(self,
                              amount,
                              asset,
                              memo,
                              request_id=None,
                              to=None,
                              account=None):
        """ Withdraw SBD or STEEM from 'savings' account.

            :param float amount: STEEM or SBD amount
            :param float asset: 'STEEM' or 'SBD'
            :param str memo: (optional) Memo
            :param str request_id: (optional) identifier for tracking or
            cancelling the withdrawal
            :param str to: (optional) the source account for the transfer if
            not ``default_account``
            :param str account: (optional) the source account for the transfer
            if not ``default_account``
        """
        assert asset in ['STEEM', 'SBD']

        if not account:
            account = configStorage.get("default_account")
        if not account:
            raise ValueError("You need to provide an account")

        if not to:
            to = account  # move to savings on same account

        if request_id:
            request_id = int(request_id)
        else:
            request_id = random.getrandbits(32)

        op = operations.TransferFromSavings(
            **{
                "from":
                account,
                "request_id":
                request_id,
                "to":
                to,
                "amount":
                '{:.{prec}f} {asset}'.format(
                    float(amount), prec=3, asset=asset),
                "memo":
                memo,
            })
        return self.finalizeOp(op, account, "active")

    def transfer_from_savings_cancel(self, request_id, account=None):
        """ Cancel a withdrawal from 'savings' account.

            :param str request_id: Identifier for tracking or cancelling
            the withdrawal
            :param str account: (optional) the source account for the transfer
            if not ``default_account``
        """
        if not account:
            account = configStorage.get("default_account")
        if not account:
            raise ValueError("You need to provide an account")

        op = operations.CancelTransferFromSavings(**{
            "from": account,
            "request_id": request_id,
        })
        return self.finalizeOp(op, account, "active")

    def claim_reward_balance(self,
                             reward_steem='0 STEEM',
                             reward_sbd='0 SBD',
                             reward_vests='0 VESTS',
                             account=None):
        """ Claim reward balances.

        By default, this will claim ``all`` outstanding balances. To bypass
        this behaviour, set desired claim amount by setting any of
        `reward_steem`, `reward_sbd` or `reward_vests`.

        Args:
            reward_steem (string): Amount of STEEM you would like to claim.
            reward_sbd (string): Amount of SBD you would like to claim.
            reward_vests (string): Amount of VESTS you would like to claim.
            account (string): The source account for the claim if not
            ``default_account`` is used.
        """
        if not account:
            account = configStorage.get("default_account")
        if not account:
            raise ValueError("You need to provide an account")

        # if no values were set by user, claim all outstanding balances on
        # account
        if none(
                int(first(x.split(' ')))
                for x in [reward_sbd, reward_steem, reward_vests]):
            a = Account(account)
            reward_steem = a['reward_steem_balance']
            reward_sbd = a['reward_sbd_balance']
            reward_vests = a['reward_vesting_balance']

        op = operations.ClaimRewardBalance(
            **{
                "account": account,
                "reward_steem": reward_steem,
                "reward_sbd": reward_sbd,
                "reward_vests": reward_vests,
            })
        return self.finalizeOp(op, account, "posting")

    def delegate_vesting_shares(self, to_account, vesting_shares,
                                account=None):
        """ Delegate SP to another account.

        Args:
            to_account (string): Account we are delegating shares to
            (delegatee).
            vesting_shares (string): Amount of VESTS to delegate eg. `10000
            VESTS`.
            account (string): The source account (delegator). If not specified,
            ``default_account`` is used.
        """
        if not account:
            account = configStorage.get("default_account")
        if not account:
            raise ValueError("You need to provide an account")

        op = operations.DelegateVestingShares(
            **{
                "delegator": account,
                "delegatee": to_account,
                "vesting_shares": str(Amount(vesting_shares)),
            })
        return self.finalizeOp(op, account, "active")

    def witness_feed_publish(self,
                             steem_usd_price,
                             quote="1.000",
                             account=None):
        """ Publish a feed price as a witness.

            :param float steem_usd_price: Price of STEEM in USD (implied price)
            :param float quote: (optional) Quote Price. Should be 1.000, unless
            we are adjusting the feed to support the peg.
            :param str account: (optional) the source account for the transfer
            if not ``default_account``
        """
        if not account:
            account = configStorage.get("default_account")
        if not account:
            raise ValueError("You need to provide an account")

        op = operations.FeedPublish(
            **{
                "publisher": account,
                "exchange_rate": {
                    "base": "%s SBD" % steem_usd_price,
                    "quote": "%s STEEM" % quote,
                }
            })
        return self.finalizeOp(op, account, "active")

    def witness_update(self, signing_key, url, props, account=None):
        """ Update witness

            :param pubkey signing_key: Signing key
            :param str url: URL
            :param dict props: Properties
            :param str account: (optional) witness account name

             Properties:::

                {
                    "account_creation_fee": x,
                    "maximum_block_size": x,
                    "sbd_interest_rate": x,
                }

        """
        if not account:
            account = configStorage.get("default_account")
        if not account:
            raise ValueError("You need to provide an account")

        try:
            PublicKey(signing_key)
        except Exception as e:
            raise e

        op = operations.WitnessUpdate(
            **{
                "owner": account,
                "url": url,
                "block_signing_key": signing_key,
                "props": props,
                "fee": "0.000 STEEM",
                "prefix": self.steemd.chain_params["prefix"]
            })
        return self.finalizeOp(op, account, "active")

    def decode_memo(self, enc_memo):
        """ Try to decode an encrypted memo
        """
        assert enc_memo[
            0] == "#", "decode memo requires memos to start with '#'"
        keys = memo.involved_keys(enc_memo)
        wif = None
        for key in keys:
            wif = self.wallet.getPrivateKeyForPublicKey(str(key))
            if wif:
                break
        if not wif:
            raise MissingKeyError
        return memo.decode_memo(PrivateKey(wif), enc_memo)

    def interest(self, account):
        """ Caluclate interest for an account

            :param str account: Account name to get interest for
        """
        account = Account(account, steemd_instance=self.steemd)
        last_payment = fmt_time_string(account["sbd_last_interest_payment"])
        next_payment = last_payment + timedelta(days=30)
        interest_rate = self.steemd.get_dynamic_global_properties()[
            "sbd_interest_rate"] / 100  # percent
        interest_amount = (interest_rate / 100) * int(
            int(account["sbd_seconds"]) / (60 * 60 * 24 * 356)) * 10**-3

        return {
            "interest": interest_amount,
            "last_payment": last_payment,
            "next_payment": next_payment,
            "next_payment_duration": next_payment - datetime.now(),
            "interest_rate": interest_rate,
        }

    def set_withdraw_vesting_route(self,
                                   to,
                                   percentage=100,
                                   account=None,
                                   auto_vest=False):
        """ Set up a vesting withdraw route. When vesting shares are
            withdrawn, they will be routed to these accounts based on the
            specified weights.

            :param str to: Recipient of the vesting withdrawal
            :param float percentage: The percent of the withdraw to go
                to the 'to' account.
            :param str account: (optional) the vesting account
            :param bool auto_vest: Set to true if the from account
                should receive the VESTS as VESTS, or false if it should
                receive them as STEEM. (defaults to ``False``)
        """
        if not account:
            account = configStorage.get("default_account")
        if not account:
            raise ValueError("You need to provide an account")

        op = operations.SetWithdrawVestingRoute(
            **{
                "from_account": account,
                "to_account": to,
                "percent": int(percentage * STEEMIT_1_PERCENT),
                "auto_vest": auto_vest
            })

        return self.finalizeOp(op, account, "active")

    @staticmethod
    def _test_weights_treshold(authority):
        weights = 0
        for a in authority["account_auths"]:
            weights += a[1]
        for a in authority["key_auths"]:
            weights += a[1]
        if authority["weight_threshold"] > weights:
            raise ValueError("Threshold too restrictive!")

    def allow(self,
              foreign,
              weight=None,
              permission="posting",
              account=None,
              threshold=None):
        """ Give additional access to an account by some other public
            key or account.

            :param str foreign: The foreign account that will obtain access
            :param int weight: (optional) The weight to use. If not
                define, the threshold will be used. If the weight is
                smaller than the threshold, additional signatures will
                be required. (defaults to threshold)
            :param str permission: (optional) The actual permission to
                modify (defaults to ``posting``)
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
            :param int threshold: The threshold that needs to be reached
                by signatures to be able to interact
        """
        if not account:
            account = configStorage.get("default_account")
        if not account:
            raise ValueError("You need to provide an account")

        if permission not in ["owner", "posting", "active"]:
            raise ValueError(
                "Permission needs to be either 'owner', 'posting', or 'active")
        account = Account(account, steemd_instance=self.steemd)
        if not weight:
            weight = account[permission]["weight_threshold"]

        authority = account[permission]
        try:
            pubkey = PublicKey(foreign)
            authority["key_auths"].append([str(pubkey), weight])
        except:  # noqa FIXME(sneak)
            try:
                foreign_account = Account(foreign, steemd_instance=self.steemd)
                authority["account_auths"].append(
                    [foreign_account["name"], weight])
            except:  # noqa FIXME(sneak)
                raise ValueError(
                    "Unknown foreign account or unvalid public key")
        if threshold:
            authority["weight_threshold"] = threshold
            self._test_weights_treshold(authority)

        op = operations.AccountUpdate(
            **{
                "account": account["name"],
                permission: authority,
                "memo_key": account["memo_key"],
                "json_metadata": account["json_metadata"],
                'prefix': self.steemd.chain_params["prefix"]
            })
        if permission == "owner":
            return self.finalizeOp(op, account["name"], "owner")
        else:
            return self.finalizeOp(op, account["name"], "active")

    def disallow(self,
                 foreign,
                 permission="posting",
                 account=None,
                 threshold=None):
        """ Remove additional access to an account by some other public
            key or account.

            :param str foreign: The foreign account that will obtain access
            :param str permission: (optional) The actual permission to
                modify (defaults to ``posting``)
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
            :param int threshold: The threshold that needs to be reached
                by signatures to be able to interact
        """
        if not account:
            account = configStorage.get("default_account")
        if not account:
            raise ValueError("You need to provide an account")

        if permission not in ["owner", "posting", "active"]:
            raise ValueError(
                "Permission needs to be either 'owner', 'posting', or 'active")
        account = Account(account, steemd_instance=self.steemd)
        authority = account[permission]

        try:
            pubkey = PublicKey(
                foreign, prefix=self.steemd.chain_params["prefix"])
            affected_items = list(
                filter(lambda x: x[0] == str(pubkey), authority["key_auths"]))
            authority["key_auths"] = list(
                filter(lambda x: x[0] != str(pubkey), authority["key_auths"]))
        except:  # noqa FIXME(sneak)
            try:
                foreign_account = Account(foreign, steemd_instance=self.steemd)
                affected_items = list(
                    filter(lambda x: x[0] == foreign_account["name"],
                           authority["account_auths"]))
                authority["account_auths"] = list(
                    filter(lambda x: x[0] != foreign_account["name"],
                           authority["account_auths"]))
            except:  # noqa FIXME(sneak)
                raise ValueError(
                    "Unknown foreign account or unvalid public key")

        removed_weight = affected_items[0][1]

        # Define threshold
        if threshold:
            authority["weight_threshold"] = threshold

        # Correct threshold (at most by the amount removed from the
        # authority)
        try:
            self._test_weights_treshold(authority)
        except:  # noqa FIXME(sneak)
            log.critical("The account's threshold will be reduced by %d" %
                         removed_weight)
            authority["weight_threshold"] -= removed_weight
            self._test_weights_treshold(authority)

        op = operations.AccountUpdate(
            **{
                "account": account["name"],
                permission: authority,
                "memo_key": account["memo_key"],
                "json_metadata": account["json_metadata"]
            })
        if permission == "owner":
            return self.finalizeOp(op, account["name"], "owner")
        else:
            return self.finalizeOp(op, account["name"], "active")

    def update_memo_key(self, key, account=None):
        """ Update an account's memo public key

            This method does **not** add any private keys to your
            wallet but merely changes the memo public key.

            :param str key: New memo public key
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
        """
        if not account:
            account = configStorage.get("default_account")
        if not account:
            raise ValueError("You need to provide an account")

        PublicKey(key)  # raises exception if invalid
        account = Account(account, steemd_instance=self.steemd)
        op = operations.AccountUpdate(
            **{
                "account": account["name"],
                "memo_key": key,
                "json_metadata": account["json_metadata"]
            })
        return self.finalizeOp(op, account["name"], "active")

    def approve_witness(self, witness, account=None, approve=True):
        """ Vote **for** a witness. This method adds a witness to your
            set of approved witnesses. To remove witnesses see
            ``disapprove_witness``.

            :param str witness: witness to approve
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
        """
        if not account:
            account = configStorage.get("default_account")
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, steemd_instance=self.steemd)
        op = operations.AccountWitnessVote(**{
            "account": account["name"],
            "witness": witness,
            "approve": approve,
        })
        return self.finalizeOp(op, account["name"], "active")

    def disapprove_witness(self, witness, account=None):
        """ Remove vote for a witness. This method removes
            a witness from your set of approved witnesses. To add
            witnesses see ``approve_witness``.

            :param str witness: witness to approve
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
        """
        return self.approve_witness(
            witness=witness, account=account, approve=False)

    def custom_json(self,
                    id,
                    json,
                    required_auths=[],
                    required_posting_auths=[]):
        """ Create a custom json operation

            :param str id: identifier for the custom json (max length 32 bytes)
            :param json json: the json data to put into the custom_json
                operation
            :param list required_auths: (optional) required auths
            :param list required_posting_auths: (optional) posting auths
        """
        account = None
        if len(required_auths):
            account = required_auths[0]
        elif len(required_posting_auths):
            account = required_posting_auths[0]
        else:
            raise Exception("At least one account needs to be specified")
        op = operations.CustomJson(
            **{
                "json": json,
                "required_auths": required_auths,
                "required_posting_auths": required_posting_auths,
                "id": id
            })
        return self.finalizeOp(op, account, "posting")

    def resteem(self, identifier, account=None):
        """ Resteem a post

            :param str identifier: post identifier (@<account>/<permlink>)
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
        """
        if not account:
            account = configStorage.get("default_account")
        if not account:
            raise ValueError("You need to provide an account")
        author, permlink = resolve_identifier(identifier)
        json_body = [
            "reblog", {
                "account": account,
                "author": author,
                "permlink": permlink
            }
        ]
        return self.custom_json(
            id="follow", json=json_body, required_posting_auths=[account])

    def unfollow(self, unfollow, what=["blog"], account=None):
        """ Unfollow another account's blog

            :param str unfollow: Follow this account
            :param list what: List of states to follow
                (defaults to ``['blog']``)
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
        """
        # FIXME: removing 'blog' from the array requires to first read
        # the follow.what from the blockchain
        return self.follow(unfollow, what=[], account=account)

    def follow(self, follow, what=["blog"], account=None):
        """ Follow another account's blog

            :param str follow: Follow this account
            :param list what: List of states to follow
                (defaults to ``['blog']``)
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
        """
        if not account:
            account = configStorage.get("default_account")
        if not account:
            raise ValueError("You need to provide an account")

        json_body = [
            'follow', {
                'follower': account,
                'following': follow,
                'what': what
            }
        ]
        return self.custom_json(
            id="follow", json=json_body, required_posting_auths=[account])

    def update_account_profile(self, profile, account=None):
        """ Update an account's meta data (json_meta)

            :param dict json: The meta data to use (i.e. use Profile() from
                account.py)
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
        """
        if not account:
            account = configStorage.get("default_account")
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, steemd_instance=self.steemd)
        op = operations.AccountUpdate(
            **{
                "account": account["name"],
                "memo_key": account["memo_key"],
                "json_metadata": profile
            })
        return self.finalizeOp(op, account["name"], "active")

    def comment_options(self, identifier, options, account=None):
        """ Set the comment options

            :param str identifier: Post identifier
            :param dict options: The options to define.
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)

            For the options, you have these defaults:::

                    {
                        "author": "",
                        "permlink": "",
                        "max_accepted_payout": "1000000.000 SBD",
                        "percent_steem_dollars": 10000,
                        "allow_votes": True,
                        "allow_curation_rewards": True,
                    }

        """
        if not account:
            account = configStorage.get("default_account")
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, steemd_instance=self.steemd)
        author, permlink = resolve_identifier(identifier)
        default_max_payout = "1000000.000 SBD"
        op = operations.CommentOptions(
            **{
                "author":
                author,
                "permlink":
                permlink,
                "max_accepted_payout":
                options.get("max_accepted_payout", default_max_payout),
                "percent_steem_dollars":
                options.get("percent_steem_dollars", 100) * STEEMIT_1_PERCENT,
                "allow_votes":
                options.get("allow_votes", True),
                "allow_curation_rewards":
                options.get("allow_curation_rewards", True),
            })
        return self.finalizeOp(op, account["name"], "posting")


if __name__ == "__main__":
    pass
