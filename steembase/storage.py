import hashlib
import logging
import os
import shutil
import sqlite3
import time
from binascii import hexlify
from datetime import datetime

from appdirs import user_data_dir

from steem.aes import AESCipher
from steem.utils import compat_bytes

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

timeformat = "%Y%m%d-%H%M%S"


class DataDir(object):
    """ This class ensures that the user's data is stored in its OS
        preotected user directory:

         Furthermore, it offers an interface to generated backups
         in the `backups/` directory every now and then.
    """

    appname = "steem"
    appauthor = "Steemit Inc"
    storageDatabase = "steem.sqlite"

    data_dir = user_data_dir(appname, appauthor)
    sqlDataBaseFile = os.path.join(data_dir, storageDatabase)

    def __init__(self):
        #: Storage
        self.mkdir_p()

    def mkdir_p(self):
        """ Ensure that the directory in which the data is stored
            exists
        """
        if os.path.isdir(self.data_dir):
            return
        else:
            try:
                os.makedirs(self.data_dir)
            except FileExistsError:
                return
            except OSError:
                raise

    def sqlite3_backup(self, dbfile, backupdir):
        """ Create timestamped database copy
        """
        if not os.path.isdir(backupdir):
            os.mkdir(backupdir)
        backup_file = os.path.join(backupdir,
                                   os.path.basename(self.storageDatabase) +
                                   datetime.now().strftime("-" + timeformat))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        # Lock database before making a backup
        cursor.execute('BEGIN IMMEDIATE')
        # Make new backup file
        shutil.copyfile(dbfile, backup_file)
        log.info("Creating {}...".format(backup_file))
        # Unlock database
        connection.rollback()
        configStorage["lastBackup"] = datetime.now().strftime(timeformat)

    def clean_data(self):
        """ Delete files older than 70 days
        """
        log.info("Cleaning up old backups")
        for filename in os.listdir(self.data_dir):
            backup_file = os.path.join(self.data_dir, filename)
            if os.stat(backup_file).st_ctime < (time.time() - 70 * 86400):
                if os.path.isfile(backup_file):
                    os.remove(backup_file)
                    log.info("Deleting {}...".format(backup_file))

    def refreshBackup(self):
        """ Make a new backup
        """
        backupdir = os.path.join(self.data_dir, "backups")
        self.sqlite3_backup(self.sqlDataBaseFile, backupdir)
        self.clean_data()


class Key(DataDir):
    __tablename__ = 'keys'

    def __init__(self):
        """ This is the key storage that stores the public key and the
            (possibly encrypted) private key in the `keys` table in the
            SQLite3 database.
        """
        super(Key, self).__init__()

    def exists_table(self):
        """ Check if the database table exists
        """
        query = ("SELECT name FROM sqlite_master " +
                 "WHERE type='table' AND name=?", (self.__tablename__,))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        return True if cursor.fetchone() else False

    def create_table(self):
        """ Create the new table in the SQLite database
        """
        query = ('CREATE TABLE %s (' % self.__tablename__ +
                 'id INTEGER PRIMARY KEY AUTOINCREMENT,' + 'pub STRING(256),' +
                 'wif STRING(256)' + ')')
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()

    def getPublicKeys(self):
        """ Returns the public keys stored in the database
        """
        query = ("SELECT pub from %s " % (self.__tablename__))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        return [x[0] for x in results]

    def getPrivateKeyForPublicKey(self, pub):
        """ Returns the (possibly encrypted) private key that
            corresponds to a public key

           :param str pub: Public key

           The encryption scheme is BIP38
        """
        query = ("SELECT wif from %s " % (self.__tablename__) + "WHERE pub=?",
                 (pub,))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        key = cursor.fetchone()
        if key:
            return key[0]
        else:
            return None

    def updateWif(self, pub, wif):
        """ Change the wif to a pubkey

           :param str pub: Public key
           :param str wif: Private key
        """
        query = ("UPDATE %s " % self.__tablename__ + "SET wif=? WHERE pub=?",
                 (wif, pub))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        connection.commit()

    def add(self, wif, pub):
        """ Add a new public/private key pair (correspondence has to be
            checked elsewhere!)

           :param str pub: Public key
           :param str wif: Private key
        """
        if self.getPrivateKeyForPublicKey(pub):
            raise ValueError("Key already in storage")
        query = ('INSERT INTO %s (pub, wif) ' % self.__tablename__ +
                 'VALUES (?, ?)', (pub, wif))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        connection.commit()

    def delete(self, pub):
        """ Delete the key identified as `pub`

           :param str pub: Public key
        """
        query = ("DELETE FROM %s " % (self.__tablename__) + "WHERE pub=?",
                 (pub,))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        connection.commit()


