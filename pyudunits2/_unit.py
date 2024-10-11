from __future__ import annotations

from ._unit_system import UnitSystem
from ._expr_graph import Node
from ._unit_reference import UnitReference


class Unit:
    def __init__(self, *, reference: UnitReference):
        self._reference = reference


class BasisUnit(Unit):
    pass


class DefinedUnit(Unit):
    # Represents a unit in a unit system.
    def __init__(
        self,
        unit_system: UnitSystem,
        unit: str,
        *,
        reference: UnitReference | None = None,
    ):
        self._unit_system = unit_system
        self._unit_raw = unit
        self._unit_graph = None
        super().__init__(reference=reference)

    @classmethod
    def from_graph(cls, unit_system: UnitSystem, unit_graph: Node):
        unit = cls(unit_system, str(unit_graph))
        unit._unit_graph = unit_graph
        return unit

    def base_form(self) -> Unit:
        from ._unit_resolver import ToBasisVisitor, IdentifierLookupVisitor

        basis_graph = ToBasisVisitor(
            IdentifierLookupVisitor(
                self._unit_system,
            ),
        ).visit(self._unit_graph)
        return type(self).from_graph(
            unit_system=self._unit_system,
            unit_graph=basis_graph,
        )
