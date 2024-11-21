from pyudunits2 import Unit, BasisUnit, DateUnit
from pyudunits2._unit_reference import Name
from pyudunits2._unit import Names, _unit_from_expression_and_identifiers
import pytest
from pyudunits2._grammar import parse
from pyudunits2._expr.atoms import ExtractIdentifiers
import pyudunits2._expr.graph as graph


@pytest.fixture
def common_id_refs():
    return {
        graph.Identifier("s"): BasisUnit(
            names=Names(name=Name(singular="s")),
            is_time_unit=True,
        ),
        graph.Identifier("years"): BasisUnit(
            names=Names(name=Name(singular="year", plural="years")),
            is_time_unit=True,
        ),
        graph.Identifier("m"): BasisUnit(
            names=Names(name=Name(singular="m")),
        ),
    }


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


@pytest.mark.parametrize(
    ["expr", "error_msg"],
    [
        ["s @ 2000", "Refusing to represent dates"],
        ["100s @ 2000", "Refusing to represent dates"],
        ["years since 2000-01-01T00:00", "Refusing to represent dates"],
        # If we do anything with the date, it isn't a date in udunits2, but we still reject it as a unit.
        ["m (s @ 2000)", "Refusing to represent dates"],
        # We could abuse the syntax and try to shift by a non time based unit too... this is rejected
        # by udunits2.
        ["m @ 2000-01-01T00:00", "Normalisation of non-numeric shift not possible"],
        ["(m/m) s @ 2000-01-01T00:00", "Refusing to represent dates"],
    ],
)
def test_unit__init_with_date(expr: str, error_msg: str, common_id_refs):
    definition = parse(expr)
    with pytest.raises(ValueError, match=error_msg):
        Unit(
            definition=definition,
            identifier_references=common_id_refs,
        )


@pytest.mark.parametrize(
    ["unit_expr", "expected_ref"],
    [
        ["s @ 2000", "2000"],
        ["s @ 2000 +10 UTC", "2000 +10 UTC"],
        ["100s @ 2000", "2000"],
        ["years since 2000-01-01T00:00", "2000-01-01T00:00"],
        [
            # Maybe we don't want to support this...
            "(m/m) s @ 2000-01-01T00:00",
            "2000-01-01T00:00",
        ],
    ],
)
def test_dateunit__reference_date(unit_expr: str, expected_ref, common_id_refs):
    definition = parse(unit_expr)
    date_unit = _unit_from_expression_and_identifiers(
        definition, identifier_references=common_id_refs
    )
    assert isinstance(date_unit, DateUnit)
    assert isinstance(date_unit.reference_date, graph.Unhandled)
    # TODO: get this assertion to be true.
    # assert isinstance(date_unit.reference_date, DateTime)
    assert str(date_unit.reference_date) == expected_ref
