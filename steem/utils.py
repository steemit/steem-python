# -*- coding: utf-8 -*-
import json
import logging
import os
import re
import time
import sys
from datetime import datetime

import future
from builtins import bytes

import w3lib.url
from langdetect import DetectorFactory, detect
from langdetect.lang_detect_exception import LangDetectException
from toolz import update_in, assoc

if sys.version >= '3.0':
    from urllib.parse import urlparse
else:
    from urlparse import urlparse

logger = logging.getLogger(__name__)

# https://github.com/matiasb/python-unidiff/blob/master/unidiff/constants.py#L37
# @@ (source offset, length) (target offset, length) @@ (section header)
RE_HUNK_HEADER = re.compile(
    r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))?\ @@[ ]?(.*)$",
    flags=re.MULTILINE)

# ensure deterministec language detection
DetectorFactory.seed = 0
MIN_TEXT_LENGTH_FOR_DETECTION = 20


def block_num_from_hash(block_hash):
    """
    return the first 4 bytes (8 hex digits) of the block ID (the block_num)
    Args:
        block_hash (str):

    Returns:
        int:
    """
    return int(str(block_hash)[:8], base=16)


def block_num_from_previous(previous_block_hash):
    """

    Args:
        previous_block_hash (str):

    Returns:
        int:
    """
    return block_num_from_hash(previous_block_hash) + 1


def chunkify(iterable, chunksize=10000):
    """Yield successive chunksized chunks from iterable.

    Args:
      iterable:
      chunksize:  (Default value = 10000)

    Returns:

    """
    i = 0
    chunk = []
    for item in iterable:
        chunk.append(item)
        i += 1
        if i == chunksize:
            yield chunk
            i = 0
            chunk = []
    if len(chunk) > 0:
        yield chunk


def ensure_decoded(thing):
    if not thing:
        logger.debug('ensure_decoded thing is logically False')
        return None
    if isinstance(thing, (list, dict)):
        logger.debug('ensure_decoded thing is already decoded')
        return thing
    single_encoded_dict = double_encoded_dict = None
    try:
        single_encoded_dict = json.loads(thing)
        if isinstance(single_encoded_dict, dict):
            logger.debug('ensure_decoded thing is single encoded dict')
            return single_encoded_dict
        elif isinstance(single_encoded_dict, str):
            logger.debug('ensure_decoded thing is single encoded str')
            if single_encoded_dict == "":
                logger.debug(
                    'ensure_decoded thing is single encoded str == ""')
                return None
            else:
                double_encoded_dict = json.loads(single_encoded_dict)
                logger.debug('ensure_decoded thing is double encoded')
                return double_encoded_dict
    except Exception as e:
        extra = dict(
            thing=thing,
            single_encoded_dict=single_encoded_dict,
            double_encoded_dict=double_encoded_dict,
            error=e)
        logger.error('ensure_decoded error', extra=extra)
        return None


def findkeys(node, kv):
    if isinstance(node, list):
        for i in node:
            for x in findkeys(i, kv):
                yield x
    elif isinstance(node, dict):
        if kv in node:
            yield node[kv]
        for j in node.values():
            for x in findkeys(j, kv):
                yield x


def extract_keys_from_meta(meta, keys):
    if isinstance(keys, str):
        keys = list([keys])
    extracted = []
    for key in keys:
        for item in findkeys(meta, key):
            if isinstance(item, str):
                extracted.append(item)
            elif isinstance(item, (list, tuple)):
                extracted.extend(item)
            else:
                logger.warning('unusual item in meta: %s', item)
    return extracted


def build_comment_url(parent_permlink=None, author=None, permlink=None):
    return '/'.join([parent_permlink, author, permlink])


