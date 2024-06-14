from unittest import TestCase

from utils import neg, bin_fixed_width


class TestUtils(TestCase):
    def test_neg(self):
        value = 100
        res, carry = neg(bin_fixed_width(value), 0)
        a=1
