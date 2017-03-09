identifier = "@xeroc/piston"
testaccount = "xeroc"
wif = {
    "active": "5KkUHuJEFhN1RCS3GLV7UMeQ5P1k5Vu31jRgivJei8dBtAcXYMV",
    "posting": "5KkUHuJEFhN1RCS3GLV7UMeQ5P1k5Vu31jRgivJei8dBtAcXYMV",
    "owner": "5KkUHuJEFhN1RCS3GLV7UMeQ5P1k5Vu31jRgivJei8dBtAcXYMV"
}
# steem = Steem(nobroadcast=True, keys=wif)
#
#
# class Testcases(unittest.TestCase):
#
#     def __init__(self, *args, **kwargs):
#         super(Testcases, self).__init__(*args, **kwargs)
#         self.post = Post(identifier, steem_instance=steem)
#
#     def test_getOpeningPost(self):
#         self.post._getOpeningPost()
#
#     def test_reply(self):
#         try:
#             self.post.reply(body="foobar", title="", author=testaccount, meta=None)
#         except InsufficientAuthorityError:
#             pass
#         except MissingKeyError:
#             pass
#
#     def test_upvote(self):
#         try:
#             self.post.upvote(voter=testaccount)
#         except VotingInvalidOnArchivedPost:
#             pass
#         except InsufficientAuthorityError:
#             pass
#         except MissingKeyError:
#             pass
#
#     def test_downvote(self, weight=-100, voter=testaccount):
#         try:
#             self.post.downvote(voter=testaccount)
#         except VotingInvalidOnArchivedPost:
#             pass
#         except InsufficientAuthorityError:
#             pass
#         except MissingKeyError:
#             pass
#
#     def test_edit(self):
#         try:
#             steem.edit(identifier, "Foobar")
#         except InsufficientAuthorityError:
#             pass
#         except MissingKeyError:
#             pass
#
#     def test_post(self):
#         try:
#             steem.post("title", "body", meta={"foo": "bar"}, author=testaccount)
#         except InsufficientAuthorityError:
#             pass
#         except MissingKeyError:
#             pass
#
#     def test_create_account(self):
#         try:
#             steem.create_account("xeroc-create",
#                                  creator=testaccount,
#                                  password="foobar foo bar hello world",
#                                  storekeys=False
#                                  )
#         except InsufficientAuthorityError:
#             pass
#         except MissingKeyError:
#             pass
#
#     def test_transfer(self):
#         try:
#             steem.transfer("fabian", 10, "STEEM", account=testaccount)
#         except InsufficientAuthorityError:
#             pass
#         except MissingKeyError:
#             pass
#
#     def test_withdraw_vesting(self):
#         try:
#             steem.withdraw_vesting(10, account=testaccount)
#         except InsufficientAuthorityError:
#             pass
#         except MissingKeyError:
#             pass
#
#     def test_transfer_to_vesting(self):
#         try:
#             steem.transfer_to_vesting(10, to=testaccount, account=testaccount)
#         except InsufficientAuthorityError:
#             pass
#         except MissingKeyError:
#             pass
#
#     def test_get_replies(self):
#         steem.get_replies(author=testaccount)
#
#     def test_get_posts(self):
#         steem.get_posts()
#
#     def test_get_categories(self):
#         steem.get_categories(sort="trending")
#
#     def test_get_balances(self):
#         steem.get_balances(testaccount)
#
#     def test_getPost(self):
#         self.assertEqual(Post("@xeroc/piston", steem_instance=steem).url,
#                          "/piston/@xeroc/piston")
#         self.assertEqual(Post({"author": "@xeroc", "permlink": "piston"}, steem_instance=steem).url,
#                          "/piston/@xeroc/piston")
#
#
# if __name__ == '__main__':
#     unittest.main()