def canonicalize_url(url, **kwargs):
    try:
        canonical_url = w3lib.url.canonicalize_url(url, **kwargs)
    except Exception as e:
        logger.warning('url preparation error', extra=dict(url=url, error=e))
        return None
    if canonical_url != url:
        logger.debug('canonical_url changed %s to %s', url, canonical_url)
    try:
        parsed_url = urlparse(canonical_url)
        if not parsed_url.scheme and not parsed_url.netloc:
            _log = dict(
                url=url, canonical_url=canonical_url, parsed_url=parsed_url)
            logger.warning('bad url encountered', extra=_log)
            return None
    except Exception as e:
        logger.warning('url parse error', extra=dict(url=url, error=e))
        return None
    return canonical_url


def findall_patch_hunks(body=None):
    return RE_HUNK_HEADER.findall(body)


def detect_language(text):
    if not text or len(text) < MIN_TEXT_LENGTH_FOR_DETECTION:
        logger.debug('not enough text to perform langdetect')
        return None
    try:
        return detect(text)
    except LangDetectException as e:
        logger.warning(e)
        return None


def is_comment(item):
    """Quick check whether an item is a comment (reply) to another post.
    The item can be a Post object or just a raw comment object from the
    blockchain.
    """
    return item['permlink'][:3] == "re-" and item['parent_author']


def time_elapsed(posting_time):
    """Takes a string time from a post or blockchain event, and returns a
    time delta from now.
    """
    if type(posting_time) == str:
        posting_time = parse_time(posting_time)
    return datetime.utcnow() - posting_time


def parse_time(block_time):
    """Take a string representation of time from the blockchain, and parse
    it into datetime object.
    """
    return datetime.strptime(block_time, '%Y-%m-%dT%H:%M:%S')


def time_diff(time1, time2):
    return parse_time(time1) - parse_time(time2)


def keep_in_dict(obj, allowed_keys=list()):
    """ Prune a class or dictionary of all but allowed keys.
    """
    if type(obj) == dict:
        items = obj.items()
    else:
        items = obj.__dict__.items()

    return {k: v for k, v in items if k in allowed_keys}


def remove_from_dict(obj, remove_keys=list()):
    """ Prune a class or dictionary of specified keys.
    """
    if type(obj) == dict:
        items = obj.items()
    else:
        items = obj.__dict__.items()

    return {k: v for k, v in items if k not in remove_keys}


def construct_identifier(*args):
    """ Create a post identifier from comment/post object or arguments.

    Examples:

        ::
            construct_identifier('username', 'permlink')
            construct_identifier({'author': 'username',
                'permlink': 'permlink'})
    """

    if len(args) == 1:
        op = args[0]
        author, permlink = op['author'], op['permlink']
    elif len(args) == 2:
        author, permlink = args
    else:
        raise ValueError(
            'construct_identifier() received unparsable arguments')

    fields = dict(author=author, permlink=permlink)
    return "{author}/{permlink}".format(**fields)


def json_expand(json_op, key_name='json'):
    """ Convert a string json object to Python dict in an op. """
    if type(json_op) == dict and key_name in json_op and json_op[key_name]:
        try:
            return update_in(json_op, [key_name], json.loads)
        except JSONDecodeError:
            return assoc(json_op, key_name, {})

    return json_op


def sanitize_permlink(permlink):
    permlink = permlink.strip()
    permlink = re.sub("_|\s|\.", "-", permlink)
    permlink = re.sub("[^\w-]", "", permlink)
    permlink = re.sub("[^a-zA-Z0-9-]", "", permlink)
    permlink = permlink.lower()
    return permlink


def derive_permlink(title, parent_permlink=None):
    permlink = ""
    if parent_permlink:
        permlink += "re-"
        permlink += parent_permlink
        permlink += "-" + fmt_time(time.time())
    else:
        permlink += title

    return sanitize_permlink(permlink)


def resolve_identifier(identifier):
    match = re.match("@?([\w\-\.]*)/([\w\-]*)", identifier)
    if not hasattr(match, "group"):
        raise ValueError("Invalid identifier")
    return match.group(1), match.group(2)


