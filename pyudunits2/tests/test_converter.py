from pyudunits2 import UnitSystem
from pyudunits2._unit import Converter

import pytest


@pytest.mark.parametrize(
    ["unit_from", "unit_to", "converted_from_10"],
    [
        ["m", "m", 10],
        ["m", "km", 0.01],
        ["200 m", "km", 2.0],  # 10*200m == 2km
        ["year", "decades", 1],
        ["decades", "year", 100],
        ["centuries", "year", 1000],
        ["centuries", "decade", 100],
        ["centuries", "10 centuries", 1],
        ["(year @ 5)", "year", 15],  # Validated with udunits2.
        ["(year @ 5)*1", "year", 10],  # Validated with udunits2.
        [
            "(year @ 5)/2",
            "year",
            5,
        ],  # Validated with udunits2.  TODO: This *feels* wrong.
        ["degC", "K", 283.15],  # Validated with udunits2.
        ["degC*1", "K", 10],  # Validated with udunits2.
        ["degC/2", "K", 5],  # Validated with udunits2.
        ["lg(re degC)", "K", 1e10],  # Validated with udunits2.
        ["m", "lg(re m)", 1],  # Validated with udunits2
        ["5 m", "lg(re m)", 1.69897],  # Validated with udunits2
        ["lb(re m)", "m", 1024],  # Validated with udunits2
        ["lg(re m)", "lg(re m)", 10],
        # ["5 lg(re m)", "2 lg(re m)", 25],  # Validated with udunits2
        ["watt", "dBm", 40],  # Validated with udunits2
        ["dBm", "watt", 0.01],  # Validated with udunits2
    ],
)
def test__converter(
    simple_unit_system: UnitSystem, unit_from: str, unit_to: str, converted_from_10: int
):
    unit1 = simple_unit_system.unit(unit_from)
    unit2 = simple_unit_system.unit(unit_to)
    converter = Converter(unit1, unit2)
    # assert converter._expression._symbolic_form() == 10
    #
    # import sympy
    # m, s, from_v, to_v = sympy.symbols('m s from to')
    # a = from_v - 10 * m / s
    # sympy.solve(a, m)
    if isinstance(converted_from_10, float):
        assert converted_from_10 == pytest.approx(converter.convert(10))
    else:
        assert converter.convert(10) == converted_from_10
