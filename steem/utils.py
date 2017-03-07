# -*- coding: utf-8 -*-
import json
import re

from urllib.parse import urlparse

import w3lib.url
import langdetect
from langdetect import DetectorFactory

import sbds.sbds_logging

logger = sbds.sbds_logging.getLogger(__name__)

# https://github.com/matiasb/python-unidiff/blob/master/unidiff/constants.py#L37
# @@ (source offset, length) (target offset, length) @@ (section header)
RE_HUNK_HEADER = re.compile(
    r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))?\ @@[ ]?(.*)$",
    flags=re.MULTILINE)

# ensure deterministec language detection
DetectorFactory.seed = 0
MIN_TEXT_LENGTH_FOR_DETECTION = 20


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


def block_info(block):
    from sbds.storages.db.tables.core import prepare_raw_block
    block_dict = prepare_raw_block(block)
    info = dict(
        block_num=block_dict['block_num'],
        transaction_count=len(block_dict['transactions']),
        operation_count=sum(
            len(trans['operations']) for trans in block_dict['transactions']),
        transactions=[], )
    info['brief'] = \
        'block: {block_num} transaction_types: {transactions} total_operations: {operation_count}'

    for trans in block_dict['transactions']:
        info['transactions'].append(trans['operations'][0][0])
    return info


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
        return langdetect.detect(text)
    except langdetect.lang_detect_exception.LangDetectException as e:
        logger.warning(e)
        return None
