from pyudunits2 import UnitSystem, DefinedUnit, UnresolvableUnitException
import pytest


def test__unit__basis_unit(simple_unit_system: UnitSystem):
    unit = simple_unit_system.unit("m")
    assert isinstance(unit, DefinedUnit)
    assert unit._unit_raw == "m"
    # TODO: The basis should be exactly the one defined in the system.
    # assert unit.basis_expr() == system._names['meters']


@pytest.mark.parametrize(
    "unit_str",
    [
        "km",
        "kmetres",
        "kilom",
    ],
)
def test__unit__prefix_plural(simple_unit_system: UnitSystem, unit_str: str):
    # We have a non defined plural name, with a symbol based prefix.
    unit = simple_unit_system.unit(unit_str)
    assert isinstance(unit, DefinedUnit)
    assert unit._unit_raw == unit_str


def test__unit__undefined_unit(simple_unit_system: UnitSystem):
    match = r"Unable to convert the identifier 'other' into a unit in the unit system"
    with pytest.raises(UnresolvableUnitException, match=match):
        simple_unit_system.unit("other")
