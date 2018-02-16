import importlib
import json
import re
import struct
from collections import OrderedDict

from .account import PublicKey
from .operationids import operations
from .types import (Int16, Uint16, Uint32, Uint64, String, Bytes, Array,
                    PointInTime, Bool, Optional, Map, Id, JsonObj,
                    StaticVariant)

default_prefix = "STM"

asset_precision = {
    "STEEM": 3,
    "VESTS": 6,
    "SBD": 3,
}


class Operation:
    def __init__(self, op):
        if isinstance(op, list) and len(op) == 2:
            if isinstance(op[0], int):
                self.opId = op[0]
                name = self.get_operation_name_for_id(self.opId)
            else:
                self.opId = operations.get(op[0], None)
                name = op[0]
                if self.opId is None:
                    raise ValueError("Unknown operation")

            # convert method name like feed_publish to class
            # name like FeedPublish
            self.name = self.to_class_name(name)
            try:
                klass = self.get_class(self.name)
            except:  # noqa FIXME(sneak)
                raise NotImplementedError(
                    "Unimplemented Operation %s" % self.name)
            else:
                self.op = klass(op[1])
        else:
            self.op = op
            # class name like FeedPublish
            self.name = type(self.op).__name__
            self.opId = operations[self.to_method_name(self.name)]

    @staticmethod
    def get_operation_name_for_id(_id):
        """ Convert an operation id into the corresponding string
        """
        for key, value in operations.items():
            if value == int(_id):
                return key

    @staticmethod
    def to_class_name(method_name):
        """ Take a name of a method, like feed_publish and turn it into
        class name like FeedPublish. """
        return ''.join(map(str.title, method_name.split('_')))

    @staticmethod
    def to_method_name(class_name):
        """ Take a name of a class, like FeedPublish and turn it into
        method name like feed_publish. """
        words = re.findall('[A-Z][^A-Z]*', class_name)
        return '_'.join(map(str.lower, words))

    @staticmethod
    def get_class(class_name):
        """ Given name of a class from `operations`, return real class. """
        module = importlib.import_module('steembase.operations')
        return getattr(module, class_name)

    def to_bytes(self):
        return bytes(Id(self.opId)) + bytes(self.op)

    def __str__(self):
        return json.dumps(
            [self.get_operation_name_for_id(self.opId),
             self.op.json()])


class GrapheneObject(object):
    """ Core abstraction class

        This class is used for any JSON reflected object in Graphene.

        * ``instance.__json__()``: encodes data into json format
        * ``bytes(instance)``: encodes data into wire format
        * ``str(instances)``: dumps json object as string

    """

    def __init__(self, data=None):
        self.data = data

    def to_bytes(self):
        if self.data is None:
            return bytes()
        b = b""
        for name, value in self.data.items():
            if isinstance(value, str):
                b += bytes(value, 'utf-8')
            else:
                b += bytes(value)
        return b

    def __json__(self):
        if self.data is None:
            return {}
        d = {}  # JSON output is *not* ordered
        for name, value in self.data.items():
            if isinstance(value, Optional) and value.isempty():
                continue

            if isinstance(value, String):
                d.update({name: str(value)})
            else:
                d.update({name: JsonObj(value)})
        return d

    def __str__(self):
        return json.dumps(self.__json__())

    def toJson(self):
        return self.__json__()

    def json(self):
        return self.__json__()


