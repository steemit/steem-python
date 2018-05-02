import logging
import os

from .instance import shared_steemd_instance
from steembase import bip38
from steembase.account import PrivateKey
from steembase.exceptions import (InvalidWifError, WalletExists)

from .account import Account

log = logging.getLogger(__name__)


class Wallet:
    """ The wallet is meant to maintain access to private keys for
        your accounts. It either uses manually provided private keys
        or uses a SQLite database managed by storage.py.

        :param Steem rpc: RPC connection to a Steem node

        :param array,dict,string keys: Predefine the wif keys to shortcut
        the wallet database

        Three wallet operation modes are possible:

        * **Wallet Database**: Here, steemlibs loads the keys from the
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
    decryptedKEK = None

    # Keys from database
    configStorage = None
    keyEncryptionKey = None
    keyStorage = None

    # Manually provided keys
    keys = {}  # struct with pubkey as key and wif as value
    keyMap = {}  # type:wif pairs to force certain keys

    def __init__(self, steemd_instance=None, **kwargs):
        from steembase.storage import configStorage
        self.configStorage = configStorage

        # RPC
        self.steemd = steemd_instance or shared_steemd_instance()

        # Prefix
        if self.steemd:
            self.prefix = self.steemd.chain_params["prefix"]
        else:
            # If not connected, load prefix from config
            self.prefix = self.configStorage["prefix"]

        if "keys" in kwargs:
            self.setKeys(kwargs["keys"])
        else:
            """ If no keys are provided manually we load the SQLite
                keyStorage
            """
            from steembase.storage import (keyStorage, KeyEncryptionKey)
            self.keyEncryptionKey = KeyEncryptionKey
            self.keyStorage = keyStorage

    def setKeys(self, loadkeys):
        """ This method is strictly only for in memory keys that are
            passed to Wallet/Steem with the ``keys`` argument
        """
        log.debug(
            "Force setting of private keys. Not using the wallet database!")
        if isinstance(loadkeys, dict):
            Wallet.keyMap = loadkeys
            loadkeys = list(loadkeys.values())
        elif not isinstance(loadkeys, list):
            loadkeys = [loadkeys]

        for wif in loadkeys:
            try:
                key = PrivateKey(wif)
            except:  # noqa FIXME(sneak)
                raise InvalidWifError
            Wallet.keys[format(key.pubkey, self.prefix)] = str(key)

    def unlock(self, user_passphrase=None):
        """ Unlock the wallet database
        """
        if not self.created():
            self.newWallet()

        if (self.decryptedKEK is None
                and self.configStorage[self.keyEncryptionKey.config_key]):
            if user_passphrase is None:
                user_passphrase = self.getUserPassphrase()
            kek = self.keyEncryptionKey(user_passphrase)
            self.decryptedKEK = kek.decrypted_KEK

    def lock(self):
        """ Lock the wallet database
        """
        self.decryptedKEK = None

    def locked(self):
        """ Is the wallet database locked?
        """
        return False if self.decryptedKEK else True

    def changeUserPassphrase(self):
        """ Change the user entered password for the wallet database
        """
        # Open Existing Wallet
        pwd = self.getUserPassphrase()
        kek = self.keyEncryptionKey(pwd)
        self.decryptedKEK = kek.decrypted_KEK
        # Provide new passphrase
        print("Please provide the new passphrase")
        newpwd = self.getUserPassphrase(confirm=True)
        # Change passphrase
        kek.changePassphrase(newpwd)

    def created(self):
        """ Do we have a wallet database already?
        """
        if len(self.getPublicKeys()):
            # Already keys installed
            return True
        elif self.keyEncryptionKey.config_key in self.configStorage:
            # no keys but a KeyEncryptionKey
            return True
        else:
            return False

    def newWallet(self):
        """ Create a new wallet database
        """
        if self.created():
            raise WalletExists("You already have created a wallet!")
        print("Please provide a passphrase for the new wallet")
        pwd = self.getUserPassphrase(confirm=True)
        kek = self.keyEncryptionKey(pwd)
        self.decryptedKEK = kek.decrypted_KEK

    def encrypt_wif(self, wif):
        """ Encrypt a wif key
        """
        self.unlock()
        return format(
            bip38.encrypt(PrivateKey(wif), self.decryptedKEK), "encwif")

    def decrypt_wif(self, encwif):
        """ decrypt a wif key
        """
        try:
            # Try to decode as wif
            PrivateKey(encwif)
            return encwif
        except:  # noqa FIXME(sneak)
            pass
        self.unlock()
        return format(bip38.decrypt(encwif, self.decryptedKEK), "wif")

    def getUserPassphrase(self, confirm=False, text='Passphrase: '):
        """ Obtain a passphrase from the user
        """
        import getpass
        if "UNLOCK" in os.environ:
            # overwrite passphrase from environmental variable
            return os.environ.get("UNLOCK")
        if confirm:
            # Loop until both match
            while True:
                pw = self.getUserPassphrase(confirm=False)
                if not pw:
                    print("You cannot choose an empty password! " +
                          "If you want to automate the use of the library, " +
                          "please use the `UNLOCK` environmental variable!")
                    continue
                else:
                    pwck = self.getUserPassphrase(
                        confirm=False, text="Confirm Passphrase: ")
                    if pw == pwck:
                        return pw
                    else:
                        print("Given Passphrases do not match!")
        else:
            # return just one password
            return getpass.getpass(text)

    def addPrivateKey(self, wif):
        """ Add a private key to the wallet database
        """

        # it could be either graphenebase or pistonbase so we can't check
        # the type directly

        if isinstance(wif, PrivateKey) or isinstance(wif, PrivateKey):
            wif = str(wif)
        try:
            pub = format(PrivateKey(wif).pubkey, self.prefix)
        except:  # noqa FIXME(sneak)
            raise InvalidWifError(
                "Invalid Private Key Format. Please use WIF!")

        if self.keyStorage:
            # Test if wallet exists
            if not self.created():
                self.newWallet()
            self.keyStorage.add(self.encrypt_wif(wif), pub)

    def getPrivateKeyForPublicKey(self, pub):
        """ Obtain the private key for a given public key

            :param str pub: Public Key
        """
        if Wallet.keys:
            if pub in Wallet.keys:
                return Wallet.keys[pub]
            elif len(Wallet.keys) == 1:
                # If there is only one key in my overwrite-storage, then
                # use that one! Whether it will has sufficient
                # authorization is left to ensure by the developer
                return list(self.keys.values())[0]
        else:
            # Test if wallet exists
            if not self.created():
                self.newWallet()

            return self.decrypt_wif(
                self.keyStorage.getPrivateKeyForPublicKey(pub))

    def removePrivateKeyFromPublicKey(self, pub):
        """ Remove a key from the wallet database
        """
        if self.keyStorage:
            # Test if wallet exists
            if not self.created():
                self.newWallet()
            self.keyStorage.delete(pub)

    def removeAccount(self, account):
        """ Remove all keys associated with a given account
        """
        accounts = self.getAccounts()
        for a in accounts:
            if a["name"] == account:
                self.removePrivateKeyFromPublicKey(a["pubkey"])

    def getOwnerKeyForAccount(self, name):
        """ Obtain owner Private Key for an account from the wallet database
        """
        if "owner" in Wallet.keyMap:
            return Wallet.keyMap.get("owner")
        else:
            account = self.steemd.get_account(name)
            if not account:
                return
            for authority in account["owner"]["key_auths"]:
                key = self.getPrivateKeyForPublicKey(authority[0])
                if key:
                    return key
            return False

    def getPostingKeyForAccount(self, name):
        """ Obtain owner Posting Key for an account from the wallet database
        """
        if "posting" in Wallet.keyMap:
            return Wallet.keyMap.get("posting")
        else:
            account = self.steemd.get_account(name)
            if not account:
                return
            for authority in account["posting"]["key_auths"]:
                key = self.getPrivateKeyForPublicKey(authority[0])
                if key:
                    return key
            return False

    def getMemoKeyForAccount(self, name):
        """ Obtain owner Memo Key for an account from the wallet database
        """
        if "memo" in Wallet.keyMap:
            return Wallet.keyMap.get("memo")
        else:
            account = self.steemd.get_account(name)
            if not account:
                return
            key = self.getPrivateKeyForPublicKey(account["memo_key"])
            if key:
                return key
            return False

    def getActiveKeyForAccount(self, name):
        """ Obtain owner Active Key for an account from the wallet database
        """
        if "active" in Wallet.keyMap:
            return Wallet.keyMap.get("active")
        else:
            account = self.steemd.get_account(name)
            if not account:
                return
            for authority in account["active"]["key_auths"]:
                key = self.getPrivateKeyForPublicKey(authority[0])
                if key:
                    return key
            return False

    def getAccountFromPrivateKey(self, wif):
        """ Obtain account name from private key
        """
        pub = format(PrivateKey(wif).pubkey, self.prefix)
        return self.getAccountFromPublicKey(pub)

    def getAccountFromPublicKey(self, pub):
        """ Obtain account name from public key
        """
        # FIXME, this only returns the first associated key.
        # If the key is used by multiple accounts, this
        # will surely lead to undesired behavior
        names = self.steemd.call(
            'get_key_references', [pub], api="account_by_key_api")[0]
        if not names:
            return None
        else:
            return names[0]

    def getAccount(self, pub):
        """ Get the account data for a public key
        """
        name = self.getAccountFromPublicKey(pub)
        if not name:
            return {"name": None, "type": None, "pubkey": pub}
        else:
            try:
                account = Account(name)
            except:  # noqa FIXME(sneak)
                return
            keyType = self.getKeyType(account, pub)
            return {
                "name": name,
                "account": account,
                "type": keyType,
                "pubkey": pub
            }

    def getKeyType(self, account, pub):
        """ Get key type
        """
        for authority in ["owner", "posting", "active"]:
            for key in account[authority]["key_auths"]:
                if pub == key[0]:
                    return authority
        if pub == account["memo_key"]:
            return "memo"
        return None

    def getAccounts(self):
        """ Return all accounts installed in the wallet database
        """
        pubkeys = self.getPublicKeys()
        accounts = []
        for pubkey in pubkeys:
            # Filter those keys not for our network
            if pubkey[:len(self.prefix)] == self.prefix:
                accounts.append(self.getAccount(pubkey))
        return accounts

    def getAccountsWithPermissions(self):
        """ Return a dictionary for all installed accounts with their
            corresponding installed permissions
        """
        accounts = [self.getAccount(a) for a in self.getPublicKeys()]
        r = {}
        for account in accounts:
            name = account["name"]
            if not name:
                continue
            type = account["type"]
            if name not in r:
                r[name] = {
                    "posting": False,
                    "owner": False,
                    "active": False,
                    "memo": False
                }
            r[name][type] = True
        return r

    def getPublicKeys(self):
        """ Return all installed public keys
        """
        if self.keyStorage:
            return self.keyStorage.getPublicKeys()
        else:
            return list(Wallet.keys.keys())
