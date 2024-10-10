from __future__ import annotations

# Gold dust. https://github.com/Unidata/MetPy/issues/1362
import contextlib
import dataclasses
import logging
import typing
from pathlib import Path

from lxml import etree

from ._grammar import graph as unit_graph
from ._grammar.graph import Identifier, Node, Visitor

_log = logging.getLogger(__name__)
XML_path = Path(__file__).parent / "udunits2_combined.xml"


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
class MagnitudePrefix:
    value: float

    name: Name | None

    symbols: tuple[str, ...] = ()

    alias_names: tuple[Name, ...] = ()
    alias_symbols: tuple[str, ...] = ()


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


@dataclasses.dataclass(frozen=True)
class SpecifiedUnit(BaseUnit):
    unit_spec: Node = None


# @dataclasses.dataclass(frozen=True)
# class NamePrefix:
#     prefix: str
#     value: float
#
#
# @dataclasses.dataclass(frozen=True)
# class SymbolPrefix:
#     prefix: str
#     value: float
#
#
#


class UnitNode(Identifier):
    content: BaseUnit


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


class DimensionalityCounter(Visitor):
    if typing.TYPE_CHECKING:

        def visit(self, node: Node) -> dict[unit_graph.Node, float]:
            pass

    def generic_visit(self, node: unit_graph.Node):
        raise NotImplementedError(f"Not implemented for {type(node)}")

    def visit_Number(self, node: unit_graph.Identifier):
        return {}

    def visit_Identifier(self, node: unit_graph.Identifier):
        return {node.content: 1}

    def visit_UnitNode(self, node: unit_graph.UnitNode):
        return {node.content: 1}

    def visit_Multiply(self, node: unit_graph.Multiply):
        scope = self.visit(node.lhs)
        for ut, order in self.visit(node.rhs).items():
            scope[ut] = scope.get(ut, 0) + order
        return scope

    def visit_Divide(self, node: unit_graph.Divide):
        scope = self.visit(node.lhs)
        rhs_scope = self.visit(node.rhs)
        for ut, order in rhs_scope.items():
            scope[ut] = scope.get(ut, 0) - order
        return scope

    def visit_Raise(self, node: unit_graph.Raise):
        assert isinstance(node.rhs, unit_graph.Number)
        scope = self.visit(node.lhs)
        for ut in scope:
            scope[ut] += node.rhs.content - 1
        return scope

    def visit_Shift(self, node: unit_graph.Shift):
        # We can drop the shift value when doing dimensionality analysis.
        return self.visit(node.unit)


