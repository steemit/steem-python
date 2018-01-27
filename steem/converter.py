import math

from .amount import Amount
from .instance import shared_steemd_instance


class Converter(object):
    """ Converter simplifies the handling of different metrics of
        the blockchain

        :param Steemd steemd_instance: Steemd() instance to
        use when accessing a RPC

    """

    def __init__(self, steemd_instance=None):
        self.steemd = steemd_instance or shared_steemd_instance()

        self.CONTENT_CONSTANT = 2000000000000

    def sbd_median_price(self):
        """ Obtain the sbd price as derived from the median over all
            witness feeds. Return value will be SBD
        """
        return (Amount(self.steemd.get_feed_history()['current_median_history']
                       ['base']).amount / Amount(self.steemd.get_feed_history(
                       )['current_median_history']['quote']).amount)

    def steem_per_mvests(self):
        """ Obtain STEEM/MVESTS ratio
        """
        info = self.steemd.get_dynamic_global_properties()
        return (Amount(info["total_vesting_fund_steem"]).amount /
                (Amount(info["total_vesting_shares"]).amount / 1e6))

    def vests_to_sp(self, vests):
        """ Obtain SP from VESTS (not MVESTS!)

            :param number vests: Vests to convert to SP
        """
        return vests / 1e6 * self.steem_per_mvests()

    def sp_to_vests(self, sp):
        """ Obtain VESTS (not MVESTS!) from SP

            :param number sp: SP to convert
        """
        return sp * 1e6 / self.steem_per_mvests()

    def sp_to_rshares(self, sp, voting_power=10000, vote_pct=10000):
        """ Obtain the r-shares

            :param number sp: Steem Power
            :param int voting_power: voting power (100% = 10000)
            :param int vote_pct: voting participation (100% = 10000)
        """
        # calculate our account voting shares (from vests), mine is 6.08b
        vesting_shares = int(self.sp_to_vests(sp) * 1e6)

        # calculate vote rshares
        power = (((voting_power * vote_pct) / 10000) / 200) + 1
        rshares = (power * vesting_shares) / 10000

        return rshares

    def steem_to_sbd(self, amount_steem):
        """ Conversion Ratio for given amount of STEEM to SBD at current
            price feed

            :param number amount_steem: Amount of STEEM
        """
        return self.sbd_median_price() * amount_steem

    def sbd_to_steem(self, amount_sbd):
        """ Conversion Ratio for given amount of SBD to STEEM at current
            price feed

            :param number amount_sbd: Amount of SBD
        """
        return amount_sbd / self.sbd_median_price()

    def sbd_to_rshares(self, sbd_payout):
        """ Obtain r-shares from SBD

            :param number sbd_payout: Amount of SBD
        """
        steem_payout = self.sbd_to_steem(sbd_payout)

        props = self.steemd.get_dynamic_global_properties()
        total_reward_fund_steem = Amount(props['total_reward_fund_steem'])
        total_reward_shares2 = int(props['total_reward_shares2'])

        post_rshares2 = (
            steem_payout / total_reward_fund_steem) * total_reward_shares2

        rshares = math.sqrt(
            self.CONTENT_CONSTANT**2 + post_rshares2) - self.CONTENT_CONSTANT
        return rshares

    def rshares_2_weight(self, rshares):
        """ Obtain weight from rshares

            :param number rshares: R-Shares
        """
        _max = 2**64 - 1
        return (_max * rshares) / (2 * self.CONTENT_CONSTANT + rshares)
