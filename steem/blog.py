from contextlib import suppress

from funcy.seqs import rest, first
from steembase.exceptions import PostDoesNotExist

from .account import Account
from .instance import shared_steemd_instance
from .post import Post
from .utils import is_comment


class Blog:
    """ Obtain a list of blog posts of an account

        :param str account_name: Name of the account
        :param Steemd steemd_instance: Steemd() instance to use when accessing a RPC

    """

    def __init__(self, account_name, steemd_instance=None):
        self.steem = steemd_instance or shared_steemd_instance()

        self.account = Account(account_name)
        self.current_index = self.account.virtual_op_count()
        self.history = None

        # prevent duplicates
        self.seen_items = set()

    def refresh(self):
        # fetch the next batch
        if self.current_index == 0:
            raise StopIteration

        limit = 1000
        if self.current_index < 1000:
            # avoid duplicates on last batch
            limit = 1000 - self.current_index
            self.current_index = 1000

        h = self.steem.get_account_history(self.account.name, self.current_index, limit)
        if not h:
            raise StopIteration

        self.current_index -= 1000

        # filter out irrelevant items
        def blogpost_only(item):
            op_type, op = item[1]['op']
            return op_type == 'comment' and not is_comment(op)

        hist = filter(blogpost_only, h)
        hist = map(lambda x: x[1]['op'][1], hist)
        hist = [x for x in hist if x['author'] == self.account.name]

        # filter out items that have been already passed on
        # this is necessary because post edits create multiple entries in the chain
        hist_uniq = []
        for item in hist:
            if item['permlink'] not in self.seen_items:
                self.seen_items.add(item['permlink'])
                hist_uniq.append(item)

        # LIFO
        self.history = hist_uniq[::-1]

    def __iter__(self):
        return self

    def __next__(self):
        while not self.history:
            self.refresh()

        while self.history:
            # consume an item from history
            next_item = first(self.history)
            self.history = list(rest(self.history))

            # stay in while loop until we find a post that exists
            with suppress(PostDoesNotExist):
                return Post(next_item)