class ChainedExpr:
    # Represents 2 or more multiplications raised to a numeric power.
    def __init__(self):
        self._chain: list[tuple[unit_graph.Terminal, int]] = []

    def add_term(self, term: unit_graph.Terminal, raised_to: int) -> None:
        self._chain.append((term, raised_to))

    def terms(self) -> unit_graph.Node:
        # Sort the expression chain by contents that can potentially be
        # combined.
        t = sorted(
            self._chain,
            key=lambda item: (
                str(type(item[0].content)),
                str(item[0].content),
            ),
            reverse=True,
        )
        terms = []

        # Iterate over each of the nodes, and try to combine with the previous
        # one.
        for node, raised_to in t[::-1]:
            term = node
            if raised_to == 0:
                continue
            elif raised_to != 1:
                term = unit_graph.Raise(node, unit_graph.Number(raised_to))

            if terms:
                last_term = terms[-1]
            else:
                # There is nothing to combine with, so let's move to the
                # next term.
                terms.append(term)
                continue

            # Try to combine this node with the previous one.

            if (
                isinstance(last_term, unit_graph.Terminal)
                and last_term == node
            ):
                # a · a^n == a^(n+1)

                # We can combine the two terms, so pop the last one.
                assert terms.pop() is last_term
                new_exponent = raised_to + 1
                if new_exponent == 0:
                    # Both terms have cancelled out to 1. We don't need any
                    # terms to represent this.
                    _log.debug(
                        'Combined form "a · a^n"; '
                        f"Expr: {last_term} · {node}^{raised_to} == 1"
                    )
                    continue
                else:
                    new_term = unit_graph.Raise(
                        node,
                        unit_graph.Number(new_exponent),
                    )
                _log.debug(
                    'Combined form "a · a^n"; '
                    f"Expr: {last_term} · {node}^{raised_to} == {new_term}"
                )
                terms.append(new_term)

            elif (
                isinstance(last_term, unit_graph.Terminal)
                and isinstance(last_term, unit_graph.Number)
                and isinstance(node, unit_graph.Number)
                and type(node.content) is type(last_term.content)
                and isinstance(raised_to, int)
                and raised_to > 0
            ):
                # a · b^n == a*(b^n); Where a and b are numbers of the same
                #                     type (float / int)

                # We can combine the two terms, so pop the last one.
                assert terms.pop() is last_term
                print("S:", type(node.content), node.content)
                print("N:", node)
                new_term = unit_graph.Number(
                    last_term.content * (node.content**raised_to)
                )
                _log.debug(
                    'Combined form "a · b^n"; '
                    f"Expr: {last_term} · {node}^{raised_to} == {new_term}"
                )
                terms.append(new_term)

            elif (
                isinstance(last_term, unit_graph.Raise)
                and isinstance(last_term.rhs, unit_graph.Number)
                and last_term.lhs == node
            ):
                # a^n · a^m == a^(n+m); Where n and m are numbers.

                # We can combine the two terms, so pop the last one.
                assert terms.pop() is last_term
                new_exponent = last_term.rhs.content + raised_to
                if new_exponent == 0:
                    # Both terms have cancelled out to 1. We don't need any
                    # terms to represent this.
                    _log.debug(
                        'Combined form "a^n · a^m" == a^(n+m); '
                        f"Expr: {last_term} · {node}^{raised_to} == 1"
                    )
                    continue
                elif new_exponent == 1:
                    # We don't need to raise anymore.
                    new_term = last_term.lhs
                else:
                    new_term = unit_graph.Raise(
                        node,
                        unit_graph.Number(new_exponent),
                    )
                _log.debug(
                    'Combined form "a^n · a^m == a^(n+m)"; '
                    f"Expr: {last_term} · {node}^{raised_to} == {new_term}"
                )
                terms.append(new_term)

            else:
                terms.append(term)

        result = unit_graph.Number(1)
        if len(terms) == 1:
            result = terms[0]
        elif len(terms) > 1:
            result = terms.pop()
            for term in terms[::-1]:
                result = unit_graph.Multiply(term, result)
        return result


class ToBasisVisitor(Visitor):
    def __init__(self, identifier_lookup: IdentifierLookupVisitor):
        self._identifier_lookup = identifier_lookup

    def generic_visit(self, node: Node):
        if isinstance(node, unit_graph.Terminal):
            return node
        elif isinstance(node, unit_graph.BinaryOp):
            return type(node)(self.visit(node.lhs), self.visit(node.rhs))
        else:
            raise ValueError(f"Not yet supported {type(node)}")

    def visit_Shift(self, node: unit_graph.Shift):
        return unit_graph.Shift(
            self.visit(node.unit),
            self.visit(node.shift_from),
        )

    def visit_Identifier(self, node: unit_graph.Identifier):
        return self.visit(self._identifier_lookup.visit(node))

    def visit_UnitNode(self, node: UnitNode):
        from ._grammar import parse

        if isinstance(node.content, DerivedUnit):
            # Substitute the identifiers.
            unit_expr = self._identifier_lookup.visit(
                parse(node.content.base_unit_definition),
            )
            # Now potentially expand the derived units identified
            # until there are none left.
            return self.visit(unit_expr)

        return node


