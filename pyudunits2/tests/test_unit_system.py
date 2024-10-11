from pyudunits2 import UnitSystem, DefinedUnit, UnresolvableUnitException
import pytest


def test__unit__basis_unit(simple_unit_system: UnitSystem):
    system = simple_unit_system
    unit = system.unit("m")
    assert isinstance(unit, DefinedUnit)
    assert unit._unit_raw == "m"
    # TODO: The basis should be exactly the one defined in the system.
    # assert unit.basis_expr() == system._names['meters']


def test__unit__defined_unit(simple_unit_system: UnitSystem):
    system = simple_unit_system
    unit = system.unit("km")
    assert isinstance(unit, DefinedUnit)
    assert unit._unit_raw == "km"


def test__unit__undefined_unit(simple_unit_system: UnitSystem):
    system = simple_unit_system
    match = r"Unable to convert the identifier 'other' into a unit in the unit system"
    with pytest.raises(UnresolvableUnitException, match=match):
        system.unit("other")
