import json
import logging
import re
from datetime import datetime

from funcy.colls import walk_values, get_in
from funcy.flow import silent
from funcy.seqs import flatten
from steembase.exceptions import (
    PostDoesNotExist,
    VotingInvalidOnArchivedPost,
)
from steembase.operations import CommentOptions

from .amount import Amount
from .commit import Commit
from .instance import shared_steemd_instance
from .utils import construct_identifier, resolve_identifier
from .utils import parse_time, remove_from_dict

log = logging.getLogger(__name__)


class Post(dict):
    """ This object gets instantiated by Steem.streams and is used as an
        abstraction layer for Comments in Steem

        Args:

            post (str or dict): ``@author/permlink`` or raw ``comment`` as
            dictionary.

            steemd_instance (Steemd): Steemd node to connect to

    """

    def __init__(self, post, steemd_instance=None):
        self.steemd = steemd_instance or shared_steemd_instance()
        self.commit = Commit(steemd_instance=self.steemd)

        # will set these during refresh()
        self.patched = False
        self.category = None
        self.root_identifier = None

        if isinstance(post, str):  # From identifier
            self.identifier = self.parse_identifier(post)
        elif isinstance(post,
                        dict) and "author" in post and "permlink" in post:
            post["author"] = post["author"].replace('@', '')
            self.identifier = construct_identifier(post["author"],
                                                   post["permlink"])
        else:
            raise ValueError("Post expects an identifier or a dict "
                             "with author and permlink!")

        self.refresh()

    @staticmethod
    def parse_identifier(uri):
        """ Extract post identifier from post URL. """
        return '@%s' % uri.split('@')[-1]

    def refresh(self):
        post_author, post_permlink = resolve_identifier(self.identifier)
        post = self.steemd.get_content(post_author, post_permlink)
        if not post["permlink"]:
            raise PostDoesNotExist("Post does not exist: %s" % self.identifier)

        # If this 'post' comes from an operation, it might carry a patch
        if "body" in post and re.match("^@@", post["body"]):
            self.patched = True

        # Parse Times
        parse_times = [
            "active", "cashout_time", "created", "last_payout", "last_update",
            "max_cashout_time"
        ]
        for p in parse_times:
            post[p] = parse_time(post.get(p, "1970-01-01T00:00:00"))

        # Parse Amounts
        sbd_amounts = [
            "total_payout_value",
            "max_accepted_payout",
            "pending_payout_value",
            "curator_payout_value",
            "total_pending_payout_value",
            "promoted",
        ]
        for p in sbd_amounts:
            post[p] = Amount(post.get(p, "0.000 SBD"))

        # turn json_metadata into python dict
        meta_str = post.get("json_metadata", "{}")
        post['json_metadata'] = silent(json.loads)(meta_str) or {}

        post["tags"] = []
        post['community'] = ''
        if isinstance(post['json_metadata'], dict):
            if post["depth"] == 0:
                post["tags"] = (post["parent_permlink"], *get_in(
                    post, ['json_metadata', 'tags'], default=[]))

            post['community'] = get_in(
                post, ['json_metadata', 'community'], default='')

        # If this post is a comment, retrieve the root comment
        self.root_identifier, self.category = self._get_root_identifier(post)

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

    def __getattr__(self, key):
        return object.__getattribute__(self, key)

    def __getitem__(self, key):
        return super(Post, self).__getitem__(key)

    def __repr__(self):
        return "<Post-%s>" % self.identifier

    __str__ = __repr__

    def _get_root_identifier(self, post=None):
        if not post:
            post = self
        m = re.match("/([^/]*)/@([^/]*)/([^#]*).*", post.get("url", ""))
        if not m:
            return "", ""
        else:
            category = m.group(1)
            author = m.group(2)
            permlink = m.group(3)
            return construct_identifier(author, permlink), category

    def get_replies(self):
        """ Return **first-level** comments of the post.
        """
        post_author, post_permlink = resolve_identifier(self.identifier)
        replies = self.steemd.get_content_replies(post_author, post_permlink)
        return map(silent(Post), replies)

    @staticmethod
    def get_all_replies(root_post=None, comments=list(), all_comments=list()):
        """ Recursively fetch all the child comments, and return them as a list.

        Usage: all_comments = Post.get_all_replies(Post('@foo/bar'))
        """
        # see if our root post has any comments
        if root_post:
            return Post.get_all_replies(comments=list(root_post.get_replies()))
        if not comments:
            return all_comments

        # recursively scrape children one depth layer at a time
        children = list(flatten([list(x.get_replies()) for x in comments]))
        if not children:
            return all_comments or comments
        return Post.get_all_replies(
            comments=children, all_comments=comments + children)

    @property
    def reward(self):
        """Return a float value of estimated total SBD reward.
        """
        return Amount(self.get("total_payout_value", "0 SBD")) + \
            Amount(self.get("pending_payout_value", "0 SBD"))

    def time_elapsed(self):
        """Return a timedelta on how old the post is.
        """
        return datetime.utcnow() - self['created']

    def is_main_post(self):
        """ Retuns True if main post, and False if this is a comment (reply).
        """
        return self['depth'] == 0

    def is_comment(self):
        """ Retuns True if post is a comment
        """
        return self['depth'] > 0

    def curation_reward_pct(self):
        """ If post is less than 30 minutes old, it will incur a curation
        reward penalty.  """
        reward = (self.time_elapsed().seconds / 1800) * 100
        if reward > 100:
            reward = 100
        return reward

    def export(self):
        """ This method returns a dictionary that is type-safe to store as
        JSON or in a database.  """
        self.refresh()

        # Remove Steem instance object
        safe_dict = remove_from_dict(self, ['steemd', 'commit'])

        # Convert Amount class objects into pure dictionaries
        def decompose_amounts(item):
            if type(item) == Amount:
                return dict(item)
            return item

        return walk_values(decompose_amounts, safe_dict)

    ######################
    # Commital Properties
    ######################
    def upvote(self, weight=+100, voter=None):
        """ Upvote the post

            :param float weight: (optional) Weight for posting (-100.0 -
            +100.0) defaults to +100.0
            :param str voter: (optional) Voting account
        """
        return self.vote(weight, voter=voter)

    def downvote(self, weight=-100, voter=None):
        """ Downvote the post

            :param float weight: (optional) Weight for posting (-100.0 -
            +100.0) defaults to -100.0
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
        if not self.get('net_rshares'):
            raise VotingInvalidOnArchivedPost
        return self.commit.vote(self.identifier, weight, account=voter)

    def edit(self, body, meta=None, replace=False):
        """ Edit an existing post

            :param str body: Body of the reply
            :param json meta: JSON meta object that can be attached to the
                              post. (optional)
            :param bool replace: Instead of calculating a *diff*, replace
                                 the post entirely (defaults to ``False``)
        """
        if not meta:
            meta = {}
        original_post = self

        if replace:
            newbody = body
        else:
            import diff_match_patch
            dmp = diff_match_patch.diff_match_patch()
            patch = dmp.patch_make(original_post["body"], body)
            newbody = dmp.patch_toText(patch)

            if not newbody:
                log.info("No changes made! Skipping ...")
                return

        reply_identifier = construct_identifier(
            original_post["parent_author"], original_post["parent_permlink"])

        new_meta = {}
        if meta:
            if original_post["json_metadata"]:
                import json
                new_meta = original_post["json_metadata"].update(meta)
            else:
                new_meta = meta

        return self.commit.post(
            original_post["title"],
            newbody,
            reply_identifier=reply_identifier,
            author=original_post["author"],
            permlink=original_post["permlink"],
            json_metadata=new_meta,
        )

    def reply(self, body, title="", author="", meta=None):
        """ Reply to an existing post

            :param str body: Body of the reply
            :param str title: Title of the reply post
            :param str author: Author of reply (optional) if not provided
                               ``default_user`` will be used, if present, else
                               a ``ValueError`` will be raised.
            :param json meta: JSON meta object that can be attached to the
                              post. (optional)
        """
        return self.commit.post(
            title,
            body,
            json_metadata=meta,
            author=author,
            reply_identifier=self.identifier)

    def set_comment_options(self, options):
        op = CommentOptions(
            **{
                "author":
                self["author"],
                "permlink":
                self["permlink"],
                "max_accepted_payout":
                options.get("max_accepted_payout",
                            str(self["max_accepted_payout"])),
                "percent_steem_dollars":
                int(
                    options.get("percent_steem_dollars",
                                self["percent_steem_dollars"] / 100) * 100),
                "allow_votes":
                options.get("allow_votes", self["allow_votes"]),
                "allow_curation_rewards":
                options.get("allow_curation_rewards", self[
                    "allow_curation_rewards"]),
            })
        return self.commit.finalizeOp(op, self["author"], "posting")