class Expander(Visitor):
    def __init__(self):
        self._expansion: list[ChainedExpr] = [ChainedExpr()]
        self._offset_terms: list[ChainedExpr] = [ChainedExpr()]

    def generic_visit(self, node: unit_graph.Node):
        raise NotImplementedError(f"Not implemented for {type(node)}")

    def visit_internal(self, node):
        return super().visit(node)

    def visit(self, node):
        _ = self.visit_internal(node)
        terms = self._expansion[-1].terms()
        if self._offset_terms[-1]._chain:
            terms = unit_graph.Shift(terms, self._offset_terms[-1].terms())
        return terms

    @contextlib.contextmanager
    def expr_context(
        self,
    ) -> typing.Generator[tuple[ChainedExpr, ChainedExpr]]:
        expansion = ChainedExpr()
        offset = ChainedExpr()
        self._expansion.append(expansion)
        self._offset_terms.append(offset)
        yield expansion, offset
        self._expansion.pop()
        self._offset_terms.pop()

    def visit_Multiply(self, node: unit_graph.Multiply):
        self.visit_internal(node.lhs)
        with self.expr_context() as (expansion, offset):
            self.visit_internal(node.rhs)

        for term, raise_to in expansion._chain:
            self._expansion[-1].add_term(term, raise_to)

        for term, raise_to in offset._chain:
            # TODO: Figure out what this should be.
            self._offset_terms[-1].add_term(term, raise_to)

    def visit_Divide(self, node: unit_graph.Divide):
        self.visit_internal(node.lhs)
        with self.expr_context() as (expansion, offset):
            self.visit_internal(node.rhs)

        for term, raise_to in expansion._chain:
            self._expansion[-1].add_term(term, -raise_to)

        for term, raise_to in offset._chain:
            # TODO: Figure out what this should be.
            self._offset_terms[-1].add_term(term, raise_to)

        # expansion = ChainedExpr()
        # self._expansion.append(expansion)
        # self.visit_internal(node.rhs)
        # self._expansion.pop()
        # for term, raise_to in expansion._chain:
        #     self._expansion[-1].add_term(term, -raise_to)
        # self._expansion[-1]._offset -= expansion._offset

    def visit_UnitNode(self, node: UnitNode):
        if not isinstance(node.content, BaseUnit):
            raise ValueError("unknown type")
        return unit_graph.Identifier(node.content.name)

    def visit_Identifier(self, node: unit_graph.Identifier):
        self._expansion[-1].add_term(node, 1)

    def visit_Number(self, node: unit_graph.Number):
        self._expansion[-1].add_term(node, 1)

    def visit_Raise(self, node: unit_graph.Raise):
        with self.expr_context() as (expansion, offset):
            self.visit_internal(node.lhs)

        assert isinstance(node.rhs, unit_graph.Number)
        for term, raise_to in expansion._chain:
            self._expansion[-1].add_term(term, raise_to * node.rhs.content)
        for term, raise_to in offset._chain:
            self._offset_terms[-1].add_term(term, raise_to * node.rhs.content)

    def visit_Shift(self, node: unit_graph.Shift):
        self.visit_internal(node.unit)
        with self.expr_context() as (expansion, offset):
            self.visit_internal(node.shift_from)

        if offset._chain:
            raise ValueError("Chain:", str(offset.terms()))
        assert not offset._chain

        # Copy over the expansion into the offset.
        for term, raise_to in expansion._chain:
            # print("F:", term, raise_to)
            self._offset_terms[-1].add_term(term, raise_to)
        # self._offset_terms[-1].node.shift_from.content


class SimplifyingVisitor(Visitor):
    def visit_Divide(self, node: unit_graph.Divide):
        lhs = self.visit(node.lhs)
        rhs = self.visit(unit_graph.Raise(node.rhs, unit_graph.Number(-1)))
        return self.visit(unit_graph.Multiply(lhs, rhs))

    def generic_visit(self, node: unit_graph.Node):
        raise NotImplementedError(f"Not implemented for {type(node)}")

    def _no_op(self, node: unit_graph.Node):
        return node

    def visit(self, node: Node):
        result = self.visit_internal(node)
        # Sort and strip the result.

        return result

    def visit_internal(self, node: unit_graph.Node):
        # Like visit, except we don't simplify the final unit.
        result = super().visit(node)
        return result

    visit_Identifier = _no_op
    visit_Number = _no_op

    def visit_Multiply(self, node: unit_graph.Multiply):
        lhs = self.visit_internal(node.lhs)
        rhs = self.visit_internal(node.rhs)
        # TODO: Sort & try to combine terms if we can.

        if isinstance(lhs, unit_graph.Identifier) and isinstance(
            rhs, unit_graph.Identifier
        ):
            if lhs.content == rhs.content:
                return unit_graph.Raise(lhs, 2)
            else:
                lhs, rhs = sorted(
                    [lhs, rhs], key=lambda identifier: identifier.content
                )
                return unit_graph.Multiply(lhs, rhs)
        elif (
            isinstance(lhs, unit_graph.Identifier)
            and isinstance(rhs, unit_graph.Raise)
            and isinstance(rhs.lhs, unit_graph.Identifier)
        ):
            if lhs.content == rhs.content:
                return unit_graph.Raise(lhs, 2)
            else:
                lhs, rhs = sorted(
                    [lhs, rhs], key=lambda identifier: identifier.content
                )
                return unit_graph.Multiply(lhs, rhs)

        return unit_graph.Multiply(lhs, rhs)

    def visit_Raise(self, node: unit_graph.Raise):
        assert isinstance(node.rhs, unit_graph.Number)
        lhs = self.visit_internal(node.lhs)
        if isinstance(lhs, unit_graph.Terminal):
            return unit_graph.Raise(lhs, node.rhs)
        elif isinstance(lhs, unit_graph.Multiply):
            # Expand multiplications such (AB)^2 becomes A^2.B^2
            g = unit_graph.Multiply(
                unit_graph.Raise(self.visit_internal(lhs.lhs), node.rhs),
                unit_graph.Raise(self.visit_internal(lhs.rhs), node.rhs),
            )
            return g
        else:
            return unit_graph.Raise(self.visit_internal(lhs.lhs), node.rhs)


