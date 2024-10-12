from __future__ import annotations

import pathlib
import typing

from ._unit_reference import Prefix

from ._expr_graph import Node
from . import _expr_graph as unit_graph
from ._grammar import parse
from ._exceptions import UnresolvableUnitException

if typing.TYPE_CHECKING:
    from ._unit import Unit
    from ._unit_reference import UnitReference


class LazilyDefinedUnit:
    """
    A unit which has all of the necessary definitions, but which hasn't yet
    been parsed and resolved against the basis units.

    The :meth:`resolve` method may result in an exception if the definition
    is not resolvable in the given unit system.

    """

    def __init__(
        self, unit_system: UnitSystem, definition: str, reference: UnitReference
    ):
        self._unit_system = unit_system
        self._definition = definition
        self._reference = reference
        self._resolved_definition: Node | None = None

    def resolve(self) -> Unit:
        from ._unit import DefinedUnit

        if self._resolved_definition is None:
            unit_expr = parse(self._definition)

            from ._unit_resolver import IdentifierLookupVisitor

            identifier_handler = IdentifierLookupVisitor(self._unit_system)
            definition = identifier_handler.visit(unit_expr)
            # Fully resolve the unit definition all the way down to the basis.
            # basis_definition = ToBasisVisitor(identifier_handler).visit(unit_expr)

            self._resolved_definition = definition

        return DefinedUnit(
            raw_spec=self._definition,
            definition=self._resolved_definition,
            reference=self._reference,
        )