class Configuration(DataDir):
    __tablename__ = "config"

    #: Default configuration
    config_defaults = {
        "categories_sorting": "trending",
        "default_vote_weight": 100.0,
        "format": "markdown",
        "limit": 10,
        "list_sorting": "trending",
        "post_category": "steem",
        "prefix": "STM"
    }

    def __init__(self):
        """ This is the configuration storage that stores key/value
            pairs in the `config` table of the SQLite3 database.
        """
        super(Configuration, self).__init__()

    def exists_table(self):
        """ Check if the database table exists
        """
        query = ("SELECT name FROM sqlite_master " +
                 "WHERE type='table' AND name=?", (self.__tablename__,))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        return True if cursor.fetchone() else False

    def create_table(self):
        """ Create the new table in the SQLite database
        """
        query = ('CREATE TABLE %s (' % self.__tablename__ +
                 'id INTEGER PRIMARY KEY AUTOINCREMENT,' + 'key STRING(256),' +
                 'value STRING(256)' + ')')
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()

    def checkBackup(self):
        """ Backup the SQL database every 7 days
        """
        if ("lastBackup" not in configStorage
                or configStorage["lastBackup"] == ""):
            print("No backup has been created yet!")
            self.refreshBackup()
        try:
            if (datetime.now() - datetime.strptime(configStorage["lastBackup"],
                                                   timeformat)).days > 7:
                print("Backups older than 7 days!")
                self.refreshBackup()
        except:  # noqa FIXME(sneak)
            self.refreshBackup()

    def _haveKey(self, key):
        """ Is the key `key` available int he configuration?
        """
        query = ("SELECT value FROM %s " %
                 (self.__tablename__) + "WHERE key=?", (key,))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        return True if cursor.fetchone() else False

    def __getitem__(self, key):
        """ This method behaves differently from regular `dict` in that
            it returns `None` if a key is not found!
        """
        query = ("SELECT value FROM %s " %
                 (self.__tablename__) + "WHERE key=?", (key,))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            if key in self.config_defaults:
                return self.config_defaults[key]
            else:
                return None

    def get(self, key, default=None):
        """ Return the key if exists or a default value
        """
        if key in self:
            return self.__getitem__(key)
        else:
            return default

    def __contains__(self, key):
        if self._haveKey(key) or key in self.config_defaults:
            return True
        else:
            return False

    def __setitem__(self, key, value):
        if self._haveKey(key):
            query = (
                "UPDATE %s " % self.__tablename__ + "SET value=? WHERE key=?",
                (value, key))
        else:
            query = ("INSERT INTO %s " % self.__tablename__ +
                     "(key, value) VALUES (?, ?)", (key, value))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        connection.commit()

    def delete(self, key):
        """ Delete a key from the configuration store
        """
        query = ("DELETE FROM %s " % (self.__tablename__) + "WHERE key=?",
                 (key,))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(*query)
        connection.commit()

    def __iter__(self):
        query = ("SELECT key, value from %s " % (self.__tablename__))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(query)
        r = {}
        for key, value in cursor.fetchall():
            r[key] = value
        return iter(r)

    def __len__(self):
        query = ("SELECT id from %s " % (self.__tablename__))
        connection = sqlite3.connect(self.sqlDataBaseFile)
        cursor = connection.cursor()
        cursor.execute(query)
        return len(cursor.fetchall())


class WrongKEKException(Exception):
    pass


class KeyEncryptionKey(object):
    """ The keys are encrypted with a KeyEncryptionKey that is stored in
        the configurationStore. It has a checksum to verify correctness
        of the userPassphrase
    """

    userPassphrase = ""
    decrypted_KEK = ""

    #: This key identifies the encrypted KeyEncryptionKey
    # stored in the configuration
    config_key = "encrypted_master_password"

    def __init__(self, user_passphrase):
        """ The encrypted private keys in `keys` are encrypted with a
            random encrypted KeyEncryptionKey that is stored in the
            configuration.

            The userPassphrase is used to encrypt this KeyEncryptionKey. To
            decrypt the keys stored in the keys database, one must use
            BIP38, decrypt the KeyEncryptionKey from the configuration
            store with the userPassphrase, and use the decrypted
            KeyEncryptionKey to decrypt the BIP38 encrypted private keys
            from the keys storage!

            :param str user_passphrase: Password to use for en-/de-cryption
        """
        self.userPassphrase = user_passphrase
        if self.config_key not in configStorage:
            self.newKEK()
            self.saveEncrytpedKEK()
        else:
            self.decryptEncryptedKEK()

    def decryptEncryptedKEK(self):
        """ Decrypt the encrypted KeyEncryptionKey
        """
        aes = AESCipher(self.userPassphrase)
        checksum, encrypted_kek = configStorage[self.config_key].split("$")
        try:
            decrypted_kek = aes.decrypt(encrypted_kek)
        except:  # noqa FIXME(sneak)
            raise WrongKEKException
        if checksum != self.deriveChecksum(decrypted_kek):
            raise WrongKEKException
        self.decrypted_KEK = decrypted_kek

    def saveEncrytpedKEK(self):
        """ Store the encrypted KeyEncryptionKey in the configuration
            store
        """
        configStorage[self.config_key] = self.getEncryptedKEK()

    def newKEK(self):
        """ Generate a new random KeyEncryptionKey
        """
        # make sure to not overwrite an existing key
        if (self.config_key in configStorage
                and configStorage[self.config_key]):
            return
        self.decrypted_KEK = hexlify(os.urandom(32)).decode("ascii")

    def deriveChecksum(self, s):
        """ Derive the checksum
        """
        checksum = hashlib.sha256(compat_bytes(s, "ascii")).hexdigest()
        return checksum[:4]

    def getEncryptedKEK(self):
        """ Obtain the encrypted KeyEncryptionKey
        """
        if not self.decrypted_KEK:
            raise Exception("KeyEncryptionKey not decrypted")
        aes = AESCipher(self.userPassphrase)
        return "{}${}".format(
            self.deriveChecksum(self.decrypted_KEK),
            aes.encrypt(self.decrypted_KEK))

    def changePassphrase(self, newpassphrase):
        """ Change the passphrase
        """
        self.userPassphrase = newpassphrase
        self.saveEncrytpedKEK()

    def purge(self):
        """ Remove the KeyEncryptionKey from the configuration store
        """
        configStorage[self.config_key] = ""


# Create keyStorage
keyStorage = Key()
configStorage = Configuration()

# Create Tables if database is brand new
if not configStorage.exists_table():
    configStorage.create_table()

newKeyStorage = False
if not keyStorage.exists_table():
    newKeyStorage = True
    keyStorage.create_table()
