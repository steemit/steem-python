import json
import struct
import time
from binascii import hexlify, unhexlify
from calendar import timegm
from steem.utils import future_bytes

object_type = {
    "dynamic_global_property": 0,
    "reserved0": 1,
    "account": 2,
    "witness": 3,
    "transaction": 4,
    "block_summary": 5,
    "chain_property": 6,
    "witness_schedule": 7,
    "comment": 8,
    "category": 9,
    "comment_vote": 10,
    "vote": 11,
    "witness_vote": 12,
    "limit_order": 13,
    "feed_history": 14,
    "convert_request": 15,
    "liquidity_reward_balance": 16,
    "operation": 17,
    "account_history": 18,
}

timeformat = '%Y-%m-%dT%H:%M:%S%Z'


def varint(n):
    """ Varint encoding
    """
    data = b''
    while n >= 0x80:
        data += bytes([(n & 0x7f) | 0x80])
        n >>= 7
    data += bytes([n])
    return data


def varintdecode(data):
    """ Varint decoding
    """
    shift = 0
    result = 0
    for c in data:
        b = ord(c)
        result |= ((b & 0x7f) << shift)
        if not (b & 0x80):
            break
        shift += 7
    return result


def variable_buffer(s):
    """ Encode variable length buffer
    """
    return varint(len(s)) + s


def JsonObj(data):
    """ Returns json object from data
    """
    try:
        return json.loads(str(data))
    except:  # noqa FIXME(sneak)
        try:
            return data.__str__()
        except:  # noqa FIXME(sneak)
            raise ValueError('JsonObj could not parse %s:\n%s' %
                             (type(data).__name__, data.__class__))


class Uint8:
    def __init__(self, d):
        self.data = d

    def to_bytes(self):
        return struct.pack("<B", self.data)

    def __str__(self):
        return '%d' % self.data


class Int16:
    def __init__(self, d):
        self.data = int(d)

    def to_bytes(self):
        return struct.pack("<h", int(self.data))

    def __str__(self):
        return '%d' % self.data


class Uint16:
    def __init__(self, d):
        self.data = int(d)

    def to_bytes(self):
        return struct.pack("<H", self.data)

    def __str__(self):
        return '%d' % self.data


class Uint32:
    def __init__(self, d):
        self.data = int(d)

    def to_bytes(self):
        return struct.pack("<I", self.data)

    def __str__(self):
        return '%d' % self.data


class Uint64:
    def __init__(self, d):
        self.data = int(d)

    def to_bytes(self):
        return struct.pack("<Q", self.data)

    def __str__(self):
        return '%d' % self.data


class Varint32:
    def __init__(self, d):
        self.data = d

    def to_bytes(self):
        return varint(self.data)

    def __str__(self):
        return '%d' % self.data


class Int64:
    def __init__(self, d):
        self.data = d

    def to_bytes(self):
        return struct.pack("<q", self.data)

    def __str__(self):
        return '%d' % self.data


class String:
    def __init__(self, d):
        self.data = d

    def to_bytes(self):
        d = self.unicodify()
        return varint(len(d)) + d

    def __str__(self):
        return '%s' % str(self.data)

    def unicodify(self):
        r = []
        for s in self.data:
            o = ord(s)
            if o <= 7:
                r.append("u%04x" % o)
            elif o == 8:
                r.append("b")
            elif o == 9:
                r.append("\t")
            elif o == 10:
                r.append("\n")
            elif o == 11:
                r.append("u%04x" % o)
            elif o == 12:
                r.append("f")
            elif o == 13:
                r.append("\r")
            elif 13 < o < 32:
                r.append("u%04x" % o)
            else:
                r.append(s)
        return bytes("".join(r), "utf-8")


class Bytes:
    def __init__(self, d, length=None):
        self.data = d
        if length:
            self.length = length
        else:
            self.length = len(self.data)

    def to_bytes(self):
        # FIXME constraint data to self.length
        d = unhexlify(bytes(self.data, 'utf-8'))
        return varint(len(d)) + d

    def __str__(self):
        return str(self.data)


