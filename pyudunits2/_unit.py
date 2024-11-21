from __future__ import annotations

# NOTE: No unit_system imports allowed.
from ._expr.graph import Node, Identifier
from ._expr import graph as unit_graph
from ._unit_reference import UnitReference, Prefix
from ._exceptions import IncompatibleUnitsError
from ._datetime import DateTime
from ._expr.normaliser import NormalisedNode

import typing


if typing.TYPE_CHECKING:
    from sympy.core.expr import Expr as SympyExpr


class Expression:
    # A representation of an expression. The expression itself is immutable,
    # but internally a cache of the generated expression (in sympy form) is made,
    # allowing re-use/optimisation of the computation.
    def __init__(self, raw_definition: str, expression: Node):
        self._raw_definition = raw_definition
        self.expression = expression
        self._expanded_symbolic_form: SympyExpr | None = None
        self._expanded_symbolic_form2: tuple[SympyExpr, SympyExpr] | None = None

    def __repr__(self):
        return f"Expression({self._raw_definition!r}, {self.expression!r})"

    @classmethod
    def from_raw(cls, raw_definition: str) -> Expression:
        from ._grammar import parse

        return Expression(raw_definition, parse(raw_definition))

    def _symbolic_form(self) -> SympyExpr:
        if self._expanded_symbolic_form is None:
            from ._expr.sympy import ToSympy

            prepared = ToSympy().visit(self.expression)
            self._expanded_symbolic_form = prepared
        return self._expanded_symbolic_form

    def _symbolic_form2(self) -> tuple[SympyExpr, SympyExpr]:
        if self._expanded_symbolic_form2 is None:
            from ._expr.sympy import ToSympy
            from ._expr.split import SplitExpr

            t, d = SplitExpr(self.expression).visit(self.expression)
            if t is not None:
                transform = ToSympy().visit(t)
            else:
                import sympy

                transform = sympy.Symbol("value")

            prepared = ToSympy().visit(d)

            self._expanded_symbolic_form2 = transform, prepared
        return self._expanded_symbolic_form2

    def __eq__(self, other: Expression) -> bool:
        # TODO: This is probably wrong as we have some details to deal with
        #  when building the conversion expression.
        # print('EQ EXPR:', self, other)
        if type(self) is not type(other):
            return NotImplemented

        from sympy import simplify, expand

        # TODO: Use symbolic form 2
        a = self._symbolic_form()
        b = other._symbolic_form()
        if a == b:
            # Symbolically identical short-circuit.
            return True

        eq = a - b
        sim = simplify(eq)
        return expand(sim, trig=False) == 0


class UnitDefinition:
    def __init__(
        self, definition: Node, identifier_references: typing.Mapping[Identifier, Unit]
    ):
        self._definition = definition
        self._expression_graph: Node
        self._identifier_references: dict[Identifier, Prefix | Unit] = {}

    def _to_sympy(self):
        pass


