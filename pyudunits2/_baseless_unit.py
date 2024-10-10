"""
Representation of units without any unit system.

Such a concept does not represent what you would consider a useful unit... you
can't compare things like "m == meters", and you can't convert "km to m", since
there is no basis definition (unit system) to understand the abstract terms.

"""
from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class Prefix:
    name: str
    # String, since it needs to be parsed, looks like '1e-3', or '.01'.
    value: str
    symbols: tuple[str, ...] = ()


@dataclasses.dataclass(frozen=True)
class Name:
    singular: str
    plural: str | None


@dataclasses.dataclass(frozen=True)
class BaseUnit:
    # A unit which is a basis in the unit system
    name: Name | None = None
    symbols: tuple[str, ...] = ()

    alias_names: tuple[Name, ...] = ()
    alias_symbols: tuple[str, ...] = ()
    description: str | None = ""

    def __str__(self):
        # Pick the first representation that is suitable.
        if self.name:
            return self.name.singular
        for symbol in self.symbols:
            return symbol


@dataclasses.dataclass(frozen=True)
class DerivedUnit(BaseUnit):
    base_unit_definition: str = ""  # Has a default for subclassing reasons...
