class Amount(dict):
    """ This class helps deal and calculate with the different assets on the
            chain.

        :param str amountString: Amount string as used by the backend
            (e.g. "10 SBD")
    """

    def __init__(self, amount_string="0 SBD"):
        if isinstance(amount_string, Amount):
            self["amount"] = amount_string["amount"]
            self["asset"] = amount_string["asset"]
        elif isinstance(amount_string, str):
            self["amount"], self["asset"] = amount_string.split(" ")
        else:
            raise ValueError(
                "Need an instance of 'Amount' or a string with amount " +
                "and asset")

        self["amount"] = float(self["amount"])

    @property
    def amount(self):
        return self["amount"]

    @property
    def symbol(self):
        return self["asset"]

    @property
    def asset(self):
        return self["asset"]

    def __str__(self):
        # STEEM
        if self["asset"] == "SBD":
            prec = 3
        elif self["asset"] == "STEEM":
            prec = 3
        elif self["asset"] == "VESTS":
            prec = 6

        # default
        else:
            prec = 6
        return "{:.{prec}f} {}".format(
            self["amount"], self["asset"], prec=prec)

    def __float__(self):
        return self["amount"]

    def __int__(self):
        return int(self["amount"])

    def __add__(self, other):
        a = Amount(self)
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            a["amount"] += other["amount"]
        else:
            a["amount"] += float(other)
        return a

    def __sub__(self, other):
        a = Amount(self)
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            a["amount"] -= other["amount"]
        else:
            a["amount"] -= float(other)
        return a

    def __mul__(self, other):
        a = Amount(self)
        if isinstance(other, Amount):
            a["amount"] *= other["amount"]
        else:
            a["amount"] *= other
        return a

    def __floordiv__(self, other):
        a = Amount(self)
        if isinstance(other, Amount):
            raise Exception("Cannot divide two Amounts")
        else:
            a["amount"] //= other
        return a

    def __div__(self, other):
        a = Amount(self)
        if isinstance(other, Amount):
            raise Exception("Cannot divide two Amounts")
        else:
            a["amount"] /= other
        return a

    def __mod__(self, other):
        a = Amount(self)
        if isinstance(other, Amount):
            a["amount"] %= other["amount"]
        else:
            a["amount"] %= other
        return a

    def __pow__(self, other):
        a = Amount(self)
        if isinstance(other, Amount):
            a["amount"] **= other["amount"]
        else:
            a["amount"] **= other
        return a

    def __iadd__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            self["amount"] += other["amount"]
        else:
            self["amount"] += other
        return self

    def __isub__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            self["amount"] -= other["amount"]
        else:
            self["amount"] -= other
        return self

    def __imul__(self, other):
        if isinstance(other, Amount):
            self["amount"] *= other["amount"]
        else:
            self["amount"] *= other
        return self

    def __idiv__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            return self["amount"] / other["amount"]
        else:
            self["amount"] /= other
            return self

    def __ifloordiv__(self, other):
        if isinstance(other, Amount):
            self["amount"] //= other["amount"]
        else:
            self["amount"] //= other
        return self

    def __imod__(self, other):
        if isinstance(other, Amount):
            self["amount"] %= other["amount"]
        else:
            self["amount"] %= other
        return self

    def __ipow__(self, other):
        self["amount"] **= other
        return self

    def __lt__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            return self["amount"] < other["amount"]
        else:
            return self["amount"] < float(other or 0)

    def __le__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            return self["amount"] <= other["amount"]
        else:
            return self["amount"] <= float(other or 0)

    def __eq__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            return self["amount"] == other["amount"]
        else:
            return self["amount"] == float(other or 0)

    def __ne__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            return self["amount"] != other["amount"]
        else:
            return self["amount"] != float(other or 0)

    def __ge__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            return self["amount"] >= other["amount"]
        else:
            return self["amount"] >= float(other or 0)

    def __gt__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            return self["amount"] > other["amount"]
        else:
            return self["amount"] > float(other or 0)

    __repr__ = __str__
    __truediv__ = __div__
    __truemul__ = __mul__


if __name__ == "__main__":
    a = Amount("2 SBD")
    b = Amount("9 SBD")
    print(a + b)
    print(b)
    b **= 2
    b += .5
    print(b)
    print(b > a)

    c = Amount("100 STEEM")
    print(c * .10)

    # print(a + c)
    # print(a < c)
