import hashlib
import logging
import struct
import time
import array
import sys
from binascii import hexlify, unhexlify
from collections import OrderedDict
from datetime import datetime

import ecdsa

from steem.utils import future_bytes, to_chr
from .account import PrivateKey, PublicKey
from .chains import known_chains
from .operations import Operation, GrapheneObject, isArgsThisClass
from .types import (
    Array,
    Set,
    Signature,
    PointInTime,
    Uint16,
    Uint32,
)

log = logging.getLogger(__name__)

try:
    import secp256k1

    USE_SECP256K1 = True
    log.debug("Loaded secp256k1 binding.")
except:  # noqa FIXME(sneak)
    USE_SECP256K1 = False
    log.debug("To speed up transactions signing install \n"
              "    pip install secp256k1")


class SignedTransaction(GrapheneObject):
    """ Create a signed transaction and offer method to create the
        signature

        :param num refNum: parameter ref_block_num (see ``getBlockParams``)
        :param num refPrefix: parameter ref_block_prefix (see
        ``getBlockParams``)
        :param str expiration: expiration date
        :param Array operations:  array of operations
    """

    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            if "extensions" not in kwargs:
                kwargs["extensions"] = Set([])
            elif not kwargs.get("extensions"):
                kwargs["extensions"] = Set([])
            if "signatures" not in kwargs:
                kwargs["signatures"] = Array([])
            else:
                kwargs["signatures"] = Array(
                    [Signature(unhexlify(a)) for a in kwargs["signatures"]])

            if "operations" in kwargs:
                if all([
                    not isinstance(a, Operation)
                    for a in kwargs["operations"]
                ]):
                    kwargs['operations'] = Array(
                        [Operation(a) for a in kwargs["operations"]])
                else:
                    kwargs['operations'] = Array(kwargs["operations"])

            super(SignedTransaction, self).__init__(
                OrderedDict([
                    ('ref_block_num', Uint16(kwargs['ref_block_num'])),
                    ('ref_block_prefix', Uint32(kwargs['ref_block_prefix'])),
                    ('expiration', PointInTime(kwargs['expiration'])),
                    ('operations', kwargs['operations']),
                    ('extensions', kwargs['extensions']),
                    ('signatures', kwargs['signatures']),
                ]))

    def recoverPubkeyParameter(self, digest, signature, pubkey):
        """ Use to derive a number that allows to easily recover the
            public key from the signature
        """
        for i in range(0, 4):
            if USE_SECP256K1:
                sig = pubkey.ecdsa_recoverable_deserialize(signature, i)
                p = secp256k1.PublicKey(
                    pubkey.ecdsa_recover(self.message, sig))
                if p.serialize() == pubkey.serialize():
                    return i
            else:
                p = self.recover_public_key(digest, signature, i)
                if (p.to_string() == pubkey.to_string()
                        or self.compressedPubkey(p) == pubkey.to_string()):
                    return i
        return None

    def derSigToHexSig(self, s):
        """ Format DER to HEX signature
        """
        s, junk = ecdsa.der.remove_sequence(unhexlify(s))
        if junk:
            log.debug('JUNK: %s', hexlify(junk).decode('ascii'))
        assert (junk == b'')
        x, s = ecdsa.der.remove_integer(s)
        y, s = ecdsa.der.remove_integer(s)
        return '%064x%064x' % (x, y)

    def compressedPubkey(self, pk):
        order = pk.curve.generator.order()
        p = pk.pubkey.point
        x_str = ecdsa.util.number_to_string(p.x(), order)
        return future_bytes(to_chr(2 + (p.y() & 1)), 'ascii') + x_str

    # FIXME(sneak) this should be reviewed for correctness
    def recover_public_key(self, digest, signature, i):
        """ Recover the public key from the the signature
        """
        # See http: //www.secg.org/download/aid-780/sec1-v2.pdf
        # section 4.1.6 primarily
        curve = ecdsa.SECP256k1.curve
        G = ecdsa.SECP256k1.generator
        order = ecdsa.SECP256k1.order
        yp = (i % 2)
        r, s = ecdsa.util.sigdecode_string(signature, order)
        # 1.1
        x = r + (i // 2) * order
        # 1.3. This actually calculates for either effectively
        # 02||X or 03||X depending on 'k' instead of always
        # for 02||X as specified.
        # This substitutes for the lack of reversing R later on.
        # -R actually is defined to be just flipping the y-coordinate
        # in the elliptic curve.
        alpha = ((x * x * x) + (curve.a() * x) + curve.b()) % curve.p()
        beta = ecdsa.numbertheory.square_root_mod_prime(alpha, curve.p())
        y = beta if (beta - yp) % 2 == 0 else curve.p() - beta
        # 1.4 Constructor of Point is supposed to check if nR is at infinity.
        R = ecdsa.ellipticcurve.Point(curve, x, y, order)
        # 1.5 Compute e
        e = ecdsa.util.string_to_number(digest)
        # 1.6 Compute Q = r^-1(sR - eG)
        Q = ecdsa.numbertheory.inverse_mod(r, order) * (s * R +
                                                        (-e % order) * G)
        # Not strictly necessary, but let's verify the message for
        # paranoia's sake.
        if not ecdsa.VerifyingKey.from_public_point(
                Q, curve=ecdsa.SECP256k1).verify_digest(
            signature, digest, sigdecode=ecdsa.util.sigdecode_string):
            return None
        return ecdsa.VerifyingKey.from_public_point(Q, curve=ecdsa.SECP256k1)

    def getKnownChains(self):
        return known_chains

    def getChainParams(self, chain):
        # Which network are we on:
        chains = self.getKnownChains()
        if isinstance(chain, str) and chain in chains:
            chain_params = chains[chain]
        elif isinstance(chain, dict):
            chain_params = chain
        else:
            raise Exception("sign() only takes a string or a dict as chain!")
        if "chain_id" not in chain_params:
            raise Exception("sign() needs a 'chain_id' in chain params!")
        return chain_params

    def deriveDigest(self, chain):
        chain_params = self.getChainParams(chain)
        # Chain ID
        self.chainid = chain_params["chain_id"]

        # Do not serialize signatures
        sigs = self.data["signatures"]
        self.data["signatures"] = []

        # Get message to sign
        #   bytes(self) will give the wire formatted data according to
        #   GrapheneObject and the data given in __init__()
        self.message = unhexlify(self.chainid) + future_bytes(self)
        self.digest = hashlib.sha256(self.message).digest()

        # restore signatures
        self.data["signatures"] = sigs

    def verify(self, pubkeys=[], chain=None):
        if not chain:
            raise ValueError("Chain needs to be provided!")
        chain_params = self.getChainParams(chain)
        self.deriveDigest(chain)
        signatures = self.data["signatures"].data
        pubKeysFound = []

        for signature in signatures:
            sig = future_bytes(signature)[1:]
            if sys.version >= '3.0':
                recoverParameter = (future_bytes(signature)[0]) - 4 - 27  # recover parameter only
            else:
                recoverParameter = ord((future_bytes(signature)[0])) - 4 - 27

            if USE_SECP256K1:
                ALL_FLAGS = secp256k1.lib.SECP256K1_CONTEXT_VERIFY | \
                            secp256k1.lib.SECP256K1_CONTEXT_SIGN
                # Placeholder
                pub = secp256k1.PublicKey(flags=ALL_FLAGS)
                # Recover raw signature
                sig = pub.ecdsa_recoverable_deserialize(sig, recoverParameter)
                # Recover PublicKey
                verifyPub = secp256k1.PublicKey(
                    pub.ecdsa_recover(future_bytes(self.message), sig))
                # Convert recoverable sig to normal sig
                normalSig = verifyPub.ecdsa_recoverable_convert(sig)
                # Verify
                verifyPub.ecdsa_verify(future_bytes(self.message), normalSig)
                phex = hexlify(
                    verifyPub.serialize(compressed=True)).decode('ascii')
                pubKeysFound.append(phex)
            else:
                p = self.recover_public_key(self.digest, sig, recoverParameter)
                # Will throw an exception of not valid
                p.verify_digest(
                    sig, self.digest, sigdecode=ecdsa.util.sigdecode_string)
                phex = hexlify(self.compressedPubkey(p)).decode('ascii')
                pubKeysFound.append(phex)

        for pubkey in pubkeys:
            if not isinstance(pubkey, PublicKey):
                raise Exception("Pubkeys must be array of 'PublicKey'")

            k = pubkey.unCompressed()[2:]
            if k not in pubKeysFound and repr(pubkey) not in pubKeysFound:
                k = PublicKey(PublicKey(k).compressed())
                f = format(k, chain_params["prefix"])
                raise Exception("Signature for %s missing!" % f)
        return pubKeysFound

    def _is_canonical(self, sig):
        return (not (sig[0] & 0x80)
                and not (sig[0] == 0 and not (sig[1] & 0x80))
                and not (sig[32] & 0x80)
                and not (sig[32] == 0 and not (sig[33] & 0x80)))

    # FIXME(sneak) audit this function
    def sign(self, wifkeys, chain=None):
        """ Sign the transaction with the provided private keys.

            :param list wifkeys: Array of wif keys
            :param str chain: identifier for the chain

        """
        if not chain:
            raise ValueError("Chain needs to be provided!")
        self.deriveDigest(chain)

        # Get Unique private keys
        self.privkeys = []
        [
            self.privkeys.append(item) for item in wifkeys
            if item not in self.privkeys
        ]

        # Sign the message with every private key given!
        sigs = []
        for wif in self.privkeys:
            p = future_bytes(PrivateKey(wif))
            i = 0
            if USE_SECP256K1:
                ndata = secp256k1.ffi.new("const int *ndata")
                ndata[0] = 0
                while True:
                    ndata[0] += 1
                    privkey = secp256k1.PrivateKey(p, raw=True)
                    sig = secp256k1.ffi.new(
                        'secp256k1_ecdsa_recoverable_signature *')
                    signed = secp256k1.lib.secp256k1_ecdsa_sign_recoverable(
                        privkey.ctx, sig, self.digest, privkey.private_key,
                        secp256k1.ffi.NULL, ndata)
                    assert signed == 1
                    signature, i = privkey.ecdsa_recoverable_serialize(sig)
                    if self._is_canonical(signature):
                        i += 4  # compressed
                        i += 27  # compact
                        break
            else:
                cnt = 0
                sk = ecdsa.SigningKey.from_string(p, curve=ecdsa.SECP256k1)
                while 1:
                    cnt += 1
                    if not cnt % 20:
                        log.info("Still searching for a canonical signature. "
                                 "Tried %d times already!" % cnt)

                    # Deterministic k
                    k = ecdsa.rfc6979.generate_k(
                        sk.curve.generator.order(),
                        sk.privkey.secret_multiplier,
                        hashlib.sha256,
                        hashlib.sha256(
                            self.digest + struct.pack("d", time.time(
                            ))  # use the local time to randomize the signature
                        ).digest())

                    # Sign message
                    #
                    sigder = sk.sign_digest(
                        self.digest, sigencode=ecdsa.util.sigencode_der, k=k)

                    # Reformating of signature
                    #
                    r, s = ecdsa.util.sigdecode_der(sigder,
                                                    sk.curve.generator.order())
                    signature = ecdsa.util.sigencode_string(
                        r, s, sk.curve.generator.order())

                    # Make sure signature is canonical!
                    #
                    sigder = array.array('B', sigder)
                    lenR = sigder[3]
                    lenS = sigder[5 + lenR]
                    if lenR is 32 and lenS is 32:
                        # Derive the recovery parameter
                        #
                        i = self.recoverPubkeyParameter(
                            self.digest, signature, sk.get_verifying_key())
                        i += 4  # compressed
                        i += 27  # compact
                        break

            # pack signature
            #
            sigstr = struct.pack("<B", i)
            sigstr += signature

            sigs.append(Signature(sigstr))

        self.data["signatures"] = Array(sigs)
        return self


time_format = '%Y-%m-%dT%H:%M:%S%Z'


def get_block_params(steem):
    """ Auxiliary method to obtain ``ref_block_num`` and
        ``ref_block_prefix``. Requires a websocket connection to a
        witness node!
    """
    props = steem.get_dynamic_global_properties()
    ref_block_num = props["head_block_number"] - 3 & 0xFFFF
    ref_block = steem.get_block(props["head_block_number"] - 2)
    ref_block_prefix = struct.unpack_from("<I", unhexlify(
        ref_block["previous"]), 4)[0]
    return ref_block_num, ref_block_prefix


def fmt_time_from_now(secs=0):
    """ Properly Format Time that is `x` seconds in the future

     :param int secs: Seconds to go in the future (`x>0`) or the past (`x<0`)
     :return: Properly formated time for Graphene (`%Y-%m-%dT%H:%M:%S`)
     :rtype: str

    """
    return datetime.utcfromtimestamp(time.time() + int(secs)).strftime(
        time_format)
