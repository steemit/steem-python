import json
import logging
import random
import re
from datetime import datetime, timedelta

from steembase import memo
from steembase import operations
from steembase.account import PrivateKey, PublicKey
from steembase.exceptions import (
    AccountExistsException,
    MissingKeyError,
)

from .account import Account
from .helpers import (
    resolveIdentifier,
    constructIdentifier,
    derivePermlink,
    formatTimeString
)
from .instance import shared_steemd_instance
from .post import Post
from .storage import configStorage as config
from .transactionbuilder import TransactionBuilder

log = logging.getLogger(__name__)

STEEMIT_100_PERCENT = 10000
STEEMIT_1_PERCENT = (STEEMIT_100_PERCENT / 100)


class Commit(object):
    """ Commit things to the Steem network.

        This class contains helper methods to construct, sign and broadcast common transactions, such as posting,
        voting, sending funds, etc.

        :param Steemd steemd: Steemd node to connect to*
        :param bool offline: Do **not** broadcast transactions! *(optional)*
        :param bool debug: Enable Debugging *(optional)*
        :param array,dict,string keys: Predefine the wif keys to shortcut the wallet database

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

    def __init__(self, steemd_instance=None, offline=False, debug=False, **kwargs):
        self.steemd = steemd_instance or shared_steemd_instance()
        self.debug = debug
        self.offline = offline
        self.unsigned = kwargs.get("unsigned", False)
        self.expiration = int(kwargs.get("expiration", 30))

        # self.wallet = Wallet(self.rpc, **kwargs)

    def finalizeOp(self, ops, account, permission):
        """ This method obtains the required private keys if present in
            the wallet, finalizes the transaction, signs it and
            broadacasts it

            :param operation ops: The operation (or list of operaions) to broadcast
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
        tx = TransactionBuilder(steemd_instance=self.steemd)
        tx.appendOps(ops)

        if self.unsigned:
            tx.addSigningInformation(account, permission)
            return tx
        else:
            tx.appendSigner(account, permission)
            tx.sign()

        return tx.broadcast()

    def sign(self, tx, wifs=[]):
        """ Sign a provided transaction witht he provided key(s)

            :param dict tx: The transaction to be signed and returned
            :param string wifs: One or many wif keys to use for signing
                a transaction. If not present, the keys will be loaded
                from the wallet as defined in "missing_signatures" key
                of the transactions.
        """
        tx = TransactionBuilder(tx, steemd_instance=self.steemd)
        tx.appendMissingSignatures(wifs)
        tx.sign()
        return tx.json()

    def broadcast(self, tx):
        """ Broadcast a transaction to the Steem network

            :param tx tx: Signed transaction to broadcast
        """
        tx = TransactionBuilder(tx, steemd_instance=self.steemd)
        return tx.broadcast()

    def reply(self, identifier, body, title="", author="", meta=None):
        """ Reply to an existing post

            :param str identifier: Identifier of the post to reply to. Takes the
                             form ``@author/permlink``
            :param str body: Body of the reply
            :param str title: Title of the reply post
            :param str author: Author of reply (optional) if not provided
                               ``default_user`` will be used, if present, else
                               a ``ValueError`` will be raised.
            :param json meta: JSON meta object that can be attached to the
                              post. (optional)
        """
        return self.post(title,
                         body,
                         meta=meta,
                         author=author,
                         reply_identifier=identifier)

    def edit(self,
             identifier,
             body,
             meta={},
             replace=False):
        """ Edit an existing post

            :param str identifier: Identifier of the post to reply to. Takes the
                             form ``@author/permlink``
            :param str body: Body of the reply
            :param json meta: JSON meta object that can be attached to the
                              post. (optional)
            :param bool replace: Instead of calculating a *diff*, replace
                                 the post entirely (defaults to ``False``)
        """
        original_post = Post(identifier, steemd_instance=self.steemd)

        if replace:
            newbody = body
        else:
            import diff_match_patch
            dmp = diff_match_patch.diff_match_patch()
            patch = dmp.patch_make(original_post["body"], body)
            newbody = dmp.patch_toText(patch)

            if not newbody:
                log.info("No changes made! Skipping ...")
                return

        reply_identifier = constructIdentifier(
            original_post["parent_author"],
            original_post["parent_permlink"]
        )

        new_meta = {}
        if meta:
            if original_post["json_metadata"]:
                import json
                new_meta = original_post["json_metadata"].update(meta)
            else:
                new_meta = meta

        return self.post(
            original_post["title"],
            newbody,
            reply_identifier=reply_identifier,
            author=original_post["author"],
            permlink=original_post["permlink"],
            meta=new_meta,
        )

    def post(self,
             title,
             body,
             author=None,
             permlink=None,
             meta={},
             reply_identifier=None,
             category=None,
             tags=[]):
        """ New post

            :param str title: Title of the reply post
            :param str body: Body of the reply
            :param str author: Author of reply (optional) if not provided
                               ``default_user`` will be used, if present, else
                               a ``ValueError`` will be raised.
            :param json meta: JSON meta object that can be attached to the
                              post. This can be used to add ``tags`` or ``options``.
                              The default options are:::

                                   {
                                        "author": "",
                                        "permlink": "",
                                        "max_accepted_payout": "1000000.000 SBD",
                                        "percent_steem_dollars": 10000,
                                        "allow_votes": True,
                                        "allow_curation_rewards": True,
                                    }

            :param str reply_identifier: Identifier of the post to reply to. Takes the
                                         form ``@author/permlink``
            :param str category: (deprecated, see ``tags``) Allows to
                define a category for new posts.  It is highly recommended
                to provide a category as posts end up in ``spam`` otherwise.
                If no category is provided but ``tags``, then the first tag
                will be used as category
            :param array tags: The tags to flag the post with. If no
                category is used, then the first tag will be used as
                category
        """

        if not author and config["default_author"]:
            author = config["default_author"]

        if not author:
            raise ValueError("Please define an author.")

        # Deal with meta data
        if not isinstance(meta, dict):
            try:
                meta = json.loads(meta)
            except:
                meta = {}

        # Identify the comment options
        options = {}
        if "max_accepted_payout" in meta:
            options["max_accepted_payout"] = meta.pop("max_accepted_payout", None)
        if "percent_steem_dollars" in meta:
            options["percent_steem_dollars"] = meta.pop("percent_steem_dollars", None)
        if "allow_votes" in meta:
            options["allow_votes"] = meta.pop("allow_votes", None)
        if "allow_curation_rewards" in meta:
            options["allow_curation_rewards"] = meta.pop("allow_curation_rewards", None)

        # deal with the category and tags
        if isinstance(tags, str):
            tags = list(filter(None, (re.split("[\W_]", tags))))
        if not category and tags:
            # extract the first tag
            category = tags[0]
            tags = list(set(tags))
            # do not use the first tag in tags
            meta.update({"tags": tags[1:]})
        elif tags:
            # store everything in tags
            tags = list(set(tags))
            meta.update({"tags": tags})

        # Deal with replies
        if reply_identifier and not category:
            parent_author, parent_permlink = resolveIdentifier(reply_identifier)
            if not permlink:
                permlink = derivePermlink(title, parent_permlink)
        elif category and not reply_identifier:
            parent_permlink = derivePermlink(category)
            parent_author = ""
            if not permlink:
                permlink = derivePermlink(title)
        elif not category and not reply_identifier:
            parent_author = ""
            parent_permlink = ""
            if not permlink:
                permlink = derivePermlink(title)
        else:
            raise ValueError(
                "You can't provide a category while replying to a post"
            )

        postOp = operations.Comment(
            **{"parent_author": parent_author,
               "parent_permlink": parent_permlink,
               "author": author,
               "permlink": permlink,
               "title": title,
               "body": body,
               "json_metadata": meta}
        )
        op = [postOp]

        # If comment_options are used, add a new op to the transaction
        if options:
            default_max_payout = "1000000.000 SBD"
            op.append(
                operations.CommentOptions(**{
                    "author": author,
                    "permlink": permlink,
                    "max_accepted_payout": options.get("max_accepted_payout", default_max_payout),
                    "percent_steem_dollars": int(
                        options.get("percent_steem_dollars", 100) * STEEMIT_1_PERCENT
                    ),
                    "allow_votes": options.get("allow_votes", True),
                    "allow_curation_rewards": options.get("allow_curation_rewards", True)}))

        return self.finalizeOp(op, author, "posting")

    def vote(self,
             identifier,
             weight,
             voter=None):
        """ Vote for a post

            :param str identifier: Identifier for the post to upvote Takes
                                   the form ``@author/permlink``
            :param float weight: Voting weight. Range: -100.0 - +100.0. May
                                 not be 0.0
            :param str voter: Voter to use for voting. (Optional)

            If ``voter`` is not defines, the ``default_voter`` will be taken or
            a ValueError will be raised

            .. code-block:: python

                piston set default_voter <account>
        """
        if not voter:
            if "default_voter" in config:
                voter = config["default_voter"]
        if not voter:
            raise ValueError("You need to provide a voter account")

        post_author, post_permlink = resolveIdentifier(identifier)

        op = operations.Vote(
            **{"voter": voter,
               "author": post_author,
               "permlink": post_permlink,
               "weight": int(weight * STEEMIT_1_PERCENT)}
        )

        return self.finalizeOp(op, voter, "posting")

    def create_account(self,
                       account_name,
                       json_meta={},
                       creator=None,
                       owner_key=None,
                       active_key=None,
                       posting_key=None,
                       memo_key=None,
                       password=None,
                       additional_owner_keys=[],
                       additional_active_keys=[],
                       additional_posting_keys=[],
                       additional_owner_accounts=[],
                       additional_active_accounts=[],
                       additional_posting_accounts=[],
                       storekeys=True,
                       ):
        """ Create new account in Steem

            The brainkey/password can be used to recover all generated keys (see
            `pistonbase.account` for more details.

            By default, this call will use ``default_author`` to
            register a new name ``account_name`` with all keys being
            derived from a new brain key that will be returned. The
            corresponding keys will automatically be installed in the
            wallet.

            .. note:: Account creations cost a fee that is defined by
                       the network. If you create an account, you will
                       need to pay for that fee!

            .. warning:: Don't call this method unless you know what
                          you are doing! Be sure to understand what this
                          method does and where to find the private keys
                          for your account.

            .. note:: Please note that this imports private keys
                      (if password is present) into the wallet by
                      default. However, it **does not import the owner
                      key** for security reasons. Do NOT expect to be
                      able to recover it from the wallet if you lose
                      your password!

            :param str account_name: (**required**) new account name
            :param str json_meta: Optional meta data for the account
            :param str creator: which account should pay the registration fee
                                (defaults to ``default_author``)
            :param str owner_key: Main owner key
            :param str active_key: Main active key
            :param str posting_key: Main posting key
            :param str memo_key: Main memo_key
            :param str password: Alternatively to providing keys, one
                                 can provide a password from which the
                                 keys will be derived
            :param array additional_owner_keys:  Additional owner public keys
            :param array additional_active_keys: Additional active public keys
            :param array additional_posting_keys: Additional posting public keys
            :param array additional_owner_accounts: Additional owner account names
            :param array additional_active_accounts: Additional acctive account names
            :param array additional_posting_accounts: Additional posting account names
            :param bool storekeys: Store new keys in the wallet (default: ``True``)
            :raises AccountExistsException: if the account already exists on the blockchain

        """
        assert len(account_name) <= 16, "Account name must be at most 16 chars long"

        if not creator and config["default_author"]:
            creator = config["default_author"]
        if not creator:
            raise ValueError(
                "Not creator account given. Define it with " +
                "creator=x, or set the default_author using piston")
        if password and (owner_key or posting_key or active_key or memo_key):
            raise ValueError(
                "You cannot use 'password' AND provide keys!"
            )

        account = None
        try:
            account = Account(account_name, steemd_instance=self.steemd)
        except:
            pass
        if account:
            raise AccountExistsException

        " Generate new keys from password"
        from pistonbase.account import PasswordKey, PublicKey
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
            # owner_privkey   = owner_key.get_private_key()
            memo_privkey = memo_key.get_private_key()
            # store private keys
            if storekeys:
                # self.wallet.addPrivateKey(owner_privkey)
                self.wallet.addPrivateKey(active_privkey)
                self.wallet.addPrivateKey(posting_privkey)
                self.wallet.addPrivateKey(memo_privkey)
        elif (owner_key and posting_key and active_key and memo_key):
            posting_pubkey = PublicKey(posting_key, prefix=self.steemd.chain_params["prefix"])
            active_pubkey = PublicKey(active_key, prefix=self.steemd.chain_params["prefix"])
            owner_pubkey = PublicKey(owner_key, prefix=self.steemd.chain_params["prefix"])
            memo_pubkey = PublicKey(memo_key, prefix=self.steemd.chain_params["prefix"])
        else:
            raise ValueError(
                "Call incomplete! Provide either a password or public keys!"
            )

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
        fee = props["account_creation_fee"]
        s = {'creator': creator,
             'fee': fee,
             'json_metadata': json_meta,
             'memo_key': memo,
             'new_account_name': account_name,
             'owner': {'account_auths': owner_accounts_authority,
                       'key_auths': owner_key_authority,
                       'weight_threshold': 1},
             'active': {'account_auths': active_accounts_authority,
                        'key_auths': active_key_authority,
                        'weight_threshold': 1},
             'posting': {'account_auths': posting_accounts_authority,
                         'key_auths': posting_key_authority,
                         'weight_threshold': 1},
             'prefix': self.steemd.chain_params["prefix"]}

        op = operations.AccountCreate(**s)

        return self.finalizeOp(op, creator, "active")

    def transfer(self, to, amount, asset, memo="", account=None):
        """ Transfer SBD or STEEM to another account.

            :param str to: Recipient
            :param float amount: Amount to transfer
            :param str asset: Asset to transfer (``SBD`` or ``STEEM``)
            :param str memo: (optional) Memo, may begin with `#` for encrypted messaging
            :param str account: (optional) the source account for the transfer if not ``default_account``
        """
        if not account:
            if "default_account" in config:
                account = config["default_account"]
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
                PublicKey(to_account["memo_key"], prefix=self.steemd.chain_params["prefix"]),
                nonce,
                memo,
                prefix=self.steemd.chain_params["prefix"]
            )

        op = operations.Transfer(
            **{"from": account,
               "to": to,
               "amount": '{:.{prec}f} {asset}'.format(
                   float(amount),
                   prec=3,
                   asset=asset
               ),
               "memo": memo
               }
        )
        return self.finalizeOp(op, account, "active")

    def withdraw_vesting(self, amount, account=None):
        """ Withdraw VESTS from the vesting account.

            :param float amount: number of VESTS to withdraw over a period of 104 weeks
            :param str account: (optional) the source account for the transfer if not ``default_account``
        """
        if not account:
            if "default_account" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        op = operations.WithdrawVesting(
            **{"account": account,
               "vesting_shares": '{:.{prec}f} {asset}'.format(
                   float(amount),
                   prec=6,
                   asset="VESTS"
               ),
               }
        )

        return self.finalizeOp(op, account, "active")

    def transfer_to_vesting(self, amount, to=None, account=None):
        """ Vest STEEM

            :param float amount: number of STEEM to vest
            :param str to: (optional) the source account for the transfer if not ``default_account``
            :param str account: (optional) the source account for the transfer if not ``default_account``
        """
        if not account:
            if "default_account" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        if not to:
            to = account  # powerup on the same account

        op = operations.TransferToVesting(
            **{"from": account,
               "to": to,
               "amount": '{:.{prec}f} {asset}'.format(
                   float(amount),
                   prec=3,
                   asset='STEEM')
               }
        )

        return self.finalizeOp(op, account, "active")

    def convert(self, amount, account=None, requestid=None):
        """ Convert SteemDollars to Steem (takes one week to settle)

            :param float amount: number of VESTS to withdraw over a period of 104 weeks
            :param str account: (optional) the source account for the transfer if not ``default_account``
            :param str requestid: (optional) identifier for tracking the conversion`
        """
        if not account and "default_account" in config:
            account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        if requestid:
            requestid = int(requestid)
        else:
            requestid = random.getrandbits(32)
        op = operations.Convert(
            **{"owner": account,
               "requestid": requestid,
               "amount": '{:.{prec}f} {asset}'.format(
                   float(amount),
                   prec=3,
                   asset='SBD'
               )}
        )

        return self.finalizeOp(op, account, "active")

    def transfer_to_savings(self, amount, currency, memo, to=None, account=None):
        """ Transfer SBD or STEEM into a 'savings' account.

            :param float amount: STEEM or SBD amount
            :param float currency: 'STEEM' or 'SBD'
            :param str memo: (optional) Memo
            :param str to: (optional) the source account for the transfer if not ``default_account``
            :param str account: (optional) the source account for the transfer if not ``default_account``
        """
        assert currency in ['STEEM', 'SBD']

        if not account:
            if "default_account" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        if not to:
            to = account  # move to savings on same account

        op = operations.TransferToSavings(
            **{
                "from": account,
                "to": to,
                "amount": '{:.{prec}f} {asset}'.format(
                    float(amount),
                    prec=3,
                    asset=currency),
                "memo": memo,
            }
        )
        return self.finalizeOp(op, account, "active")

    def transfer_from_savings(self, amount, currency, memo, request_id=None, to=None, account=None):
        """ Withdraw SBD or STEEM from 'savings' account.

            :param float amount: STEEM or SBD amount
            :param float currency: 'STEEM' or 'SBD'
            :param str memo: (optional) Memo
            :param str request_id: (optional) identifier for tracking or cancelling the withdrawal
            :param str to: (optional) the source account for the transfer if not ``default_account``
            :param str account: (optional) the source account for the transfer if not ``default_account``
        """
        assert currency in ['STEEM', 'SBD']

        if not account:
            if "default_account" in config:
                account = config["default_account"]
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
                "from": account,
                "request_id": request_id,
                "to": to,
                "amount": '{:.{prec}f} {asset}'.format(
                    float(amount),
                    prec=3,
                    asset=currency),
                "memo": memo,
            }
        )
        return self.finalizeOp(op, account, "active")

    def transfer_from_savings_cancel(self, request_id, account=None):
        """ Cancel a withdrawal from 'savings' account.

            :param str request_id: Identifier for tracking or cancelling the withdrawal
            :param str account: (optional) the source account for the transfer if not ``default_account``
        """
        if not account:
            if "default_account" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        op = operations.CancelTransferFromSavings(
            **{
                "from": account,
                "request_id": request_id,
            }
        )
        return self.finalizeOp(op, account, "active")

    def witness_feed_publish(self, steem_usd_price, quote="1.000", account=None):
        """ Publish a feed price as a witness.

            :param float steem_usd_price: Price of STEEM in USD (implied price)
            :param float quote: (optional) Quote Price. Should be 1.000, unless we are adjusting the feed to support the peg.
            :param str account: (optional) the source account for the transfer if not ``default_account``
        """
        if not account:
            if "default_account" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        op = operations.FeedPublish(
            **{
                "publisher": account,
                "exchange_rate": {
                    "base": "%s SBD" % steem_usd_price,
                    "quote": "%s STEEM" % quote,
                }
            }
        )
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
            if "default_account" in config:
                account = config["default_account"]
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
            }
        )
        return self.finalizeOp(op, account, "active")

    def decode_memo(self, enc_memo, account):
        """ Try to decode an encrypted memo
        """
        assert enc_memo[0] == "#", "decode memo requires memos to start with '#'"
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
        account = Account(account, steemd_instance=self.steemd.rpc)
        last_payment = formatTimeString(account["sbd_last_interest_payment"])
        next_payment = last_payment + timedelta(days=30)
        interest_rate = self.steemd.get_dynamic_global_properties()["sbd_interest_rate"] / 100  # the result is in percent!
        interest_amount = (interest_rate / 100) * int(
            int(account["sbd_seconds"]) / (60 * 60 * 24 * 356)
        ) * 10 ** -3

        return {
            "interest": interest_amount,
            "last_payment": last_payment,
            "next_payment": next_payment,
            "next_payment_duration": next_payment - datetime.now(),
            "interest_rate": interest_rate,
        }

    def set_withdraw_vesting_route(self, to, percentage=100,
                                   account=None, auto_vest=False):
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
            if "default_account" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        op = operations.SetWithdrawVestingRoute(
            **{"from_account": account,
               "to_account": to,
               "percent": int(percentage * STEEMIT_1_PERCENT),
               "auto_vest": auto_vest
               }
        )

        return self.finalizeOp(op, account, "active")

    def _test_weights_treshold(self, authority):
        weights = 0
        for a in authority["account_auths"]:
            weights += a[1]
        for a in authority["key_auths"]:
            weights += a[1]
        if authority["weight_threshold"] > weights:
            raise ValueError("Threshold too restrictive!")

    def allow(self, foreign, weight=None, permission="posting",
              account=None, threshold=None):
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
                to (defaults to ``default_author``)
            :param int threshold: The threshold that needs to be reached
                by signatures to be able to interact
        """
        if not account:
            if "default_author" in config:
                account = config["default_author"]
        if not account:
            raise ValueError("You need to provide an account")

        if permission not in ["owner", "posting", "active"]:
            raise ValueError(
                "Permission needs to be either 'owner', 'posting', or 'active"
            )
        account = Account(account, steemd_instance=self.steemd)
        if not weight:
            weight = account[permission]["weight_threshold"]

        authority = account[permission]
        try:
            pubkey = PublicKey(foreign)
            authority["key_auths"].append([
                str(pubkey),
                weight
            ])
        except:
            try:
                foreign_account = Account(foreign, steemd_instance=self.steemd)
                authority["account_auths"].append([
                    foreign_account["name"],
                    weight
                ])
            except:
                raise ValueError(
                    "Unknown foreign account or unvalid public key"
                )
        if threshold:
            authority["weight_threshold"] = threshold
            self._test_weights_treshold(authority)

        op = operations.AccountUpdate(
            **{"account": account["name"],
               permission: authority,
               "memo_key": account["memo_key"],
               "json_metadata": account["json_metadata"],
               'prefix': self.steemd.chain_params["prefix"]}
        )
        if permission == "owner":
            return self.finalizeOp(op, account["name"], "owner")
        else:
            return self.finalizeOp(op, account["name"], "active")

    def disallow(self, foreign, permission="posting",
                 account=None, threshold=None):
        """ Remove additional access to an account by some other public
            key or account.

            :param str foreign: The foreign account that will obtain access
            :param str permission: (optional) The actual permission to
                modify (defaults to ``posting``)
            :param str account: (optional) the account to allow access
                to (defaults to ``default_author``)
            :param int threshold: The threshold that needs to be reached
                by signatures to be able to interact
        """
        if not account:
            if "default_author" in config:
                account = config["default_author"]
        if not account:
            raise ValueError("You need to provide an account")

        if permission not in ["owner", "posting", "active"]:
            raise ValueError(
                "Permission needs to be either 'owner', 'posting', or 'active"
            )
        account = Account(account, steemd_instance=self.steemd)
        authority = account[permission]

        try:
            pubkey = PublicKey(foreign, prefix=self.steemd.chain_params["prefix"])
            affected_items = list(
                filter(lambda x: x[0] == str(pubkey),
                       authority["key_auths"]))
            authority["key_auths"] = list(filter(
                lambda x: x[0] != str(pubkey),
                authority["key_auths"]
            ))
        except:
            try:
                foreign_account = Account(foreign, steemd_instance=self.steemd)
                affected_items = list(
                    filter(lambda x: x[0] == foreign_account["name"],
                           authority["account_auths"]))
                authority["account_auths"] = list(filter(
                    lambda x: x[0] != foreign_account["name"],
                    authority["account_auths"]
                ))
            except:
                raise ValueError(
                    "Unknown foreign account or unvalid public key"
                )

        removed_weight = affected_items[0][1]

        # Define threshold
        if threshold:
            authority["weight_threshold"] = threshold

        # Correct threshold (at most by the amount removed from the
        # authority)
        try:
            self._test_weights_treshold(authority)
        except:
            log.critical(
                "The account's threshold will be reduced by %d"
                % removed_weight
            )
            authority["weight_threshold"] -= removed_weight
            self._test_weights_treshold(authority)

        op = operations.AccountUpdate(
            **{"account": account["name"],
               permission: authority,
               "memo_key": account["memo_key"],
               "json_metadata": account["json_metadata"]}
        )
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
                to (defaults to ``default_author``)
        """
        if not account:
            if "default_author" in config:
                account = config["default_author"]
        if not account:
            raise ValueError("You need to provide an account")

        PublicKey(key)  # raises exception if invalid
        account = Account(account, steemd_instance=self.steemd)
        op = operations.AccountUpdate(
            **{"account": account["name"],
               "memo_key": key,
               "json_metadata": account["json_metadata"]}
        )
        return self.finalizeOp(op, account["name"], "active")

    def approve_witness(self, witness, account=None, approve=True):
        """ Vote **for** a witness. This method adds a witness to your
            set of approved witnesses. To remove witnesses see
            ``disapprove_witness``.

            :param str witness: witness to approve
            :param str account: (optional) the account to allow access
                to (defaults to ``default_author``)
        """
        if not account:
            if "default_author" in config:
                account = config["default_author"]
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, steemd_instance=self.steemd)
        op = operations.AccountWitnessVote(
            **{"account": account["name"],
               "witness": witness,
               "approve": approve,
               })
        return self.finalizeOp(op, account["name"], "active")

    def disapprove_witness(self, witness, account=None, approve=True):
        """ Remove vote for a witness. This method removes
            a witness from your set of approved witnesses. To add
            witnesses see ``approve_witness``.

            :param str witness: witness to approve
            :param str account: (optional) the account to allow access
                to (defaults to ``default_author``)
        """
        return self.approve_witness(witness=witness, account=account, approve=False)

    def custom_json(self, id, json, required_auths=[], required_posting_auths=[]):
        """ Create a custom json operation

            :param str id: identifier for the custom json (max length 32 bytes)
            :param json json: the json data to put into the custom_json operation
            :param list required_auths: (optional) required auths
            :param list required_posting_auths: (optional) posting auths
        """
        account = None
        if len(required_auths):
            account = required_auths[0]
        elif len(required_posting_auths):
            account = required_posting_auths[0]
        else:
            raise Exception("At least on account needs to be specified")
        op = operations.CustomJson(
            **{"json": json,
               "required_auths": required_auths,
               "required_posting_auths": required_posting_auths,
               "id": id})
        return self.finalizeOp(op, account, "posting")

    def resteem(self, identifier, account=None):
        """ Resteem a post

            :param str identifier: post identifier (@<account>/<permlink>)
            :param str account: (optional) the account to allow access
                to (defaults to ``default_author``)
        """
        if not account:
            if "default_author" in config:
                account = config["default_author"]
        if not account:
            raise ValueError("You need to provide an account")
        author, permlink = resolveIdentifier(identifier)
        return self.custom_json(
            id="follow",
            json=["reblog",
                  {"account": account,
                   "author": author,
                   "permlink": permlink
                   }],
            required_posting_auths=[account]
        )

    def unfollow(self, unfollow, what=["blog"], account=None):
        """ Unfollow another account's blog

            :param str unfollow: Follow this account
            :param list what: List of states to follow (defaults to ``['blog']``)
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
        """
        # FIXME: removing 'blog' from the array requires to first read
        # the follow.what from the blockchain
        return self.follow(unfollow, what=[], account=account)

    def follow(self, follow, what=["blog"], account=None):
        """ Follow another account's blog

            :param str follow: Follow this account
            :param list what: List of states to follow (defaults to ``['blog']``)
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
        """
        if not account:
            if "default_account" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")
        return self.custom_json(
            id="follow",
            json=['follow', {
                'follower': account,
                'following': follow,
                'what': what}],
            required_posting_auths=[account]
        )

    def update_account_profile(self, profile, account=None):
        """ Update an account's meta data (json_meta)

            :param dict json: The meta data to use (i.e. use Profile() from account.py)
            :param str account: (optional) the account to allow access
                to (defaults to ``default_account``)
        """
        if not account:
            if "default_author" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, steemd_instance=self.steemd)
        op = operations.AccountUpdate(
            **{"account": account["name"],
               "memo_key": account["memo_key"],
               "json_metadata": profile}
        )
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
            if "default_author" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, steemd_instance=self.steemd)
        author, permlink = resolveIdentifier(identifier)
        default_max_payout = "1000000.000 SBD"
        op = operations.CommentOptions(
            **{
                "author": author,
                "permlink": permlink,
                "max_accepted_payout": options.get("max_accepted_payout", default_max_payout),
                "percent_steem_dollars": options.get("percent_steem_dollars", 100) * STEEMIT_1_PERCENT,
                "allow_votes": options.get("allow_votes", True),
                "allow_curation_rewards": options.get("allow_curation_rewards", True),
            }
        )
        return self.finalizeOp(op, account["name"], "posting")


if __name__ == "__main__":
    c = Commit()
    c.transfer(to='fnait', amount='0.001', asset='STEEM', memo='libtest', account='furion')