class Permission(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            prefix = kwargs.pop("prefix", default_prefix)

            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            # Sort keys (FIXME: ideally, the sorting is part of Public
            # Key and not located here)
            kwargs["key_auths"] = sorted(
                kwargs["key_auths"],
                key=lambda x: repr(PublicKey(x[0], prefix=prefix)),
                reverse=False,
            )
            kwargs["account_auths"] = sorted(
                kwargs["account_auths"],
                key=lambda x: x[0],
                reverse=False,
            )

            accountAuths = Map([[String(e[0]), Uint16(e[1])]
                                for e in kwargs["account_auths"]])
            keyAuths = Map([[PublicKey(e[0], prefix=prefix),
                             Uint16(e[1])] for e in kwargs["key_auths"]])
            super(Permission, self).__init__(
                OrderedDict([
                    ('weight_threshold', Uint32(
                        int(kwargs["weight_threshold"]))),
                    ('account_auths', accountAuths),
                    ('key_auths', keyAuths),
                ]))


class Memo(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            prefix = kwargs.pop("prefix", default_prefix)

            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            super(Memo, self).__init__(
                OrderedDict([
                    ('from', PublicKey(kwargs["from"], prefix=prefix)),
                    ('to', PublicKey(kwargs["to"], prefix=prefix)),
                    ('nonce', Uint64(int(kwargs["nonce"]))),
                    ('check', Uint32(int(kwargs["check"]))),
                    ('encrypted', Bytes(kwargs["encrypted"])),
                ]))


class Vote(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super(Vote, self).__init__(
                OrderedDict([
                    ('voter', String(kwargs["voter"])),
                    ('author', String(kwargs["author"])),
                    ('permlink', String(kwargs["permlink"])),
                    ('weight', Int16(kwargs["weight"])),
                ]))


class Comment(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            meta = ""
            if "json_metadata" in kwargs and kwargs["json_metadata"]:
                if (isinstance(kwargs["json_metadata"], dict)
                        or isinstance(kwargs["json_metadata"], list)):
                    meta = json.dumps(kwargs["json_metadata"])
                else:
                    meta = kwargs["json_metadata"]

            super(Comment, self).__init__(
                OrderedDict([
                    ('parent_author', String(kwargs["parent_author"])),
                    ('parent_permlink', String(kwargs["parent_permlink"])),
                    ('author', String(kwargs["author"])),
                    ('permlink', String(kwargs["permlink"])),
                    ('title', String(kwargs["title"])),
                    ('body', String(kwargs["body"])),
                    ('json_metadata', String(meta)),
                ]))


class Amount:
    def __init__(self, d):
        self.amount, self.asset = d.strip().split(" ")
        self.amount = float(self.amount)

        if self.asset in asset_precision:
            self.precision = asset_precision[self.asset]
        else:
            raise Exception("Asset unknown")

    def to_bytes(self):
        # padding
        asset = self.asset + "\x00" * (7 - len(self.asset))
        amount = round(float(self.amount) * 10**self.precision)
        return (struct.pack("<q", amount) + struct.pack("<b", self.precision) +
                bytes(asset, "ascii"))

    def __str__(self):
        return '{:.{}f} {}'.format(self.amount, self.precision, self.asset)


class ExchangeRate(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            super(ExchangeRate, self).__init__(
                OrderedDict([
                    ('base', Amount(kwargs["base"])),
                    ('quote', Amount(kwargs["quote"])),
                ]))


class WitnessProps(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            super(WitnessProps, self).__init__(
                OrderedDict([
                    ('account_creation_fee',
                     Amount(kwargs["account_creation_fee"])),
                    ('maximum_block_size',
                     Uint32(kwargs["maximum_block_size"])),
                    ('sbd_interest_rate', Uint16(kwargs["sbd_interest_rate"])),
                ]))


class Beneficiary(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super(Beneficiary, self).__init__(
                OrderedDict([
                    ('account', String(kwargs["account"])),
                    ('weight', Int16(kwargs["weight"])),
                ]))


class Beneficiaries(GrapheneObject):
    def __init__(self, kwargs):
        super(Beneficiaries, self).__init__(
            OrderedDict([
                ('beneficiaries',
                 Array([Beneficiary(o) for o in kwargs["beneficiaries"]])),
            ]))


class CommentOptionExtensions(StaticVariant):
    """ Serialize Comment Payout Beneficiaries.

    Args:
        beneficiaries (list): A static_variant containing beneficiaries.

    Example:

        ::

            [0,
                {'beneficiaries': [
                    {'account': 'furion', 'weight': 10000}
                ]}
            ]
    """

    def __init__(self, o):
        type_id, data = o
        if type_id == 0:
            data = Beneficiaries(data)
        else:
            raise Exception("Unknown CommentOptionExtension")
        StaticVariant.__init__(self, data, type_id)


########################################################
# Actual Operations
########################################################


class AccountCreate(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            prefix = kwargs.pop("prefix", default_prefix)

            assert len(kwargs["new_account_name"]
                       ) <= 16, "Account name must be at most 16 chars long"

            meta = ""
            if "json_metadata" in kwargs and kwargs["json_metadata"]:
                if isinstance(kwargs["json_metadata"], dict):
                    meta = json.dumps(kwargs["json_metadata"])
                else:
                    meta = kwargs["json_metadata"]
            super(AccountCreate, self).__init__(
                OrderedDict([
                    ('fee', Amount(kwargs["fee"])),
                    ('creator', String(kwargs["creator"])),
                    ('new_account_name', String(kwargs["new_account_name"])),
                    ('owner', Permission(kwargs["owner"], prefix=prefix)),
                    ('active', Permission(kwargs["active"], prefix=prefix)),
                    ('posting', Permission(kwargs["posting"], prefix=prefix)),
                    ('memo_key', PublicKey(kwargs["memo_key"], prefix=prefix)),
                    ('json_metadata', String(meta)),
                ]))


class AccountCreateWithDelegation(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            prefix = kwargs.pop("prefix", default_prefix)

            assert len(kwargs["new_account_name"]
                       ) <= 16, "Account name must be at most 16 chars long"

            meta = ""
            if "json_metadata" in kwargs and kwargs["json_metadata"]:
                if isinstance(kwargs["json_metadata"], dict):
                    meta = json.dumps(kwargs["json_metadata"])
                else:
                    meta = kwargs["json_metadata"]
            super(AccountCreateWithDelegation, self).__init__(
                OrderedDict([
                    ('fee', Amount(kwargs["fee"])),
                    ('delegation', Amount(kwargs["delegation"])),
                    ('creator', String(kwargs["creator"])),
                    ('new_account_name', String(kwargs["new_account_name"])),
                    ('owner', Permission(kwargs["owner"], prefix=prefix)),
                    ('active', Permission(kwargs["active"], prefix=prefix)),
                    ('posting', Permission(kwargs["posting"], prefix=prefix)),
                    ('memo_key', PublicKey(kwargs["memo_key"], prefix=prefix)),
                    ('json_metadata', String(meta)),
                    ('extensions', Array([])),
                ]))


class AccountUpdate(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            prefix = kwargs.pop("prefix", default_prefix)

            meta = ""
            if "json_metadata" in kwargs and kwargs["json_metadata"]:
                if isinstance(kwargs["json_metadata"], dict):
                    meta = json.dumps(kwargs["json_metadata"])
                else:
                    meta = kwargs["json_metadata"]

            owner = Permission(
                kwargs["owner"], prefix=prefix) if "owner" in kwargs else None
            active = Permission(
                kwargs["active"],
                prefix=prefix) if "active" in kwargs else None
            posting = Permission(
                kwargs["posting"],
                prefix=prefix) if "posting" in kwargs else None

            super(AccountUpdate, self).__init__(
                OrderedDict([
                    ('account', String(kwargs["account"])),
                    ('owner', Optional(owner)),
                    ('active', Optional(active)),
                    ('posting', Optional(posting)),
                    ('memo_key', PublicKey(kwargs["memo_key"], prefix=prefix)),
                    ('json_metadata', String(meta)),
                ]))


class Transfer(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            if "memo" not in kwargs:
                kwargs["memo"] = ""
            super(Transfer, self).__init__(
                OrderedDict([
                    ('from', String(kwargs["from"])),
                    ('to', String(kwargs["to"])),
                    ('amount', Amount(kwargs["amount"])),
                    ('memo', String(kwargs["memo"])),
                ]))


class TransferToVesting(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super(TransferToVesting, self).__init__(
                OrderedDict([
                    ('from', String(kwargs["from"])),
                    ('to', String(kwargs["to"])),
                    ('amount', Amount(kwargs["amount"])),
                ]))


class WithdrawVesting(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super(WithdrawVesting, self).__init__(
                OrderedDict([
                    ('account', String(kwargs["account"])),
                    ('vesting_shares', Amount(kwargs["vesting_shares"])),
                ]))


class TransferToSavings(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            if "memo" not in kwargs:
                kwargs["memo"] = ""
            super(TransferToSavings, self).__init__(
                OrderedDict([
                    ('from', String(kwargs["from"])),
                    ('to', String(kwargs["to"])),
                    ('amount', Amount(kwargs["amount"])),
                    ('memo', String(kwargs["memo"])),
                ]))


class TransferFromSavings(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            if "memo" not in kwargs:
                kwargs["memo"] = ""

            super(TransferFromSavings, self).__init__(
                OrderedDict([
                    ('from', String(kwargs["from"])),
                    ('request_id', Uint32(int(kwargs["request_id"]))),
                    ('to', String(kwargs["to"])),
                    ('amount', Amount(kwargs["amount"])),
                    ('memo', String(kwargs["memo"])),
                ]))


class CancelTransferFromSavings(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super(CancelTransferFromSavings, self).__init__(
                OrderedDict([
                    ('from', String(kwargs["from"])),
                    ('request_id', Uint32(int(kwargs["request_id"]))),
                ]))


class ClaimRewardBalance(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super(ClaimRewardBalance, self).__init__(
                OrderedDict([
                    ('account', String(kwargs["account"])),
                    ('reward_steem', Amount(kwargs["reward_steem"])),
                    ('reward_sbd', Amount(kwargs["reward_sbd"])),
                    ('reward_vests', Amount(kwargs["reward_vests"])),
                ]))


class DelegateVestingShares(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super(DelegateVestingShares, self).__init__(
                OrderedDict([
                    ('delegator', String(kwargs["delegator"])),
                    ('delegatee', String(kwargs["delegatee"])),
                    ('vesting_shares', Amount(kwargs["vesting_shares"])),
                ]))


class LimitOrderCreate(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super(LimitOrderCreate, self).__init__(
                OrderedDict([
                    ('owner', String(kwargs["owner"])),
                    ('orderid', Uint32(int(kwargs["orderid"]))),
                    ('amount_to_sell', Amount(kwargs["amount_to_sell"])),
                    ('min_to_receive', Amount(kwargs["min_to_receive"])),
                    ('fill_or_kill', Bool(kwargs["fill_or_kill"])),
                    ('expiration', PointInTime(kwargs["expiration"])),
                ]))


class LimitOrderCancel(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super(LimitOrderCancel, self).__init__(
                OrderedDict([
                    ('owner', String(kwargs["owner"])),
                    ('orderid', Uint32(int(kwargs["orderid"]))),
                ]))


class SetWithdrawVestingRoute(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super(SetWithdrawVestingRoute, self).__init__(
                OrderedDict([
                    ('from_account', String(kwargs["from_account"])),
                    ('to_account', String(kwargs["to_account"])),
                    ('percent', Uint16((kwargs["percent"]))),
                    ('auto_vest', Bool(kwargs["auto_vest"])),
                ]))


class Convert(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super(Convert, self).__init__(
                OrderedDict([
                    ('owner', String(kwargs["owner"])),
                    ('requestid', Uint32(kwargs["requestid"])),
                    ('amount', Amount(kwargs["amount"])),
                ]))


class FeedPublish(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super(FeedPublish, self).__init__(
                OrderedDict([
                    ('publisher', String(kwargs["publisher"])),
                    ('exchange_rate', ExchangeRate(kwargs["exchange_rate"])),
                ]))


class WitnessUpdate(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            prefix = kwargs.pop("prefix", default_prefix)

            if not kwargs["block_signing_key"]:
                kwargs[
                    "block_signing_key"] = \
                        "STM1111111111111111111111111111111114T1Anm"
            super(WitnessUpdate, self).__init__(
                OrderedDict([
                    ('owner', String(kwargs["owner"])),
                    ('url', String(kwargs["url"])),
                    ('block_signing_key',
                     PublicKey(kwargs["block_signing_key"], prefix=prefix)),
                    ('props', WitnessProps(kwargs["props"])),
                    ('fee', Amount(kwargs["fee"])),
                ]))


class AccountWitnessVote(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super(AccountWitnessVote, self).__init__(
                OrderedDict([
                    ('account', String(kwargs["account"])),
                    ('witness', String(kwargs["witness"])),
                    ('approve', Bool(bool(kwargs["approve"]))),
                ]))


class CustomJson(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            if "json" in kwargs and kwargs["json"]:
                if (isinstance(kwargs["json"], dict)
                        or isinstance(kwargs["json"], list)):
                    js = json.dumps(kwargs["json"])
                else:
                    js = kwargs["json"]

            if len(kwargs["id"]) > 32:
                raise Exception("'id' too long")

            super(CustomJson, self).__init__(
                OrderedDict([
                    ('required_auths',
                     Array([String(o) for o in kwargs["required_auths"]])),
                    ('required_posting_auths',
                     Array([
                         String(o) for o in kwargs["required_posting_auths"]
                     ])),
                    ('id', String(kwargs["id"])),
                    ('json', String(js)),
                ]))


class CommentOptions(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            # handle beneficiaries
            extensions = Array([])
            beneficiaries = kwargs.get('beneficiaries')
            if beneficiaries and type(beneficiaries) == list:
                ext_obj = [0, {'beneficiaries': beneficiaries}]
                ext = CommentOptionExtensions(ext_obj)
                extensions = Array([ext])

            super(CommentOptions, self).__init__(
                OrderedDict([
                    ('author', String(kwargs["author"])),
                    ('permlink', String(kwargs["permlink"])),
                    ('max_accepted_payout',
                     Amount(kwargs["max_accepted_payout"])),
                    ('percent_steem_dollars',
                     Uint16(int(kwargs["percent_steem_dollars"]))),
                    ('allow_votes', Bool(bool(kwargs["allow_votes"]))),
                    ('allow_curation_rewards',
                     Bool(bool(kwargs["allow_curation_rewards"]))),
                    ('extensions', extensions),
                ]))


def isArgsThisClass(self, args):
    return len(args) == 1 and type(args[0]).__name__ == type(self).__name__
