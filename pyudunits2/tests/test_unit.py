from pyudunits2 import Unit
from pyudunits2._unit import SimpleUnit
import pytest


@pytest.mark.parametrize(
    ["lhs", "rhs", "expectation"],
    [
        [SimpleUnit("a"), SimpleUnit("a"), True],
        [SimpleUnit("a"), SimpleUnit("2a"), False],
        [SimpleUnit("2a"), SimpleUnit("a 2"), True],
        [SimpleUnit("lg(re m)"), SimpleUnit("lg(re m)"), True],
        [SimpleUnit("7 days"), SimpleUnit("week"), False],
    ],
)
def test_unit__eq(lhs: Unit, rhs: Unit, expectation: str):
    assert (lhs == rhs) is expectation
    assert (rhs == lhs) is expectation
