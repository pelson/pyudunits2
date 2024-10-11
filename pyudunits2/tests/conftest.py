import pytest

from pyudunits2 import UnitSystem, BasisUnit, DefinedUnit
from pyudunits2._unit_reference import UnitReference, Prefix, Name


@pytest.fixture
def simple_unit_system() -> UnitSystem:
    # A unit system with meters, seconds, minutes, hours, and centi & kilo
    # meter prefixes. Symbols k, c, m, s, min, hr.
    system = UnitSystem()

    system.add_prefix(
        Prefix(
            "kilo",
            value="1000",
            symbols=("k",),
        ),
    )

    system.add_prefix(
        Prefix(
            "centi",
            value="100",
            symbols=("c",),
        ),
    )

    system.add_unit(
        BasisUnit(
            reference=UnitReference(
                name=Name(singular="meter", plural="meters"),
                symbols=("m",),
            ),
        ),
    )

    system.add_unit(
        BasisUnit(
            reference=UnitReference(
                name=Name(singular="second", plural="seconds"),
                symbols=("s",),
            ),
        ),
    )

    # Add a simple unit definition.
    system.add_unit(
        DefinedUnit(
            unit_system=system,
            unit="60 seconds",
            reference=UnitReference(
                name=Name(singular="minute", plural="minutes"),
                symbols=("min",),
            ),
        ),
    )

    # Add a unit definition which relies on another unit definition.
    system.add_unit(
        DefinedUnit(
            unit_system=system,
            unit="60 minutes",
            reference=UnitReference(
                name=Name(singular="hour", plural="hours"),
                symbols=("hr",),
            ),
        ),
    )

    return system
