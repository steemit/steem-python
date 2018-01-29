from steem.post import Post


def test_post_refresh():
    """ Post should load correctly if passed a dict or string identifier. """
    p1 = Post('https://steemit.com/marketing/@steemitblog/'
              'marketing-w-mitchell-a-steem-ecosystem')
    p2 = Post({
        'author': 'steemitblog',
        'permlink': 'marketing-w-mitchell-a-steem-ecosystem'
    })

    # did post load?
    assert 'json_metadata' in p1 and 'json_metadata' in p2

    # are posts the same
    assert p1.export() == p2.export()