class Converter:
    def __init__(self, from_unit: Unit, to_unit: Unit):
        """

        Log units. The best example to help you get your head around what they represent
        is to have a unit of `decade = lg(re year)`. 20 years == 2 decades. The log part
        of a unit is a transformation of the value, and *not* a true symbolic
        representation of log(year). Now we can extend the concept to
        `century = lg(re lg(re year))`.

        Some useful examples from UDUNITS-2::

            You have: lg(re m/s)
            You want: m/s
                1 lg(re m/s) = 10 m/s
                x/(m/s) = pow(10, (x/(lg(re m/s))))

            You have: m
            You want: lg(re m)
                1 m = 0 (lg(re m))
                x/(lg(re m)) = lg((x/m))

            You have: m/s
            You want: lg(re 2*m/s)
                1 m/s = -0.30103 (lg(re 2*m/s))
                x/(lg(re 2*m/s)) = lg(0.5*(x/(m/s)))

            You have: lg(re lg(re m))
            You want: m
                1 lg(re lg(re m)) = 1e+10 m
                x/m = pow(10, (pow(10, (x/(lg(re lg(re m)))))))

            You have: lg(re m)*degrees
            You want: m
                1 lg(re m)*degrees = 1.04101 m
                x/m = pow(10, (0.0174533*(x/(lg(re m)*degrees))))

        Note that the unit grammar does not follow the normal mathematical rules
        for logarithms (namely `n log(m) != log(m^n)`)

            You have: 2 lg(re years)
            You want: years
                2 lg(re years) = 100 years
                x/years = 3.16888e-08*(3.15569e+07*(pow(10, (x/(lg(re years))))))
            You have: 2*lg(re years)

            You have: lg(re years)*2
            You want: years
                1 lg(re years)*2 = 100 years
                x/years = 3.16888e-08*(3.15569e+07*(pow(10, (2*(x/(lg(re years)*2))))))

        Some useful failure modes::

            You have: lg(re m)*lg(re s)
            logMultiply(): can't multiply second unit
            ut_are_convertible(): NULL unit argument
            udunits2: Don't recognize "lg(re m)*lg(re s)"

            You have: lg(re m)*s
            logMultiply(): Second unit not dimensionless
            ut_are_convertible(): NULL unit argument
            udunits2: Don't recognize "lg(re m)*s"

        Is it possible that this is inconsistent...?

            You have: degC
            You want: kelvin
                1 degC = 274.15 kelvin
                x/kelvin = (x/degC) + 273.15

            You have: degC^2
            You want: kelvin^2
                1 degC^2 = 1 kelvin^2
                x/kelvin^2 = (x/degC^2)

        Log units are not really log units at all... they are value transformations.
        For example:

            10 lg(re m) is really lg(re 10) m


        Date units... sigh. We avoid converting them at all, since it requires a calendar in general.
            $ udunits2 -H '(m/m) days since 2000' -W '(km/m) days since 2001'
                1 (m/m) days since 2000 = -0.365 ((km/m) days since 2001)
                x/((km/m) days since 2001) = 0.001*(x/((m/m) days since 2000)) - 0.366
        """
        self._from_unit = from_unit
        self._to_unit = to_unit

        import sympy

        from_dimensionality = from_unit.dimensionality()
        to_dimensionality = to_unit.dimensionality()

        # It is also possible to simply invert the dimensionality. For example,
        # m/s is simply 1/value s/m
        inverted_d = from_dimensionality.inverted()

        is_direct_conversion = from_dimensionality == to_dimensionality
        is_inverted_conversion = inverted_d == to_dimensionality
        if not (is_direct_conversion or is_inverted_conversion):
            raise IncompatibleUnitsError(
                f"Units {to_unit} and {from_unit} are not convertible"
            )

        t1, d1 = from_unit._symbolic_definition()
        t2, d2 = to_unit._symbolic_definition()

        to_symbol = sympy.symbols("value_transformed_to_base_unit_scale")

        orig_qty = sympy.symbols("value")
        to_value = sympy.symbols("to_value")

        # The t1 definition is the inverse of what we express. For example, lg(re value) means
        # we must 10^value to get the base unit scale value.
        t1 = t1.subs(orig_qty, to_symbol)

        t2 = t2.subs(orig_qty, to_value)

        if t1 == orig_qty:
            transformer1 = orig_qty
        else:
            transformer1 = sympy.solve(t1 - orig_qty, to_symbol)
            assert len(transformer1) == 1
            [transformer1] = transformer1

        if is_direct_conversion:
            convert_expr = t2.subs(to_value, transformer1 * d1 / d2)
        else:
            convert_expr = t2.subs(to_value, 1 / (transformer1 * d1 * d2))

        fn = sympy.lambdify(
            orig_qty,
            convert_expr,
        )
        self.expression = convert_expr
        self._converter = fn

        # TODO: Check that it is dimensionless.

        return

    def convert(self, values):
        # TODO: Sympy can return an expression here. We never want it
        #  to - it should always be a number-like.
        return self._converter(values)


