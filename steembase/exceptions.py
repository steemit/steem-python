import re


def decodeRPCErrorMsg(e):
    """ Helper function to decode the raised Exception and give it a
        python Exception class
    """
    found = re.search(
        ("(10 assert_exception: Assert Exception\n|"
         "3030000 tx_missing_posting_auth)"
         ".*: (.*)\n"),
        str(e),
        flags=re.M)
    if found:
        return found.group(2).strip()
    else:
        return str(e)


class RPCError(Exception):
    pass


class NumRetriesReached(Exception):
    pass


class NoAccessApi(RPCError):
    pass


class AlreadyTransactedThisBlock(RPCError):
    pass


class VoteWeightTooSmall(RPCError):
    pass


class OnlyVoteOnceEvery3Seconds(RPCError):
    pass


class AlreadyVotedSimilarily(RPCError):
    pass


class NoMethodWithName(RPCError):
    pass


class PostOnlyEvery5Min(RPCError):
    pass


class DuplicateTransaction(RPCError):
    pass


class MissingRequiredPostingAuthority(RPCError):
    pass


class UnhandledRPCError(RPCError):
    pass


class ExceededAllowedBandwidth(RPCError):
    pass


class AccountExistsException(Exception):
    pass


class AccountDoesNotExistsException(Exception):
    pass


class InsufficientAuthorityError(Exception):
    pass


class MissingKeyError(Exception):
    pass


class BlockDoesNotExistsException(Exception):
    pass


class WitnessDoesNotExistsException(Exception):
    pass


class InvalidKeyFormat(Exception):
    pass


class NoWallet(Exception):
    pass


class InvalidWifError(Exception):
    pass


class WalletExists(Exception):
    pass


class PostDoesNotExist(Exception):
    pass


class VotingInvalidOnArchivedPost(Exception):
    pass