def fmt_time(t):
    """ Properly Format Time for permlinks
    """
    return datetime.utcfromtimestamp(t).strftime("%Y%m%dt%H%M%S%Z")


def fmt_time_string(t):
    """ Properly Format Time for permlinks
    """
    return datetime.strptime(t, '%Y-%m-%dT%H:%M:%S')


def fmt_time_from_now(secs=0):
    """ Properly Format Time that is `x` seconds in the future

        :param int secs: Seconds to go in the future (`x>0`) or the
                         past (`x<0`)
        :return: Properly formated time for Graphene (`%Y-%m-%dT%H:%M:%S`)
        :rtype: str

    """
    return datetime.utcfromtimestamp(time.time() + int(secs)).strftime(
        '%Y-%m-%dT%H:%M:%S')


def env_unlocked():
    """ Check if wallet password is provided as ENV variable. """
    return os.getenv('UNLOCK', False)


# todo remove these
def strfage(time, fmt=None):
    """ Format time/age
    """
    if not hasattr(time, "days"):  # dirty hack
        now = datetime.utcnow()
        if isinstance(time, str):
            time = datetime.strptime(time, '%Y-%m-%dT%H:%M:%S')
        time = (now - time)

    d = {"days": time.days}
    d["hours"], rem = divmod(time.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)

    s = "{seconds} seconds"
    if d["minutes"]:
        s = "{minutes} minutes " + s
    if d["hours"]:
        s = "{hours} hours " + s
    if d["days"]:
        s = "{days} days " + s
    return s.format(**d)


def strfdelta(tdelta, fmt):
    """ Format time/age
    """
    if not tdelta or not hasattr(tdelta, "days"):  # dirty hack
        return None

    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)


def is_valid_account_name(name):
    return re.match('^[a-z][a-z0-9\-.]{2,15}$', name)


def compat_compose_dictionary(dictionary, **kwargs):
    """
    This method allows us the one line dictionary composition that is offered by the ** dictionary unpacking
    available in 3.6.

    :param dictionary: the dictionary to add the kwargs elements to.
    :param kwargs: a set of key/value pairs to add to `dictionary`.
    :return: the composed dictionary.
    """
    composed_dict = dictionary.copy()
    composed_dict.update(kwargs)

    return composed_dict


def compat_bytes(item, encoding=None):
    """
    This method is required because Python 2.7 `bytes` is simply an alias for `str`. Without this method,
    code execution would look something like:

    class clazz(object):

        def __bytes__(self):
            return bytes(5)


    Python 2.7:

    c = clazz()
    bytes(c)
    >>'<__main__.clazz object at 0x105171a90>'

    In this example, when `bytes(c)` is invoked, the interpreter then calls `str(c)`, and prints the above string.
    the method `__bytes__` is never invoked.

    Python 3.6:
    c = clazz()
    bytes(c)
    >>b'\x00\x00\x00\x00\x00'

    This is the expected and necessary behavior across both platforms.

    w/ compat_bytes method, we will ensure that the correct bytes method is always invoked, avoiding the `str` alias in
    2.7.

    :param item: this is the object who's bytes method needs to be invoked
    :param encoding: optional encoding parameter to handle the Python 3.6 two argument 'bytes' method.
    :return: a bytes object that functions the same across 3.6 and 2.7
    """
    if hasattr(item, '__bytes__'):
        return item.__bytes__()
    else:
        if encoding:
            return bytes(item, encoding)
        else:
            return bytes(item)


def compat_chr(item):
    """
    This is necessary to maintain compatibility across Python 2.7 and 3.6.
    In 3.6, 'chr' handles any unicode character, whereas in 2.7, `chr` only handles
    ASCII characters. Thankfully, the Python 2.7 method `unichr` provides the same
    functionality as 3.6 `chr`.

    :param item: a length 1 string who's `chr` method needs to be invoked
    :return: the unichr code point of the single character string, item
    """
    if sys.version >= '3.0':
        return chr(item)
    else:
        return unichr(item)
