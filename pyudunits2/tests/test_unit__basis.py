from pyudunits2 import UnitSystem, BasisUnit

import pytest

from pyudunits2._unit_reference import Prefix, UnitReference, Name


from pyudunits2._unit_system import LazilyDefinedUnit


@pytest.fixture
def lg_system() -> UnitSystem:
    system = UnitSystem()

    system.add_prefix(
        Prefix(
            name="milli",
            value=".001",
            symbols=("m",),
        ),
    )

    system.add_unit(
        BasisUnit(
            reference=UnitReference(
                name=Name(singular="watt"),
                symbols=("W",),
            ),
        ),
    )

    # Add a simple unit definition.
    system.add_unit(
        LazilyDefinedUnit(
            unit_system=system,
            definition="lg(re 1 mW)",
            reference=UnitReference(
                symbols=("Bm",),
            ),
        ),
    )
    return system


# @pytest.mark.skip
# def test__unit__basis_unit__lg(lg_system: UnitSystem):
#     unit_w = lg_system.unit("watt")
#
#     unit_lg = lg_system.unit("Bm")
#
#     print(unit_lg._basis())
