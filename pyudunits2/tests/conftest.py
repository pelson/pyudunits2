import pytest

from pyudunits2 import UnitSystem, BasisUnit
from pyudunits2._unit_reference import UnitReference, Prefix, Name
from pyudunits2._unit_system import LazilyDefinedUnit


@pytest.fixture
def simple_unit_system() -> UnitSystem:
    # A unit system with meters, seconds, minutes, hours, and centi & kilo
    # meter prefixes. Symbols k, c, m, s, min, hr.
    system = UnitSystem()

    system.add_prefix(
        Prefix(
            name="milli",
            value=".001",
            symbols=("m",),
        ),
    )

    system.add_prefix(
        Prefix(
            "deci",
            value="10",
            symbols=("d",),
        ),
    )

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
            names=UnitReference(
                name=Name(singular="meter", plural="meters"),
                symbols=("m",),
                alias_names=(Name(singular="metre", plural="metres"),),
            ),
        ),
    )

    system.add_unit(
        BasisUnit(
            names=UnitReference(
                name=Name(singular="second", plural="seconds"),
                symbols=("s",),
            ),
            is_time_unit=True,
        ),
    )

    # Add a simple unit definition.
    system.add_unit(
        LazilyDefinedUnit(
            unit_system=system,
            definition="60 seconds",
            names=UnitReference(
                name=Name(singular="minute", plural="minutes"),
                symbols=("min",),
            ),
        ),
    )

    # Add a unit definition which relies on another unit definition.
    system.add_unit(
        LazilyDefinedUnit(
            unit_system=system,
            definition="60 minutes",
            names=UnitReference(
                name=Name(singular="hour", plural="hours"),
                symbols=("h",),
            ),
        ),
    )

    system.add_unit(
        BasisUnit(
            names=UnitReference(
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
            names=UnitReference(
                symbols=("Bm",),
            ),
        ),
    )

    system.add_unit(
        BasisUnit(
            names=UnitReference(
                name=Name(singular="year"),
            ),
        ),
    )

    # Add a simple unit definition.
    system.add_unit(
        LazilyDefinedUnit(
            unit_system=system,
            definition="10 year",
            names=UnitReference(
                name=Name(singular="decade", plural="decades"),
            ),
        ),
    )

    system.add_unit(
        LazilyDefinedUnit(
            unit_system=system,
            definition="10 decade",
            names=UnitReference(
                name=Name(singular="century", plural="centuries"),
            ),
        ),
    )

    # Add a temperature unit definition.
    system.add_unit(
        BasisUnit(
            names=UnitReference(name=Name(singular="kelvin"), symbols=("K",)),
        ),
    )

    system.add_unit(
        LazilyDefinedUnit(
            unit_system=system,
            definition="K @ 273.15",
            names=UnitReference(
                name=Name(singular="degC"),
            ),
        ),
    )

    return system
