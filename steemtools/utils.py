import os
import re
import sys
import time
from datetime import datetime

import frontmatter


def constructIdentifier(author, slug):
    return "@%s/%s" % (author, slug)


def sanitizePermlink(permlink):
    permlink = permlink.strip()
    permlink = re.sub("_|\s|\.", "-", permlink)
    permlink = re.sub("[^\w-]", "", permlink)
    permlink = re.sub("[^a-zA-Z0-9-]", "", permlink)
    permlink = permlink.lower()
    return permlink


def derivePermlink(title, parent_permlink=None):
    permlink = ""
    if parent_permlink:
        permlink += "re-"
        permlink += parent_permlink
        permlink += "-" + formatTime(time.time())
    else:
        permlink += title

    return sanitizePermlink(permlink)


def resolveIdentifier(identifier):
    match = re.match("@?([\w\-\.]*)/([\w\-]*)", identifier)
    if not hasattr(match, "group"):
        raise ValueError("Invalid identifier")
    return match.group(1), match.group(2)


def yaml_parse_file(args, initial_content):
    message = None

    if args.file and args.file != "-":
        if not os.path.isfile(args.file):
            raise Exception("File %s does not exist!" % args.file)
        with open(args.file) as fp:
            message = fp.read()
    elif args.file == "-":
        message = sys.stdin.read()
    else:
        import tempfile
        from subprocess import Popen
        EDITOR = os.environ.get('EDITOR', 'vim')
        # prefix = ""
        # if "permlink" in initial_content.metadata:
        #   prefix = initial_content.metadata["permlink"]
        with tempfile.NamedTemporaryFile(
                suffix=b".md",
                prefix=b"steem-",
                delete=False
        ) as fp:
            # Write initial content
            fp.write(bytes(frontmatter.dumps(initial_content), 'utf-8'))
            fp.flush()
            # Define parameters for command
            args = [EDITOR]
            if re.match("gvim", EDITOR):
                args.append("-f")
            args.append(fp.name)
            # Execute command
            Popen(args).wait()
            # Read content of file
            fp.seek(0)
            message = fp.read().decode('utf-8')

    try:
        meta, body = frontmatter.parse(message)
    except:
        meta = initial_content.metadata
        body = message

    # make sure that at least the metadata keys of initial_content are
    # present!
    for key in initial_content.metadata:
        if key not in meta:
            meta[key] = initial_content.metadata[key]

    # Extract anything that is not steem-libs meta and return it separately
    # for json_meta field
    json_meta = {key: meta[key] for key in meta if key not in [
        "title",
        "category",
        "author"
    ]}

    return meta, json_meta, body


def formatTime(t):
    """ Properly Format Time for permlinks
    """
    return datetime.utcfromtimestamp(t).strftime("%Y%m%dt%H%M%S%Z")


def formatTimeString(t):
    """ Properly Format Time for permlinks
    """
    return datetime.strptime(t, '%Y-%m-%dT%H:%M:%S')


def strfage(time, fmt=None):
    """ Format time/age
    """
    if not hasattr(time, "days"):  # dirty hack
        now = datetime.now()
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


def formatTimeFromNow(secs=0):
    """ Properly Format Time that is `x` seconds in the future

        :param int secs: Seconds to go in the future (`x>0`) or the
                         past (`x<0`)
        :return: Properly formated time for Graphene (`%Y-%m-%dT%H:%M:%S`)
        :rtype: str

    """
    return datetime.utcfromtimestamp(time.time() + int(secs)).strftime('%Y-%m-%dT%H:%M:%S')


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