class Dimensionality:
    """
    A dictionary-like interface to represent the mapping between a basis unit
    and the dimensional order of that basis. For example, ``m^2/s`` (area per
    second) would have a dimensionality dictionary of ``{'m': 2, 's': 1}``.
    """

    def __init__(self, dimensionality: dict[BasisUnit, int]):
        self._dimensionality = dimensionality

    def __eq__(self, other: typing.Any) -> bool:
        if isinstance(other, dict):
            return self._name_form() == other
        if type(self) is not type(other):
            return NotImplemented
        return self._dimensionality == other._dimensionality

    def _name_form(self) -> dict[str, int]:
        return {str(base_unit): order for base_unit, order in self.items()}

    def inverted(self):
        return Dimensionality(
            {unit: -order for unit, order in self._dimensionality.items()}
        )

    def __repr__(self):
        return f"Dimensionality({self._dimensionality})"

    def __str__(self):
        return str(self._name_form())

    def __len__(self):
        return len(self._dimensionality)

    def items(self):
        return self._dimensionality.items()

    def keys(self):
        return self._dimensionality.keys()

    def values(self):
        return self._dimensionality.values()


class UnitInterface(typing.Protocol):
    def dimensionality(self) -> Dimensionality: ...

    def is_dimensionless(self) -> bool: ...

    def is_convertible_to(self, other: UnitInterface) -> bool: ...

    # TODO: Add is_time_unit?


def _unit_from_expression_and_identifiers(
    unit_expr: unit_graph.Node,
    identifier_references: typing.Mapping[Identifier, Unit | Prefix],
) -> Unit | DateUnit:
    if isinstance(unit_expr, unit_graph.Shift):
        # The first shift MAY be a date unit. Any subsequent date shifts
        # will result in an exception during normalisation.
        shifted_unit_expr: unit_graph.Node = unit_expr.unit
        shifted_unit = Unit(
            definition=shifted_unit_expr,
            identifier_references=identifier_references,
        )
        if shifted_unit.is_time_unit():
            # Shifted and time => we have a date.
            # date_ref = DateUnit.parse(unit_expr.shift_from)
            date_ref = unit_expr.shift_from
            if isinstance(date_ref, unit_graph.Number):
                date_ref = unit_graph.Unhandled(date_ref.raw_content)
            if not isinstance(date_ref, unit_graph.Unhandled):
                raise ValueError(f"Unexpected parse type for date: {type(date_ref)}")

            return DateUnit(
                unit=shifted_unit,
                reference_date=date_ref,
            )

    return Unit(definition=unit_expr, identifier_references=identifier_references)


