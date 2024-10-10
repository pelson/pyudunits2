from ._baseless_unit import BaseUnit, Prefix
from ._expr_graph import Node
from . import _expr_graph as unit_graph
from ._unit_resolver import ToBasisVisitor, IdentifierLookupVisitor
from ._expr_simplifier import Expander
from ._dimensionality import DimensionalityCounter


class UnitSystem:
    def __init__(
        self,
    ):
        # # https://docs.unidata.ucar.edu/udunits/current/udunits2lib.html#Unit-Systems

        # self._units = {}
        self._symbols: dict[str, BaseUnit] = {}
        self._names: dict[str, BaseUnit] = {}

        self._alias_names: dict[str, BaseUnit] = {}
        self._alias_symbols: dict[str, BaseUnit] = {}

        self._prefix_names: dict[str, Prefix] = {}
        self._prefix_symbols: dict[str, Prefix] = {}

    def add_prefix(self, prefix: Prefix):
        self._prefix_names[prefix.name] = prefix
        for symbol in prefix.symbols:
            self._prefix_symbols[symbol] = prefix

    def add_unit(self, unit: BaseUnit) -> None:
        if unit.name is not None:
            if unit.name.singular in self._names:
                raise ValueError(
                    f"unit name '{unit.name.singular}' already registered in "
                    "the system"
                )
            if unit.name.plural and unit.name.plural in self._names:
                raise ValueError(
                    f"unit name '{unit.name.plural}' already registered in "
                    "the system"
                )

        for symbol in unit.symbols:
            if symbol in self._symbols:
                raise ValueError(
                    f"unit symbol '{symbol}' already registered in the system"
                )

        if unit.name is not None:
            self._names[unit.name.singular] = unit
            if unit.name.plural:
                self._names[unit.name.plural] = unit

        for symbol in unit.symbols:
            self._symbols[symbol] = unit

        for alias in unit.alias_names:
            self._alias_names[alias.singular] = unit
            if alias.plural:
                self._alias_names[alias.plural] = unit

        for alias in unit.alias_symbols:
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
    ) -> unit_graph.Node:
        if unit == convert_to:
            return unit_graph.Number(1)

        identifier_handler = IdentifierLookupVisitor(self)
        # unit_in_basis_units = IdentifierLookupVisitor(self).visit(
        #     unit,
        # )
        # convert_to_unit_in_basis_units = IdentifierLookupVisitor(self).visit(
        #     convert_to,
        # )
        expr = unit_graph.Divide(unit, convert_to)
        expr = ToBasisVisitor(identifier_handler).visit(expr)
        print("EXPANDED:", str(expr))

        # pprint(expr)
        conversion_unit = Expander().visit(expr)
        # Validate that there are no identifiers/units remaining.
        print("CONVERTED:", str(conversion_unit))

        return conversion_unit

    def parse(self, unit_string: str) -> Node:
        from ._grammar import parse

        return parse(unit_string)
        # for node in parsed_unit.children():
        #
        # visitor = IdentifierLookupVisitor(self)
        # return visitor.visit(parsed_unit)
        # print(type(parsed_unit))
        # print('PARSE:', parsed_unit)

    def identify(self, identifier: str) -> Node:
        """Find the unit given the name or symbol identifier"""
        if identifier in self._names:
            return self._names[identifier]
        if identifier in self._symbols:
            return self._symbols[identifier]
        raise ValueError(
            f"Identifier '{identifier}' not found in the unit system"
        )
