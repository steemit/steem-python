import steem as stm

_shared_steemd_instance = None


def get_config_node_list():
    from steembase.storage import configStorage
    nodes = configStorage.get('nodes', None)
    if nodes:
        return nodes.split(',')


def shared_steemd_instance():
    """ This method will initialize _shared_steemd_instance and return it.
    The purpose of this method is to have offer single default Steem
    instance that can be reused by multiple classes.  """

    global _shared_steemd_instance
    if not _shared_steemd_instance:
        _shared_steemd_instance = stm.steemd.Steemd(
            nodes=get_config_node_list())
    return _shared_steemd_instance


def set_shared_steemd_instance(steemd_instance):
    """ This method allows us to override default steem instance for all
    users of _shared_steemd_instance.  """

    global _shared_steemd_instance
    _shared_steemd_instance = steemd_instance
