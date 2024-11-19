import pytest

from pyudunits2._udunits2_xml_parser import UnitSystem, read_all
from pyudunits2 import DateUnit


@pytest.fixture(scope="module")
def unit_system() -> UnitSystem:
    # Use the real UDUNITS2 XML file to validate the parsing.
    # In general, outside of this test module, we should use a simpler
    # unit system form (see conftest.py::simple_unit_system).
    return read_all()


@pytest.mark.parametrize(
    ["unit_str", "equivalent_to"],
    [
        ["meters", "m"],  # Not explicitly mentioned. Plural of the name.
        ["metres", "m"],  # Not explicitly mentioned. Plural of the alias.
        ["inches", "inch"],  # Not explicitly mentioned. Plural of the alias.
    ],
)
def test__unit__well_known(
    unit_system: UnitSystem,
    unit_str: str,
    equivalent_to: str,
):
    unit = unit_system.unit(unit_str)
    equivalence = unit_system.unit(equivalent_to)
    assert equivalence == unit


@pytest.mark.parametrize(
    ["unit_str", "expected_dimensionality"],
    [
        ["radian", {}],
        ["radian meters", {"meter": 1}],
        ["feet", {"meter": 1}],
        ["inches", {"meter": 1}],  # The inches plural form is not in the XML file.
    ],
)
def test__unit__dimensionless(
    unit_system: UnitSystem,
    unit_str: str,
    expected_dimensionality: dict,
):
    unit = unit_system.unit(unit_str)
    result = unit.dimensionality()
    result = {unit._ref: order for unit, order in result.items()}
    assert result == expected_dimensionality
    if not expected_dimensionality:
        assert unit.is_dimensionless()
    else:
        assert not unit.is_dimensionless()


@pytest.mark.parametrize(
    ["unit_str", "has_time_unit"],
    [
        ["s", True],
        ["m", False],
        ["m/s", True],
        ["years", True],
        ["m @ 20", False],
        ["hr @ 20", True],  # A udunits date
        ["seconds since 2000-01-01T00:00 UTC", True],
        ["light_year", False],
        ["eon", True],
        ["s2/s", True],
        ["s/s", False],
    ],
)
def test__unit__has_time_unit(
    unit_system: UnitSystem,
    unit_str: str,
    has_time_unit: dict,
):
    unit = unit_system.unit(unit_str)
    if isinstance(unit, DateUnit):
        # If we have a date unit, it is a time unit.
        # There is no special method for this.
        assert has_time_unit is True
    else:
        assert unit.has_time_unit() is has_time_unit
