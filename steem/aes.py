import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers import algorithms
from cryptography.hazmat.primitives.ciphers import modes
from cryptography.hazmat.backends import default_backend

class AESCipher(object):
    """

    A classical AES Cipher. Can use any size of data and any size of
    password thanks to padding.  Also ensure the coherence and the type of
    the data with a unicode to byte converter.

    """

    def __init__(self, key):
        self.bs = 32
        self.key = hashlib.sha256(AESCipher.str_to_bytes(key)).digest()

    @staticmethod
    def str_to_bytes(data):
        u_type = type(b''.decode('utf8'))
        if isinstance(data, u_type):
            return data.encode('utf8')
        return data

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * AESCipher.str_to_bytes(
            chr(self.bs - len(s) % self.bs))

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s) - 1:])]

    def encrypt(self, raw):
        raw = self._pad(AESCipher.str_to_bytes(raw))
        iv = os.urandom(self.bs)
        backend = default_backend()
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=backend)
        encryptor = cipher.encryptor()
        cipher_text = encryptor.update(raw) + encryptor.finalize()
        return base64.b64encode(iv + cipher_text).decode('utf-8')

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:algorithms.AES.block_size]
        backend = default_backend()
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv),
                        backend=backend)
        decryptor = cipher.decryptor()
        plain_text = decryptor.update(enc) + decryptor.finalize()
        return self._unpad(plain_text ).decode('utf-8')
