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
        # [
        #     Unit(Expression.from_raw('7 days'), reference=UnitReference(symbols=('week', ))),
        #     SimpleUnit("week"),
        #     True,
        # ],
    ],
)
def test_unit__eq(lhs: Unit, rhs: Unit, expectation: str):
    print(lhs._expression._symbolic_form())
    print(lhs._expression.expression)
    print(rhs._expression._symbolic_form())
    print(rhs._expression.expression)
    assert (lhs == rhs) is expectation
    assert (rhs == lhs) is expectation


@pytest.mark.parametrize(
    ["lhs", "rhs", "expectation"],
    [
        [SimpleUnit("lg(re m)"), SimpleUnit("lg(re m)"), True],
    ],
)
def test_unit__eq__fail(lhs: Unit, rhs: Unit, expectation: str):
    # expr = lhs.conversion_expr(rhs)
    assert lhs == rhs
