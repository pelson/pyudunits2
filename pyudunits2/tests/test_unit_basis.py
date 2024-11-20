import pytest

from pyudunits2._expr.expander import Expander
from pyudunits2._udunits2_xml_parser import UnitSystem, read_all
from pyudunits2._grammar import parse
from pyudunits2._expr import graph as graph


# TODO: Is all of this now obsolete with the use of sympy?


@pytest.fixture(scope="module")
def unit_system() -> UnitSystem:
    return read_all()


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
