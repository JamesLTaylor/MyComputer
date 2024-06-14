from unittest import TestCase

from utils import neg, bin_fixed_width, bin_to_value


class TestUtils(TestCase):
    def test_neg_8(self):
        value = 100
        res, carry = neg(bin_fixed_width(value), 0)
        test = bin_to_value(res)
        self.assertEquals(156, test)
        self.assertEquals(1, carry)

    def test_neg_16(self):
        value = 1000
        bits16 = bin_fixed_width(value, 16)
        res0, carry0 = neg(bits16[8:], 0)
        res1, carry1 = neg(bits16[:8], carry0)
        test = bin_to_value(res0) + 256 * bin_to_value(res1)
        self.assertEquals(64536, test)
        self.assertEquals(1, carry0)
        self.assertEquals(1, carry1)

    def test_neg_0(self):
        value = 0
        res, carry = neg(bin_fixed_width(value), 0)
        test = bin_to_value(res)
        self.assertEquals(0, test)
        self.assertEquals(0, carry)

