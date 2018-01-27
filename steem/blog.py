from funcy.flow import silent
from funcy.funcs import complement
from funcy.seqs import take, first

from .account import Account
from .instance import shared_steemd_instance
from .post import Post
from .utils import is_comment


class Blog:
    """ Obtain a list of blog posts for an account

        Args:
            account_name (str): Name of the account
            comments_only (bool): (Default False). Toggle between posts
                and comments.
            steemd_instance (Steemd): Steemd instance overload

        Returns:
            Generator with Post objects in reverse chronological order.

        Example:
            To get all posts, you can use either generator:

            ::

                gen1 = Blog('furion')
                gen2 = b.all()

                next(gen1)
                next(gen2)

            To get some posts, you can call `take()`:

            ::

                b = Blog('furion')
                posts = b.take(5)

    """

    def __init__(self,
                 account_name: str,
                 comments_only=False,
                 steemd_instance=None):
        self.steem = steemd_instance or shared_steemd_instance()
        self.comments_only = comments_only
        self.account = Account(account_name)
        self.history = self.account.history_reverse(filter_by='comment')
        self.seen_items = set()

    def take(self, limit=5):
        """ Take up to n (n = limit) posts/comments at a time.

        You can call this method as many times as you want. Once
        there are no more posts to take, it will return [].

        Returns:
            List of posts/comments in a batch of size up to `limit`.
        """
        # get main posts only
        comment_filter = is_comment if self.comments_only else complement(
            is_comment)
        hist = filter(comment_filter, self.history)

        # filter out reblogs
        def match_author(x):
            return x['author'] == self.account.name

        hist2 = filter(match_author, hist)

        # post edits will re-appear in history
        # we should therefore filter out already seen posts
        def ensure_unique(post):
            if post['permlink'] not in self.seen_items:
                self.seen_items.add(post['permlink'])
                return True

        unique = filter(ensure_unique, hist2)

        serialized = filter(bool, map(silent(Post), unique))

        batch = take(limit, serialized)
        return batch

    def all(self):
        """ A generator that will return ALL of account history. """
        while True:
            chunk = self.take(10)
            if chunk:
                for little_chunk in iter(chunk):
                    yield little_chunk
            else:
                break

    def __iter__(self):
        return self

    def __next__(self):
        next_item = first(self.take(1))
        if not next_item:
            raise StopIteration

        return next_item