class UnitSystem:
    def __init__(
        self,
    ):
        # # https://docs.unidata.ucar.edu/udunits/current/udunits2lib.html#Unit-Systems

        # self._units = {}
        self._symbols: dict[str, Unit | LazilyDefinedUnit] = {}
        self._names: dict[str, Unit | LazilyDefinedUnit] = {}

        self._alias_names: dict[str, Unit | LazilyDefinedUnit] = {}
        self._alias_symbols: dict[str, Unit | LazilyDefinedUnit] = {}

        self._prefix_names: dict[str, Prefix] = {}
        self._prefix_symbols: dict[str, Prefix] = {}

    @classmethod
    def from_udunits2_xml(cls, path: pathlib.Path | None = None) -> UnitSystem:
        # Lazy import of the XML functionality, since it is not a
        # hard dependency.
        try:
            from ._udunits2_xml_parser import read_all
        except ImportError as err:
            raise ImportError(
                "Unable to import the pyudunits2 XML functionality. "
                "Be sure to install the pyudunits2 xml extra. "
                "For example, with 'pip install pyudunits2[xml]'"
            ) from err

        if path is None:
            # TODO: In the future we can short-circuit this to a pre-prepared
            #  unit system which was built from the udunits2 XML file.
            return read_all()
        else:
            raise NotImplementedError("Not yet able to read from another XML file")

    def add_prefix(self, prefix: Prefix):
        self._prefix_names[prefix.name] = prefix
        for symbol in prefix.symbols:
            self._prefix_symbols[symbol] = prefix

    def add_unit(self, unit: Unit | LazilyDefinedUnit) -> None:
        if unit._reference is None:
            raise ValueError("The unit {unit} has no reference")
        ref = unit._reference
        if ref.name is not None:
            if ref.name.singular in self._names:
                raise ValueError(
                    f"unit name '{ref.name.singular}' already registered in "
                    "the system"
                )
            if ref.name.plural and ref.name.plural in self._names:
                raise ValueError(
                    f"unit name '{ref.name.plural}' already registered in " "the system"
                )

        for symbol in ref.symbols:
            if symbol in self._symbols:
                raise ValueError(
                    f"unit symbol '{symbol}' already registered in the system"
                )

        if ref.name is not None:
            self._names[ref.name.singular] = unit
            if ref.name.plural:
                self._names[ref.name.plural] = unit

        for symbol in ref.symbols:
            self._symbols[symbol] = unit

        for alias in ref.alias_names:
            self._alias_names[alias.singular] = unit
            if alias.plural:
                self._alias_names[alias.plural] = unit

        for alias in ref.alias_symbols:
            self._alias_symbols[alias] = unit

    #     def get_symbol(self, symbol: str) -> SymbolPrefix:
    #         # This is case-sensitive.
    #         # TODO: Would be nice to be able to do get(symbol, None)?
    #         return self._symbols[symbol]
    #
    #     def get_name(self, name: str) -> NamePrefix:
    #         # This is case-sensitive.
    #         # TODO: Would be nice to be able to do get(symbol, None)?
    #         return self._names[name.lower()]

    def basis_of(self, unit: Node) -> dict[unit_graph.Node, float]:
        from ._dimensionality import DimensionalityCounter
        from ._unit_resolver import IdentifierLookupVisitor

        unit_in_basis_units = IdentifierLookupVisitor(self).visit(
            unit,
        )
        dimensionality_count = DimensionalityCounter().visit(
            unit_in_basis_units,
        )
        return dimensionality_count

    def conversion_expr(
        self,
        unit: unit_graph.Node,
        convert_to: unit_graph.Node,
    ) -> unit_graph.Node:  # TODO: Return something that is public API.
        from ._unit_resolver import ToBasisVisitor, IdentifierLookupVisitor
        from ._expr_simplifier import Expander

        if unit == convert_to:
            return unit_graph.Number(1)

        identifier_handler = IdentifierLookupVisitor(self)
        expr = unit_graph.Divide(unit, convert_to)
        expr = ToBasisVisitor(identifier_handler).visit(expr)
        conversion_unit = Expander().visit(expr)

        # TODO: Validate that there are no identifiers/units remaining.
        return conversion_unit

    def parse(self, unit_string: str) -> Node:
        return parse(unit_string)

    def _unit_by_name(self, name: str) -> Unit | None:
        unit = self._names.get(name, None) or self._alias_names.get(name, None)
        if isinstance(unit, LazilyDefinedUnit):
            unit = unit.resolve()
        return unit

    def _unit_by_symbol(self, symbol: str) -> Unit | None:
        unit = self._symbols.get(symbol, None) or self._alias_symbols.get(symbol, None)
        if isinstance(unit, LazilyDefinedUnit):
            unit = unit.resolve()
        return unit

    def unit_by_name_or_symbol(self, name_or_symbol: str) -> tuple[Prefix | None, Unit]:
        # Looks up a referencable unit from the system. This does not do any
        # parsing, for that use the `unit` method.
        # Instead, this method is designed to look up a specific referencable unit,
        # optionally with a prefix. For example "km", "hours", etc.
        no_prefix = None
        result: tuple[Prefix | None, Unit] | None = None

        if unit := self._unit_by_name(name_or_symbol):
            result = no_prefix, unit

        elif unit := self._unit_by_symbol(name_or_symbol):
            result = no_prefix, unit

        if result is None:
            for prefix_name, prefix in self._prefix_names.items():
                if name_or_symbol.startswith(prefix_name):
                    unit = self._unit_by_name(
                        name_or_symbol[len(prefix_name) :]
                    ) or self._unit_by_symbol(name_or_symbol[len(prefix_name) :])
                    if unit:
                        result = prefix, unit
                        break

        if result is None:
            for prefix_symbol, prefix in self._prefix_symbols.items():
                if name_or_symbol.startswith(prefix_symbol):
                    unit = self._unit_by_name(
                        name_or_symbol[len(prefix_symbol) :]
                    ) or self._unit_by_symbol(name_or_symbol[len(prefix_symbol) :])
                    if unit:
                        result = prefix, unit
                        break

        if result is None:
            raise UnresolvableUnitException(
                f"Unable to convert the identifier '{name_or_symbol}' into a unit "
                "in the unit system"
            )
        return result

    def unit(self, unit: str) -> Unit:
        unit_expr = parse(unit)
        from ._unit import DefinedUnit
        from ._unit_resolver import ToBasisVisitor, IdentifierLookupVisitor

        identifier_handler = IdentifierLookupVisitor(self)
        # Do a non-recursive lookup of identifiers in the given unit.
        expression = ToBasisVisitor(identifier_handler).visit(unit_expr)

        result = DefinedUnit(raw_spec=unit, definition=expression)
        return result