class Unit(UnitInterface):
    def __init__(
        self,
        *,
        definition: Node | NormalisedNode,
        identifier_references: typing.Mapping[Identifier, Unit | Prefix],
    ):
        if isinstance(definition, NormalisedNode):
            # If it has already been normalised, pull out the definition.
            definition = definition.unit_expr
        else:
            # If not already normalised, make sure we can normalise the
            # definition without issue, but continue to use the un-normalised
            # form (so that we can round-trip our unit... note that this may
            # not be necessary in the future if our graph is able to guarantee
            # round-trip even after normalisation).
            # Note that this call can result in an exception, for example if
            # the definition contains a date-like unit.
            _ = NormalisedNode(definition, identifier_references)

        self._definition: Node = definition
        self._identifier_references = identifier_references
        self._cached_symbolic_definition = None

    def __str__(self):
        return str(self._definition)

    def __repr__(self):
        return "\n".join(
            (
                f"{type(self).__name__}(",
                f"    definition={self._definition!r},"
                f"    identifier_references={self._identifier_references!r},"
                f")",
            )
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, Unit):
            return NotImplemented

        assert isinstance(other, Unit)
        # TODO: Use equality of the graph, not stringification.
        if str(other._definition) == str(self._definition):
            # Short-circuit identical definitions.
            return True

        from sympy import simplify, expand

        self_t, self_d = self._symbolic_definition()
        other_t, other_d = other._symbolic_definition()

        eq = self_d - other_d
        sim = simplify(eq)
        return expand(sim, trig=False) == 0 and self_t == other_t

    def _symbolic_definition(self) -> tuple[SympyExpr, SympyExpr]:
        if self._cached_symbolic_definition is None:
            from ._expr.sympy import ToSympy
            from ._expr.split import SplitExpr

            definition = self._expanded_expr()
            t, d = SplitExpr(definition).visit(definition)
            if t is not None:
                transform = ToSympy().visit(t)
            else:
                import sympy

                transform = sympy.Symbol("value")

            prepared = ToSympy().visit(d)

            self._cached_symbolic_definition = transform, prepared
        return self._cached_symbolic_definition

    def _expanded_expr(self) -> Node:
        from ._expr.substitute import Substitute

        # print(self._identifier_references)
        result = Substitute(
            {
                identifier: unit._expanded_expr()
                for identifier, unit in self._identifier_references.items()
            },
        ).visit(self._definition)
        return result

    def expanded(self) -> str:
        expr = self._expanded_expr()
        # TODO: Simplify & normalise.
        return str(expr)

    #
    #
    # def __eq__(self, other) -> bool:
    #     if type(self) is not type(other):
    #         return NotImplemented
    #     assert isinstance(other, ExpressionUnit)
    #     return other._expression == self._expression

    def dimensionality(self) -> Dimensionality:
        from ._expr.dimensionality import DimensionalityCounter
        from ._expr.split import SplitExpr

        _, d = SplitExpr(self._definition).visit(self._definition)
        r = DimensionalityCounter().visit(d)

        result = {}
        for identifier, order in r.items():
            identifier_unit = self._identifier_references[identifier]
            if isinstance(identifier_unit, Prefix):
                continue
            unit_dimensionality = identifier_unit.dimensionality()
            for basis_unit, basis_order in unit_dimensionality.items():
                result[basis_unit] = result.get(basis_unit, 0) + basis_order * order
        return Dimensionality(
            {basis: order for basis, order in result.items() if order != 0}
        )

    def is_dimensionless(self) -> bool:
        return self.dimensionality() == {}

    def is_time_unit(self) -> bool:
        basis = self.dimensionality()
        if len(basis) == 1:
            [basis_unit, basis_unit_order] = next(iter(basis.items()))
            return basis_unit.is_time_unit() and basis_unit_order == 1
        return False

    def is_convertible_to(self, other: UnitInterface) -> bool:
        if not isinstance(other, Unit):
            # Reject other units-like units, such as DateUnit.
            return False
        self_d = self.dimensionality()
        other_d = other.dimensionality()
        if self_d == other_d:
            return True
        # It is also possible to simply invert the dimensionality. For example,
        # m/s is simply 1/value s/m
        inverted_d = self_d.inverted()
        if inverted_d == other_d:
            return True
        return False


Names = UnitReference


class DateUnit(UnitInterface):
    def __init__(
        self,
        *,
        unit: Unit,
        reference_date: DateTime | unit_graph.Unhandled,
    ):
        assert unit.is_time_unit()
        self._unit = unit
        self._reference_date = reference_date

    def is_convertible_to(self, other: UnitInterface) -> bool:
        # TODO: We can start to do better now that we have rich dates.
        return False

    @property
    def unit(self):
        return self._unit

    @property
    def reference_date(self) -> DateTime | unit_graph.Unhandled:
        return self._reference_date

    def is_dimensionless(self) -> bool:
        return False

    def is_time_unit(self):
        return True

    def dimensionality(self) -> Dimensionality:
        return self._unit.dimensionality()

    def _symbolic_definition(self):
        # TODO: This should be specialised for dates.
        return self._unit._symbolic_definition()

    def expanded(self):
        return f"{self._unit.expanded()} since {self.reference_date}"

    # def convert_to(self):
    #     # Note that there are some interesting cases from udunits2:
    #     #
    #     #     $ udunits2 -H 'meter days since 2000' -W 'meter days since 2001'
    #     #         1 meter days since 2000 = 0 (meter days since 2001)
    #     #         x/(meter days since 2001) = (x/(meter days since 2000)) - 1
    #     #     $ udunits2 -H 'meter days since 2000-01' -W 'meter days since 2001-01'
    #     #         udunits2: Don't recognize "meter days since 2000-01"
    #     #     $ udunits2 -H 'days since 2000' -W 'days since 2001'
    #     #         1 days since 2000 = -365 (days since 2001)
    #     #         x/(days since 2001) = (x/(days since 2000)) - 366
    #     #     $ udunits2 -H 'meter (days since 2000)' -W 'meter (days since 2001)'
    #     #         1 meter (days since 2000) = 1 (meter (days since 2001))
    #     #         x/(meter (days since 2001)) = (x/(meter (days since 2000)))
    #     #     $ udunits2 -H 'meter meter-1 days since 2000' -W 'meter meter-1 days since 2001'
    #     #         1 meter meter-1 days since 2000 = -365 (meter meter-1 days since 2001)
    #     #         x/(meter meter-1 days since 2001) = (x/(meter meter-1 days since 2000)) - 366
    #     #     $ udunits2 -H '(weeks since 2001) (days since 2000)' -W '(weeks since 2001) (days since 2001)'
    #     #         1 (weeks since 2001) (days since 2000) = 1 ((weeks since 2001) (days since 2001))
    #     #         x/((weeks since 2001) (days since 2001)) = 1*(x/((weeks since 2001) (days since 2000)))
    #     #     $ udunits2 -H 'kilodays since 2000-01' -W 'days since 2001-01'
    #     #         1 kilodays since 2000-01 = 634 (days since 2001-01)
    #     #         x/(days since 2001-01) = 1000*(x/(kilodays since 2000-01)) - 366
    #     raise NotImplementedError()


