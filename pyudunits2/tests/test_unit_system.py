import contextlib

from pyudunits2 import UnitSystem, UnresolvableUnitException
from pyudunits2._unit import Unit, DateUnit
import pytest


@pytest.mark.parametrize(
    ["unit_spec", "definition"],
    [
        ["m", "meter"],
        ["Bm", "(lg(re 1·0.001·watt))"],
        ["1e-3 Bm", "0.001·(lg(re 1·0.001·watt))"],
        ["mBm", "0.001·(lg(re 1·0.001·watt))"],
        ["km", "1000·meter"],
        ["m 1000", "meter·1000"],  # The definition isn't fully normalised (yet).
        ["kmetres", "1000·meter"],
        ["kilom", "1000·meter"],
    ],
)
def test__unit__expansion(
    simple_unit_system: UnitSystem, unit_spec: str, definition: str
):
    # We have a non defined plural name, with a symbol based prefix.
    unit = simple_unit_system.unit(unit_spec)
    assert isinstance(unit, Unit)
    # TODO: Fix this.
    assert str(unit.expanded()) == definition


@pytest.mark.parametrize(
    "unit_spec",
    [
        "other",
        "deci",  # A valid prefix in the unit system.
    ],
)
def test__unit__undefined_unit(simple_unit_system: UnitSystem, unit_spec):
    match = rf"Unable to convert the identifier '{unit_spec}' into a unit in the unit system"
    with pytest.raises(UnresolvableUnitException, match=match):
        simple_unit_system.unit(unit_spec)


@pytest.mark.parametrize(
    ["unit_lhs", "unit_rhs"],
    [
        ["km", "1000 m"],
    ],
)
def test__unit__symbolic_eq(
    simple_unit_system: UnitSystem, unit_lhs: str, unit_rhs: str
):
    # We have a non defined plural name, with a symbol based prefix.
    unit1 = simple_unit_system.unit(unit_lhs)
    unit2 = simple_unit_system.unit(unit_rhs)

    assert unit1 == unit2


no_exception = contextlib.nullcontext()


@pytest.mark.parametrize(
    ["unit_expr", "expectation"],
    [
        ["s @ 2000", no_exception],
        ["hours since 2000-01-01T00:00", no_exception],
        ["kilohours since 2000-01-01T00:00", no_exception],
        # If we do anything with the date, it isn't a date in udunits2, but we still reject it as a unit.
        ["m (s @ 2000)", pytest.raises(ValueError, match="...")],
        # We could abuse the syntax and try to shift by a non time based unit too... this is rejected
        # by udunits2.
        ["m @ 2000-01-01T00:00", pytest.raises(ValueError, match="...")],
        ["(m/m) s @ 2000-01-01T00:00", no_exception],  # Normalises to a date.
        ["(1000) s @ 2000-01-01T00:00", no_exception],
        ["(m/hr) s @ 2000-01-01T00:00", pytest.raises(ValueError, match="...")],
    ],
)
def test__unit__date_unit(simple_unit_system: UnitSystem, unit_expr: str, expectation):
    with expectation:
        unit = simple_unit_system.unit(unit_expr)
        assert isinstance(unit, DateUnit)
