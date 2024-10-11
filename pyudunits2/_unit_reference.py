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
    plural: str | None


@dataclasses.dataclass(frozen=True, kw_only=True)
class UnitReference:
    name: Name | None = None
    symbols: tuple[str, ...] = ()

    alias_names: tuple[Name, ...] = ()
    alias_symbols: tuple[str, ...] = ()
    description: str | None = ""
