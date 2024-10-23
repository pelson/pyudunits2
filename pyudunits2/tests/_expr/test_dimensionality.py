from pyudunits2 import UnitSystem


import pytest


@pytest.mark.parametrize(
    ["unit_str", "expected_dimensionality"],
    [
        ["2", {}],
        ["5·m", {"meter": 1}],
        [".1", {}],
        ["1e-2", {}],
        ["s", {"second": 1}],
        ["m per s", {"meter": 1, "second": -1}],
        ["s @ 2", {"second": 1}],
        ["(s @ 2)*1", {"second": 1}],
        ["s2*s3", {"second": 5}],
        ["lg(re year)", {"year": 1}],
        ["lg(re year/2)", {"year": 1}],
        ["2 lg(re year)", {"year": 1}],
        ["5lg(re m2)", {"meter": 2}],
        ["lb(re lg(re m2/s))", {"meter": 2, "second": -1}],
        # Century is defined in the system as "10 decade". We want to validate
        # the recursive lookup.
        ["century", {"year": 1}],
    ],
)
def test__dimensionality(
    simple_unit_system: UnitSystem,
    unit_str: str | None,
    expected_dimensionality: dict,
):
    unit = simple_unit_system.unit(unit_str)

    result = unit.dimensionality()
    # result = {basis_unit.simplest_reference: exponent for basis_unit, exponent in result.items()}
    assert result == expected_dimensionality
