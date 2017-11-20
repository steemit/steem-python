# -*- coding: utf-8 -*-
import json
import logging
import os
import re
import time
from datetime import datetime
from json import JSONDecodeError

from toolz import update_in, assoc

logger = logging.getLogger(__name__)


def block_num_from_hash(block_hash: str) -> int:
    """
    return the first 4 bytes (8 hex digits) of the block ID (the block_num)
    Args:
        block_hash (str):

    Returns:
        int:
    """
    return int(str(block_hash)[:8], base=16)


def block_num_from_previous(previous_block_hash: str) -> int:
    """

    Args:
        previous_block_hash (str):

    Returns:
        int:
    """
    return block_num_from_hash(previous_block_hash) + 1



def is_comment(item):
    """Quick check whether an item is a comment (reply) to another post.
    The item can be a Post object or just a raw comment object from the blockchain.
    """
    return item['permlink'][:3] == "re-" and item['parent_author']


def time_elapsed(posting_time):
    """Takes a string time from a post or blockchain event, and returns a time delta from now.
    """
    if type(posting_time) == str:
        posting_time = parse_time(posting_time)
    return datetime.utcnow() - posting_time


def parse_time(block_time):
    """Take a string representation of time from the blockchain, and parse it into datetime object.
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


def construct_identifier(*args, username_prefix='@'):
    """ Create a post identifier from comment/post object or arguments. 
    
    Examples:
        
        :: 
        
            construct_identifier('username', 'permlink')
            construct_identifier({'author': 'username', 'permlink': 'permlink'})
    """
    if len(args) == 1:
        op = args[0]
        author, permlink = op['author'], op['permlink']
    elif len(args) == 2:
        author, permlink = args
    else:
        raise ValueError('construct_identifier() received unparsable arguments')

    fields = dict(prefix=username_prefix, author=author, permlink=permlink)
    return "{prefix}{author}/{permlink}".format(**fields)


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
    return datetime.utcfromtimestamp(time.time() + int(secs)).strftime('%Y-%m-%dT%H:%M:%S')


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



