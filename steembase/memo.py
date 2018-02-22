import hashlib
import json
import struct
import sys
from binascii import hexlify, unhexlify
from collections import OrderedDict

from Crypto.Cipher import AES

from .operations import Memo
from .base58 import base58encode, base58decode
from .account import PrivateKey, PublicKey
from steem.utils import future_bytes

default_prefix = "STM"


def get_shared_secret(priv, pub):
    """ Derive the share secret between ``priv`` and ``pub``

        :param `Base58` priv: Private Key
        :param `Base58` pub: Public Key
        :return: Shared secret
        :rtype: hex

        The shared secret is generated such that::

            Pub(Alice) * Priv(Bob) = Pub(Bob) * Priv(Alice)

    """
    pub_point = pub.point()
    priv_point = int(repr(priv), 16)
    res = pub_point * priv_point
    res_hex = '%032x' % res.x()
    # Zero padding
    res_hex = '0' * (64 - len(res_hex)) + res_hex
    return hashlib.sha512(unhexlify(res_hex)).hexdigest()


def init_aes(shared_secret, nonce):
    """ Initialize AES instance

        :param hex shared_secret: Shared Secret to use as encryption key
        :param int nonce: Random nonce
        :return: AES instance and checksum of the encryption key
        :rtype: length 2 tuple

    """
    " Seed "
    ss = unhexlify(shared_secret)
    n = struct.pack("<Q", int(nonce))
    encryption_key = hashlib.sha512(n + ss).hexdigest()
    " Check'sum' "
    check = hashlib.sha256(unhexlify(encryption_key)).digest()
    check = struct.unpack_from("<I", check[:4])[0]
    " AES "
    key = unhexlify(encryption_key[0:64])
    iv = unhexlify(encryption_key[64:96])
    return AES.new(key, AES.MODE_CBC, iv), check


def _pad(s, BS):
    numBytes = (BS - len(s) % BS)
    return s + numBytes * struct.pack('B', numBytes)


def _unpad(s, BS):
    count = int(struct.unpack('B', future_bytes(s[-1], 'ascii'))[0])
    if future_bytes(s[-count::], 'ascii') == count * struct.pack('B', count):
        return s[:-count]
    return s


def encode_memo(priv, pub, nonce, message, **kwargs):
    """ Encode a message with a shared secret between Alice and Bob

        :param PrivateKey priv: Private Key (of Alice)
        :param PublicKey pub: Public Key (of Bob)
        :param int nonce: Random nonce
        :param str message: Memo message
        :return: Encrypted message
        :rtype: hex

    """
    from steembase import transactions
    shared_secret = get_shared_secret(priv, pub)
    aes, check = init_aes(shared_secret, nonce)
    raw = future_bytes(message, 'utf8')

    " Padding "
    BS = 16
    if len(raw) % BS:
        raw = _pad(raw, BS)
    " Encryption "
    cipher = hexlify(aes.encrypt(raw)).decode('ascii')
    prefix = kwargs.pop("prefix", default_prefix)
    s = OrderedDict([
        ("from", format(priv.pubkey, prefix)),
        ("to", format(pub, prefix)),
        ("nonce", nonce),
        ("check", check),
        ("encrypted", cipher),
        ("from_priv", repr(priv)),
        ("to_pub", repr(pub)),
        ("shared_secret", shared_secret),
    ])
    tx = Memo(**s)

    return "#" + base58encode(hexlify(future_bytes(tx)).decode("ascii"))


def decode_memo(priv, message):
    """ Decode a message with a shared secret between Alice and Bob

        :param PrivateKey priv: Private Key (of Bob)
        :param base58encoded message: Encrypted Memo message
        :return: Decrypted message
        :rtype: str
        :raise ValueError: if message cannot be decoded as valid UTF-8
               string

    """
    " decode structure "
    raw = base58decode(message[1:])
    from_key = PublicKey(raw[:66])
    raw = raw[66:]
    to_key = PublicKey(raw[:66])
    raw = raw[66:]
    nonce = str(struct.unpack_from("<Q", unhexlify(raw[:16]))[0])
    raw = raw[16:]
    check = struct.unpack_from("<I", unhexlify(raw[:8]))[0]
    raw = raw[8:]
    cipher = raw

    if repr(to_key) == repr(priv.pubkey):
        shared_secret = get_shared_secret(priv, from_key)
    elif repr(from_key) == repr(priv.pubkey):
        shared_secret = get_shared_secret(priv, to_key)
    else:
        raise ValueError("Incorrect PrivateKey")

    " Init encryption "
    aes, checksum = init_aes(shared_secret, nonce)

    " Check "
    assert check == checksum, "Checksum failure"

    " Encryption "
    # remove the varint prefix (FIXME, long messages!)
    message = cipher[2:]
    message = aes.decrypt(unhexlify(future_bytes(message, 'ascii')))
    try:
        return _unpad(message.decode('utf8'), 16)
    except:  # noqa FIXME(sneak)
        raise ValueError(message)


def involved_keys(message):
    " decode structure "
    raw = base58decode(message[1:])
    from_key = PublicKey(raw[:66])
    raw = raw[66:]
    to_key = PublicKey(raw[:66])

    return [from_key, to_key]