class IdentifierLookupVisitor(Visitor):
    # Warning: not yet recursive. See ToBasisVisitor
    def __init__(self, unit_system: UnitSystem):
        self._unit_system = unit_system
        super().__init__()

    if typing.TYPE_CHECKING:

        def visit(self, node: Node) -> unit_graph.Node:
            pass

    def generic_visit(self, node: Node):
        if isinstance(node, unit_graph.Terminal):
            return node
        elif isinstance(node, unit_graph.BinaryOp):
            return type(node)(self.visit(node.lhs), self.visit(node.rhs))
        elif isinstance(node, unit_graph.Shift):
            return unit_graph.Shift(self.visit(node.unit), node.shift_from)
        else:
            raise NotImplementedError(f"Node {type(node)} not implemented")

    def visit_Identifier(self, node: Identifier) -> Node:
        if node.content in self._unit_system._names:
            return UnitNode(self._unit_system._names[node.content])
        if node.content in self._unit_system._symbols:
            return UnitNode(self._unit_system._symbols[node.content])
        # TODO: Aliases.

        if node.content in self._unit_system._alias_names:
            return UnitNode(self._unit_system._alias_names[node.content])

        if node.content in self._unit_system._alias_symbols:
            return UnitNode(self._unit_system._alias_symbols[node.content])

        for prefix_name, prefix in self._unit_system._prefix_names.items():
            # TODO: We shouldn't strip off more than one prefix.
            #  (e.g. nautical_mile)

            if node.content.startswith(prefix_name):
                # TODO: Maybe we shouldn't match if it is a named prefix but a
                #  symbol unit e.g. kilom. The inverse also true e.g. kmeter
                return unit_graph.Multiply(
                    self._prefix_value(prefix.value),
                    self.visit(Identifier(node.content[len(prefix_name) :])),
                )
        for prefix_symbol, prefix in self._unit_system._prefix_symbols.items():
            if node.content.startswith(prefix_symbol):
                return unit_graph.Multiply(
                    self._prefix_value(prefix.value),
                    self.visit(Identifier(node.content[len(prefix_symbol) :])),
                )
        raise ValueError(
            f"Unable to convert the identifier '{node.content}' into a unit "
            "in the unit system"
        )

    def _prefix_value(self, value: str) -> unit_graph.Node:
        if "e" in value:
            number, _, exponent = value.partition("e")
            if "." in number:
                number = float(number)
            else:
                number = int(number)

            if "." in exponent:
                exponent = float(exponent)
            else:
                exponent = int(exponent)

            return unit_graph.Raise(
                unit_graph.Number(number),
                unit_graph.Number(exponent),
            )
        else:
            if "." in value:
                number = float(value)
            else:
                number = int(value)
            return unit_graph.Number(number)


@dataclasses.dataclass
class Tag:
    # A mutable representation of an XML tag.
    # We drop the namespace intentionally - it has no value in the UDUNITS2
    # XML representation.
    # We strip text intentionally - it is known to be spacious in the
    # UDUNITS2 XML representation.

    name: str
    children: list[Tag]
    text: str | None

    @classmethod
    def from_element(cls, element: etree.Element) -> Tag:
        _, _, tag_name = element.tag.partition("}")

        text = (element.text or "").strip()
        children = []

        if len(element) > 0:
            for child in element:
                children.append(cls.from_element(child))
        return cls(name=tag_name, text=text, children=children)

    def pop_first_matching_tag(self, tag_name: str) -> Tag | None:
        for child in self.children[:]:
            if child.name == tag_name:
                self.children.remove(child)
                return child
        return None

    def pop_exactly_one(self, tag_name: str) -> Tag:
        raise NotImplementedError("s")

    def pop_iter_tags(self, tag_name: str) -> typing.Generator[Tag]:
        for child in self.children[:]:
            if child.name == tag_name:
                self.children.remove(child)
                yield child


