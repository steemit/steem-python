import json
import re
from datetime import datetime

from funcy.colls import walk_values
from piston.instance import shared_steem_instance
from pistonbase.operations import Comment_options

from .amount import Amount
from steembase.exceptions import (
    PostDoesNotExist,
    VotingInvalidOnArchivedPost
)
from .utils import (
    resolveIdentifier,
    constructIdentifier,
    remove_from_dict,
)
from steem.utils import parse_time, remove_from_dict


class Post(dict):
    """ This object gets instanciated by Steem.streams and is used as an
        abstraction layer for Comments in Steem

        :param identifier post: The post as obtained by `get_content` or the identifier string of the post (``@author/permlink``)
        :param Steem steem_instance: Steem() instance to use when accesing a RPC
        :param bool lazy: Use lazy loading

    """
    steem = None

    def __init__(
        self,
        post,
        steem_instance=None,
        lazy=False
    ):
        self.steem = steem_instance or shared_steem_instance()
        self.loaded = False

        if isinstance(post, str):  # From identifier
            parts = post.split("@")
            self.identifier = "@" + parts[-1]

            if not lazy:
                self.refresh()

        elif (isinstance(post, dict) and  # From dictionary
                "author" in post and
                "permlink" in post):
            # strip leading @
            if post["author"][0] == "@":
                post["author"] = post["author"][1:]
            self.identifier = constructIdentifier(
                post["author"],
                post["permlink"]
            )

            if "created" in post:
                self._store_post(post)

        else:
            raise ValueError("Post expects an identifier or a dict "
                             "with author and permlink!")

    def refresh(self):
        post_author, post_permlink = resolveIdentifier(self.identifier)
        post = self.steem.rpc.get_content(post_author, post_permlink)
        if not post["permlink"]:
            raise PostDoesNotExist("Post does not exist: %s" % self.identifier)

        # If this 'post' comes from an operation, it might carry a patch
        if "body" in post and re.match("^@@", post["body"]):
            self._patched = True
            self._patch = post["body"]

        # Total reward
        post["total_payout_reward"] = (
            Amount(post.get("total_payout_value", "0 %s" % self.steem.symbol("SBD"))) +
            Amount(post.get("total_pending_payout_value", "0 %s" % self.steem.symbol("SBD")))
        )

        # Parse Times
        parse_times = ["active",
                       "cashout_time",
                       "created",
                       "last_payout",
                       "last_update",
                       "max_cashout_time"]
        for p in parse_times:
            post[p] = parse_time(post.get(p, "1970-01-01T00:00:00"))

        # Parse Amounts
        sbd_amounts = [
            "total_payout_reward",
            "max_accepted_payout",
            "pending_payout_value",
            "curator_payout_value",
            "total_pending_payout_value",
            "promoted",
        ]
        for p in sbd_amounts:
            post[p] = Amount(post.get(p, "0.000 %s" % self.steem.symbol("SBD")))

        # Try to properly format json meta data

        try:
            meta_str = post.get("json_metadata", "{}")
            post['json_metadata'] = json.loads(meta_str)
        except:
            post['json_metadata'] = dict()
        if not post['json_metadata']:
            post['json_metadata'] = dict()

        post["tags"] = []
        if post["depth"] == 0:
            post["tags"] = (
                [post["parent_permlink"]] +
                post["json_metadata"].get("tags", [])
            )

        # Retrieve the root comment
        self.openingPostIdentifier, self.category = self._getOpeningPost(post)

        self._store_post(post)

    def _store_post(self, post):
        # Store original values as obtained from the rpc
        for key, value in post.items():
            super(Post, self).__setitem__(key, value)

        # Set attributes as well
        for key in post:
            setattr(self, key, post[key])

        # also set identifier
        super(Post, self).__setitem__("identifier", self.identifier)

        self.loaded = True

    def __getattr__(self, key):
        if not self.loaded:
            self.refresh()
        return object.__getattribute__(self, key)

    def __getitem__(self, key):
        if not self.loaded:
            self.refresh()
        return super(Post, self).__getitem__(key)

    def __repr__(self):
        return "<Post-%s>" % self.identifier

    __str__ = __repr__

    def _getOpeningPost(self, post=None):
        if not post:
            post = self
        m = re.match("/([^/]*)/@([^/]*)/([^#]*).*",
                     post.get("url", ""))
        if not m:
            return "", ""
        else:
            category = m.group(1)
            author = m.group(2)
            permlink = m.group(3)
            return constructIdentifier(
                author, permlink
            ), category

    def get_comments(self, sort="total_payout_reward"):
        """ Return **first-level** comments of the post.
        """
        post_author, post_permlink = resolveIdentifier(self.identifier)
        posts = self.steem.rpc.get_content_replies(post_author, post_permlink)
        r = []
        for post in posts:
            r.append(Post(post, steem_instance=self.steem))
        if sort == "total_payout_value":
            r = sorted(r, key=lambda x: float(
                x["total_payout_value"]
            ), reverse=True)
        elif sort == "total_payout_reward":
            r = sorted(r, key=lambda x: float(
                x["total_payout_reward"]
            ), reverse=True)
        else:
            r = sorted(r, key=lambda x: x[sort])
        return(r)

    def reply(self, body, title="", author="", meta=None):
        """ Reply to the post

            :param str body: (required) body of the reply
            :param str title: Title of the reply
            :param str author: Author of reply
            :param json meta: JSON Meta data
        """
        return self.steem.reply(self.identifier, body, title, author, meta)

    def upvote(self, weight=+100, voter=None):
        """ Upvote the post

            :param float weight: (optional) Weight for posting (-100.0 - +100.0) defaults to +100.0
            :param str voter: (optional) Voting account
        """
        return self.vote(weight, voter=voter)

    def downvote(self, weight=-100, voter=None):
        """ Downvote the post

            :param float weight: (optional) Weight for posting (-100.0 - +100.0) defaults to -100.0
            :param str voter: (optional) Voting account
        """
        return self.vote(weight, voter=voter)

    def vote(self, weight, voter=None):
        """ Vote the post

            :param float weight: Weight for posting (-100.0 - +100.0)
            :param str voter: Voting account
        """
        # Test if post is archived, if so, voting is worthless but just
        # pollutes the blockchain and account history
        if getattr(self, "mode") == "archived":
            raise VotingInvalidOnArchivedPost
        return self.steem.vote(self.identifier, weight, voter=voter)

    @property
    def reward(self):
        """Return a float value of estimated total SBD reward.
        """
        if not self.loaded:
            self.refresh()
        return self['total_payout_reward']

    @property
    def meta(self):
        if not self.loaded:
            self.refresh()
        return self.get('json_metadata', dict())

    def time_elapsed(self):
        """Return a timedelta on how old the post is.
        """
        return datetime.utcnow() - self['created']

    def is_main_post(self):
        """ Retuns True if main post, and False if this is a comment (reply).
        """
        return self['depth'] == 0

    def is_opening_post(self):
        """ Retuns True if main post, and False if this is a comment (reply).
        """
        return self['depth'] == 0

    def is_comment(self):
        """ Retuns True if post is a comment
        """
        return self['depth'] > 0

    def curation_reward_pct(self):
        """ If post is less than 30 minutes old, it will incur a curation reward penalty.
        """
        reward = (self.time_elapsed().seconds / 1800) * 100
        if reward > 100:
            reward = 100
        return reward

    def export(self):
        """ This method returns a dictionary that is type-safe to store as JSON or in a database.
        """
        self.refresh()

        # Remove Steem instance object
        safe_dict = remove_from_dict(self, ['steem'])

        # Convert Amount class objects into pure dictionaries
        def decompose_amounts(item):
            if type(item) == Amount:
                return item.__dict__
            return item
        return walk_values(decompose_amounts, safe_dict)

    def set_comment_options(self, options):
        op = Comment_options(
            **{"author": self["author"],
               "permlink": self["permlink"],
               "max_accepted_payout":
                   options.get("max_accepted_payout", str(self["max_accepted_payout"])),
               "percent_steem_dollars": int(
                   options.get("percent_steem_dollars",
                               self["percent_steem_dollars"] / 100
                               ) * 100),
               "allow_votes":
                   options.get("allow_votes", self["allow_votes"]),
               "allow_curation_rewards":
                   options.get("allow_curation_rewards", self["allow_curation_rewards"]),
               }
        )
        return self.steem.finalizeOp(op, self["author"], "posting")