class NamedUnit(Unit):
    def __init__(
        self,
        *,
        definition: Node,
        identifier_references: typing.Mapping[Identifier, Unit],
        names: Names,
    ):
        super().__init__(
            definition=definition, identifier_references=identifier_references
        )
        self._names = names


class BasisUnit(NamedUnit):
    def __init__(
        self, *, names: Names, dimensionless: bool = False, is_time_unit: bool = False
    ):
        ref = names.name.singular or names.symbols[0]
        self._ref = ref
        self._dimensionless = dimensionless
        self._is_time_unit = is_time_unit
        super().__init__(
            definition=Identifier(ref),
            identifier_references={Identifier(name=ref): self},
            names=names,
        )

    def __repr__(self):
        return f"{type(self).__name__}(names={self._names!r}, dimensionless={self._dimensionless})"

    def __hash__(self):
        # TODO: Implement this properly.
        return 1

    def _expanded_expr(self):
        return self._definition

    def __str__(self):
        return self._ref

    def dimensionality(self) -> dict[BasisUnit, int]:
        if self._dimensionless:
            return {}
        else:
            return {self: 1}

    def is_time_unit(self):
        return self._is_time_unit


# class DefinedUnit(Unit):
#     # Represents a well-defined unit with comparable basis.
#     # Note that a LazilyDefinedUnit exists if you do not want to resolve the
#     # basis expression upfront.
#     def __init__(
#         self,
#         raw_spec: str,  # The requested form of the unit.
#         definition: Node,  # The fully resolved (basis form) definition of this unit.
#         *,
#         reference: UnitReference | None = None,
#     ):
#         self._definition = definition
#         self._unit_raw = raw_spec
#         self._unit_graph = None
#         super().__init__(reference=reference)
#
#     # def conversion_expr(self, other: Unit):
#     #     from ._expr.sympy import ToSympy
#     #
#     #     sympy_expr = ToSympy().visit(self._definition)
#     #     # expr = FromSympy().visit(sympy_expr)
#     #     return sympy_expr
#     #
#     # def base_form(self) -> Unit:
#     #     # TODO: Return Unit
#     #     # TODO: Resolve the terms, and canonicalise the name/symbols.
#     #     return self._definition
#     #
#     # def convertible_to(self, other: Unit) -> bool:
#     #     raise NotImplementedError("TODO")
#
#     def __str__(self):
#         return self._unit_raw
#
#     def __repr__(self):
#         return (
#             f"DefinedUnit(raw_spec={self._unit_raw}, definition={self._definition}, "
#             f"reference={self._reference})"
#         )
#
#     def __eq__(self, other):
#         if type(other) is not DefinedUnit:
#             return NotImplemented
#
#         # TODO: Get the base form to compare __eq__ on simplified form.
#         return other.base_form() == self.base_form()
