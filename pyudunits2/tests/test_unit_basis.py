import pytest

from pyudunits2._expr_simplifier import Expander
from pyudunits2._udunits2_xml_parser import UnitSystem, read_all
from pyudunits2._grammar import parse
from pyudunits2 import _expr_graph as graph


@pytest.fixture(scope="module")
def unit_system() -> UnitSystem:
    return read_all()


@pytest.mark.parametrize(
    ["unit_str", "dimensionality"],
    [
        ["s", {"s": 1}],
        ["m2", {"m": 2}],
        ["m2/s", {"m": 2, "s": -1}],
        ["m2/m", {"m": 1}],
        ["m2 m", {"m": 3}],
        ["K @ 271", {"K": 1}],
        ["km2 m", {"m": 3}],
    ],
)
def test_get_basis(
    unit_system: UnitSystem, unit_str: str, dimensionality: dict
) -> None:
    # assert unit_system._names == {}

    # assert unit_system.parse('m2 s-1') == {}
    ut = unit_system.parse(unit_str)
    # print('UT:', )
    # from pprint import pprint
    # pprint(ut)

    dims = unit_system.basis_of(ut)
    result = {base._reference.symbols[0]: order for base, order in dims.items()}
    assert result == dimensionality


@pytest.mark.parametrize(
    ["unit_str", "convert_to_ut", "expected_conversion_expr"],
    [
        ["s", "s", "1"],
        ["10m", "m", "10"],
        ["m", "km", "1^-3"],
        ["km", "m", "1^3"],
        ["1000m", "km", "1^-3·1000"],
        ["minute", "hour", "60^-1"],
        ["week", "second", "604800"],
        ["week", "fortnight", "14^-1·7"],
        # ["kweek", "week", "1000"],
        ["nmile", "km", "1^-3·1852"],
        # ["degree_Celsius", "degree_fahrenheit", "1^-3·1000"],
    ],
)
def test_conversion_expr(
    unit_system: UnitSystem,
    unit_str: str,
    convert_to_ut: str,
    expected_conversion_expr: str,
) -> None:
    ut = unit_system.parse(unit_str)
    convert_to_ut = unit_system.parse(convert_to_ut)

    converter_expr = unit_system.conversion_expr(ut, convert_to_ut)
    assert str(converter_expr) == expected_conversion_expr


def idfn(param):
    return (
        str(param)
        .replace("^", "_pow_")
        .replace("·", "_mul_")
        .replace("@", "+")
        .replace(" ", "_")
    )


@pytest.mark.parametrize(
    ["unit_str", "expected_str"],
    [
        ["2^2", "2^2"],
        ["2^2·3^2", "2^2·3^2"],
        ["2^2·2^-1", "2"],
        ["s^0", "1"],
        ["s^1", "s"],
        ["s s", "s^2"],
        ["s s s", "s^3"],
        ["s^2 s", "s^3"],
        ["s^2 s^5", "s^7"],
        ["s m s", "m·s^2"],
        ["10s 20s", "200·s^2"],
        ["s^-1 s", "1"],
        ["s^-2 s^1", "s^-1"],
        ["s^-1 s^-1", "s^-2"],
        ["s^2 3s^-3", "3·s^-1"],
        ["s^2/3s^-3", "3^-1·s^-1"],
        ["(s^2)^3", "s^6"],
        ["(m s^2)^3", "m^3·s^6"],
        ["(m^-1 s^2)^3", "m^-3·s^6"],
        ["(m^-1 s^2)^3 m^3", "s^6"],
        ["(s @ 100)^2", "(s^2 @ 100^2)"],
        ["((s @ 2) @ 100)^2", "(s^2 @ 100^2·2^2)"],
        ["7·24·60·60·s/(14·24·60·60·s)", "14^-1·7"],
        # ["(s @ 2)/(3s @ 5)", "()"],
        #
        # ["(kelvin @ 273.15)/(kelvin/1.8 @ 459.67)", ""],
    ],
    ids=idfn,
)
@pytest.mark.parametrize("as_offset", [False, True])
def test_Expander(unit_str: str, expected_str: str, as_offset: bool) -> None:
    unit = parse(unit_str)
    if as_offset:
        if "@" in unit_str:
            pytest.skip(reason="Shifting a shift is not possible")
        # Check that shift behaves as expected too. We can't produce such
        # graphs with the udunits2 parser, but we can conceptually create
        # them, and expand them, and even produce a repr of them.
        unit = graph.Shift(graph.Identifier("m"), unit)
        expected_str = f"(m @ {expected_str})"
    sv = Expander()
    r = sv.visit(unit)
    assert str(r) == expected_str
