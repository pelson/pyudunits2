from __future__ import annotations

from ._expr_graph import Node
from ._unit_reference import UnitReference


class Unit:
    def __init__(self, *, reference: UnitReference | None):
        self._reference = reference

    def convertible_to(self, other: Unit) -> bool:
        # For basis units, and those without a unit system, the only units
        # which are convertible are those which are equal.
        return self == other


class BasisUnit(Unit):
    pass


class DefinedUnit(Unit):
    # Represents a well-defined unit with comparable basis.
    # Note that a LazilyDefinedUnit exists if you do not want to resolve the
    # basis expression upfront.
    def __init__(
        self,
        raw_spec: str,  # The requested form of the unit.
        definition: Node,  # The fully resolved (basis form) definition of this unit.
        *,
        reference: UnitReference | None = None,
    ):
        self._definition = definition
        self._unit_raw = raw_spec
        self._unit_graph = None
        super().__init__(reference=reference)

    def base_form(self) -> Unit:
        # TODO: Return Unit
        # TODO: Resolve the terms, and canonicalise the name/symbols.
        return self._definition

    def convertible_to(self, other: Unit) -> bool:
        raise NotImplementedError("TODO")

    def __str__(self):
        return self._unit_raw

    def __repr__(self):
        return (
            f"DefinedUnit(raw_spec={self._unit_raw}, definition={self._definition}, "
            f"reference={self._reference})"
        )

    def __eq__(self, other):
        if type(other) is not DefinedUnit:
            return NotImplemented

        # TODO: Get the base form to compare __eq__ on simplified form.
        return other.base_form() == self.base_form()
