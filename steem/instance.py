import piston as pstn

_shared_steem_instance = None


def shared_steem_instance():
    """ This method will initialize _shared_steem_instance and return it.
    The purpose of this method is to have offer single default Steem instance that can be reused by multiple classes.
    """
    global _shared_steem_instance
    if not _shared_steem_instance:
        _shared_steem_instance = pstn.Steem()  # todo: add piston config
    return _shared_steem_instance


def set_shared_steem_instance(steem_instance):
    """ This method allows us to override default steem instance for all users of
    _shared_steem_instance.
    """
    global _shared_steem_instance
    _shared_steem_instance = steem_instance
