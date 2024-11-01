import pytest

from pyudunits2._udunits2_xml_parser import UnitSystem, read_all


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