class UDUNITS2XMLParser:
    @classmethod
    def handle_name_tag(cls, tag: Tag) -> Name:
        singular_name = tag.pop_first_matching_tag("singular")

        if singular_name is None:
            raise ValueError(f"Name for {tag} missing the singular tag")
        else:
            assert not singular_name.children
            singular_name = singular_name.text

        # plural_name = content.pop('plural', None)
        plural_name = tag.pop_first_matching_tag("plural")
        if plural_name is not None:
            plural_name = plural_name.text

        _ = tag.pop_first_matching_tag("noplural")

        if tag.children or tag.text:
            raise ValueError(
                f"Unhandled content in unit {tag} (name {singular_name})"
            )
        return Name(
            singular=singular_name,
            plural=plural_name,
        )

    @classmethod
    def handle_prefix(cls, tag: Tag) -> Prefix:
        name_tag = tag.pop_first_matching_tag("name")
        value_tag = tag.pop_first_matching_tag("value")

        if name_tag is None:
            raise ValueError(f"Name missing in prefix {tag}")
        assert not name_tag.children
        name = name_tag.text

        if value_tag is None:
            raise ValueError(f"Value missing in prefix {tag}")
        assert not value_tag.children
        # Keep the value as a string. We can parse it later.
        value = value_tag.text

        symbols = set()
        for symbol in tag.pop_iter_tags("symbol"):
            symbols.add(symbol.text)

        if tag.children or tag.text:
            raise ValueError(
                f"Unhandled content in prefix {tag} (name {name})"
            )

        return Prefix(
            name=name,
            value=value,
            symbols=tuple(symbols),
        )

    @classmethod
    def parse_file(cls, path: Path) -> UnitSystem:
        with path.open("rt") as fh:
            tree = etree.parse(fh)
        root = tree.getroot()

        [unit_system] = root.xpath('//*[local-name()="unit-system"]')
        unit_system_t = Tag.from_element(unit_system)

        units = []
        prefixes = []

        for prefix_tag in unit_system_t.pop_iter_tags("prefix"):
            prefixes.append(cls.handle_prefix(prefix_tag))

        for unit_tag in unit_system_t.pop_iter_tags("unit"):
            name_tag = unit_tag.pop_first_matching_tag("name")
            if name_tag is None:
                name = None
            else:
                name = cls.handle_name_tag(name_tag)

            symbols = []
            for symbol_tag in unit_tag.pop_iter_tags("symbol"):
                symbols.append(symbol_tag.text)

            alias_names = []
            alias_symbols = []

            aliases = unit_tag.pop_first_matching_tag("aliases")
            if aliases is not None:
                assert not aliases.text
                for alias in aliases.children[:]:
                    aliases.children.remove(alias)
                    if alias.name == "name":
                        alias_names.append(cls.handle_name_tag(alias))
                    elif alias.name == "symbol":
                        assert alias.text and not alias.children
                        alias_symbols.append(alias.text)
                    elif alias.name == "noplural":
                        # Dropped. Seen in avogadro_constant.
                        continue
                    else:
                        raise ValueError(f"Unhandled alias content: {alias}")

            unit_tag.pop_first_matching_tag("comment")

            human_definition = unit_tag.pop_first_matching_tag("definition")
            _ = human_definition

            basis_def = unit_tag.pop_first_matching_tag("def")
            if basis_def is not None:
                assert not basis_def.children
                unit = DerivedUnit(
                    name=name,
                    symbols=tuple(symbols),
                    alias_names=tuple(alias_names),
                    alias_symbols=tuple(alias_symbols),
                    base_unit_definition=basis_def.text,
                )
            else:
                dimensionless = unit_tag.pop_first_matching_tag(
                    "dimensionless"
                )
                if dimensionless is not None:
                    pass  # Seen in radian
                else:
                    base_tag = unit_tag.pop_first_matching_tag("base")
                    assert base_tag is not None
                    assert not base_tag.text and not base_tag.children
                unit = BaseUnit(
                    name=name,
                    symbols=tuple(symbols),
                    alias_names=tuple(alias_names),
                    alias_symbols=tuple(alias_symbols),
                )

            if unit_tag.children:
                raise ValueError(
                    f"Unhandled unit content for unit {unit}: \n{unit_tag}"
                )

            units.append(unit)

        if unit_system_t.children:
            raise ValueError(f"Unhandled content {unit_system_t}")

        system = UnitSystem()

        for prefix in prefixes:
            system.add_prefix(prefix)

        for unit in units:
            system.add_unit(unit)

        return system


def read_all() -> UnitSystem:
    system = UDUNITS2XMLParser.parse_file(XML_path)
    return system


if __name__ == "__main__":
    units = read_all()