class Void:
    def __init__(self):
        pass

    def to_bytes(self):
        return b''

    def __str__(self):
        return ""


class Array:
    def __init__(self, d):
        self.data = d
        self.length = Varint32(len(self.data))

    def to_bytes(self):
        return bytes(self.length) + b"".join([bytes(a) for a in self.data])

    def __str__(self):
        r = []
        for a in self.data:
            if isinstance(a, ObjectId):
                r.append(str(a))
            elif isinstance(a, VoteId):
                r.append(str(a))
            elif isinstance(a, String):
                r.append(str(a))
            else:
                r.append(JsonObj(a))
        return json.dumps(r)


class PointInTime:
    def __init__(self, d):
        self.data = d

    def to_bytes(self):
        return struct.pack("<I",
                           timegm(
                               time.strptime((self.data + "UTC"), timeformat)))

    def __str__(self):
        return self.data


class Signature:
    def __init__(self, d):
        self.data = d

    def to_bytes(self):
        return self.data

    def __str__(self):
        return json.dumps(hexlify(self.data).decode('ascii'))


class Bool(Uint8):  # Bool = Uint8
    def __init__(self, d):
        Uint8.__init__(self, d)

    def __str__(self):
        return True if self.data else False


class Set(Array):  # Set = Array
    def __init__(self, d):
        Array.__init__(self, d)


class FixedArray:
    def __init__(self, d):
        raise NotImplementedError

    def to_bytes(self):
        raise NotImplementedError

    def __str__(self):
        raise NotImplementedError


class Optional:
    def __init__(self, d):
        self.data = d

    def to_bytes(self):
        if not self.data:
            return bytes(Bool(0))
        else:
            return bytes(Bool(1)) + bytes(self.data) if bytes(
                self.data) else bytes(Bool(0))

    def __str__(self):
        return str(self.data)

    def isempty(self):
        if not self.data:
            return True
        return not bool(future_bytes(self.data))


class StaticVariant:
    def __init__(self, d, type_id):
        self.data = d
        self.type_id = type_id

    def to_bytes(self):
        return varint(self.type_id) + bytes(self.data)

    def __str__(self):
        return json.dumps([self.type_id, self.data.json()])


class Map:
    def __init__(self, data):
        self.data = data

    def to_bytes(self):
        b = b""
        b += varint(len(self.data))
        for e in self.data:
            b += bytes(e[0]) + bytes(e[1])
        return b

    def __str__(self):
        r = []
        for e in self.data:
            r.append([str(e[0]), str(e[1])])
        return json.dumps(r)


class Id:
    def __init__(self, d):
        self.data = Varint32(d)

    def to_bytes(self):
        return bytes(self.data)

    def __str__(self):
        return str(self.data)


class VoteId:
    def __init__(self, vote):
        parts = vote.split(":")
        assert len(parts) == 2
        self.type = int(parts[0])
        self.instance = int(parts[1])

    def to_bytes(self):
        binary = (self.type & 0xff) | (self.instance << 8)
        return struct.pack("<I", binary)

    def __str__(self):
        return "%d:%d" % (self.type, self.instance)


class ObjectId:
    """ Encodes object/protocol ids
    """

    def __init__(self, object_str, type_verify=None):
        if len(object_str.split(".")) == 3:
            space, type, id = object_str.split(".")
            self.space = int(space)
            self.type = int(type)
            self.instance = Id(int(id))
            self.Id = object_str
            if type_verify:
                assert object_type[type_verify] == int(type), \
                    "Object id does not match object type! " + \
                    "Excpected %d, got %d" % \
                    (object_type[type_verify], int(type))
        else:
            raise Exception("Object id is invalid")

    def to_bytes(self):
        return bytes(self.instance)  # only yield instance

    def __str__(self):
        return self.Id
