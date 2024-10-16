from __future__ import annotations

import dataclasses
import typing

if typing.TYPE_CHECKING:
    pass


@dataclasses.dataclass(frozen=True)
class Prefix:
    name: str
    # String, since it needs to be parsed, looks like '1e-3', or '.01'.
    value: str
    symbols: tuple[str, ...] = ()


@dataclasses.dataclass(frozen=True)
class Name:
    singular: str
    plural: str | None = None


@dataclasses.dataclass(frozen=True, kw_only=True)
class UnitReference:
    # A thing representing the name and symbols that can be used to reference a
    # unit
    name: Name | None = None
    symbols: tuple[str, ...] = ()

    alias_names: tuple[Name, ...] = ()
    alias_symbols: tuple[str, ...] = ()
    description: str | None = ""
