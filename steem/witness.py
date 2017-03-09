from .instance import shared_steem_instance

from steembase.exceptions import WitnessDoesNotExistsException


class Witness(dict):
    """ Read data about a witness in the chain

        :param str witness: Name of the witness
        :param Steem steem_instance: Steem() instance to use when accesing a RPC
        :param bool lazy: Use lazy loading

    """
    def __init__(self, witness, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        self.witness_name = witness
        self.witness = None
        self.refresh()

    def refresh(self):
        witness = self.steem.get_witness_by_account(self.witness_name)
        if not witness:
            raise WitnessDoesNotExistsException
        super(Witness, self).__init__(witness)

    def __getitem__(self, key):
        return super(Witness, self).__getitem__(key)

    def items(self):
        return super(Witness, self).items()
