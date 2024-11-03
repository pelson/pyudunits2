from pyudunits2 import Unit, BasisUnit
from pyudunits2._unit_reference import Name
from pyudunits2._unit import Names
import pytest
from pyudunits2._grammar import parse
from pyudunits2._expr.atoms import ExtractIdentifiers


class SimpleUnit(Unit):
    """
    A unit in which all identifiers in the expression are treated as basis units.
    """

    def __init__(self, expression: str):
        definition = parse(expression)
        identifiers = ExtractIdentifiers().visit(definition)
        super().__init__(
            definition=definition,
            identifier_references={
                identifier: BasisUnit(
                    names=Names(name=Name(singular=identifier.content)),
                )
                for identifier in identifiers
            },
        )


@pytest.mark.parametrize(
    ["lhs", "rhs", "expectation"],
    [
        [SimpleUnit("a"), SimpleUnit("a"), True],
        [SimpleUnit("a"), SimpleUnit("2a"), False],
        [SimpleUnit("2a"), SimpleUnit("a 2"), True],
        [SimpleUnit("lg(re m)"), SimpleUnit("lg(re m)"), True],
        [SimpleUnit("2 lg(re m)"), SimpleUnit("lg(re m)"), False],
        [SimpleUnit("7 days"), SimpleUnit("week"), False],
    ],
)
def test_unit__eq(lhs: Unit, rhs: Unit, expectation: str):
    assert (lhs == rhs) is expectation
    assert (rhs == lhs) is expectation
