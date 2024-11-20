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
        ["decimeter", {"meter": 1}],
        ["m per s", {"meter": 1, "second": -1}],
        ["m per meter", {}],
        ["m meter", {"meter": 2}],
        ["(m2)^-3", {"meter": -6}],
        ["(m2)*meter-3", {"meter": -1}],
        ["(m2)^-3*meter", {"meter": -5}],
        ["s @ 2", {"second": 1}],
        ["(m @ 2)*1", {"meter": 1}],
        ["s2*s3", {"second": 5}],
        ["lg(re year)", {"year": 1}],
        ["lg(re year/2)", {"year": 1}],
        ["2 lg(re year)", {"year": 1}],
        ["5lg(re m2)", {"meter": 2}],
        ["lb(re lg(re m2/s))", {"meter": 2, "second": -1}],
        # Century is defined in the system as "10 decade". We want to validate
        # the recursive lookup.
        ["century", {"year": 1}],
        ["century^-2", {"year": -2}],
        ["century^2 year^-1", {"year": 1}],
        ["century^2 year^-3", {"year": -1}],
        ["(century^2)^-3", {"year": -6}],
        ["(century^2)^-3*year", {"year": -5}],
    ],
)
def test__dimensionality(
    simple_unit_system: UnitSystem,
    unit_str: str,
    expected_dimensionality: dict,
):
    unit = simple_unit_system.unit(unit_str)

    result = unit.dimensionality()
    # result = {str(base_unit): order for base_unit, order in result.items()}
    # result = {basis_unit.simplest_reference: exponent for basis_unit, exponent in result.items()}
    assert result == expected_dimensionality

    if not expected_dimensionality:
        assert unit.is_dimensionless()
    else:
        assert not unit.is_dimensionless()
