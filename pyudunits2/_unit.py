from __future__ import annotations

from ._expr_graph import Node, Identifier
from ._unit_reference import UnitReference

import typing

if typing.TYPE_CHECKING:
    import sympy.core.expr

# class Unit:
#     def __init__(self, *, reference: UnitReference | None):
#         self._reference = reference
#
#     def convertible_to(self, other: Unit) -> bool:
#         # For basis units, and those without a unit system, the only units
#         # which are convertible are those which are equal.
#         return self == other


class Expression:
    # A representation of an expression. The expression itself is immutable,
    # but internally a cache of the generated expression (in sympy form) is made,
    # allowing re-use/optimisation of the computation.
    def __init__(self, raw_definition: str, expression: Node):
        self._raw_definition = raw_definition
        self.expression = expression
        self._expanded_symbolic_form: sympy.core.expr.Expr | None = None
        self._expanded_symbolic_form2: (
            tuple[sympy.core.expr.Expr, sympy.core.expr.Expr] | None
        ) = None

    def __repr__(self):
        return f"Expression({self._raw_definition!r}, {self.expression!r})"

    @classmethod
    def from_raw(cls, raw_definition: str) -> Expression:
        from ._grammar import parse

        return Expression(raw_definition, parse(raw_definition))

    def _symbolic_form(self) -> sympy.core.expr.Expr:
        if self._expanded_symbolic_form is None:
            from ._expr.sympy import ToSympy

            prepared = ToSympy().visit(self.expression)
            self._expanded_symbolic_form = prepared
        return self._expanded_symbolic_form

    def _symbolic_form2(self) -> tuple[sympy.core.expr.Expr, sympy.core.expr.Expr]:
        if self._expanded_symbolic_form2 is None:
            from ._expr.sympy import ToSympy
            from ._expr.expr_split import SplitExpr

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
        """
        self._from_unit = from_unit
        self._to_unit = to_unit

        from ._expr_graph import Divide

        self._expression = Expression(
            raw_definition=f"({self._from_unit._expression._raw_definition}) / ({self._to_unit._expression._raw_definition})",
            expression=Divide(
                self._from_unit._expression.expression,
                self._to_unit._expression.expression,
            ),
        )
        import sympy

        t1, d1 = from_unit._expression._symbolic_form2()
        t2, d2 = to_unit._expression._symbolic_form2()

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
        convert_expr = t2.subs(to_value, transformer1 * d1 / d2)
        fn = sympy.lambdify(
            orig_qty,
            convert_expr,
        )
        self._converter = fn

        # TODO: Check that it is dimensionless.

        return

    def convert(self, values):
        # TODO: Sympy can return an expression here. We never want it
        #  to - it should always be a number-like.
        return self._converter(values)


class Unit:
    def __init__(
        self, expression: Expression, *, reference: UnitReference | None = None
    ):
        self._expression = expression
        self._reference = reference
        super().__init__()

    def __eq__(self, other) -> bool:
        if not isinstance(other, Unit):
            return NotImplemented

        # if type(self) is not type(other):
        #     return NotImplemented
        assert isinstance(other, Unit)
        return other._expression == self._expression

    #
    #
    # def __eq__(self, other) -> bool:
    #     if type(self) is not type(other):
    #         return NotImplemented
    #     assert isinstance(other, ExpressionUnit)
    #     return other._expression == self._expression


class BasisUnit(Unit):
    def __init__(self, reference: UnitReference):
        ref = reference.name.singular or reference.symbols[0]
        super().__init__(
            expression=Expression(ref, Identifier(ref)),
            reference=reference,
        )

    def __str__(self):
        if self._reference is None:
            return super().__str__()
        if self._reference.name is not None:
            return self._reference.name.singular
        assert self._reference.symbols
        return self._reference.symbols[0]


class SimpleUnit(Unit):
    def __init__(self, definition: str):
        from ._grammar import parse

        unit_expr = parse(definition)
        super().__init__(expression=Expression(definition, unit_expr))


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

    def conversion_expr(self, other: Unit):
        from ._expr.sympy import ToSympy

        sympy_expr = ToSympy().visit(self._definition)
        # expr = FromSympy().visit(sympy_expr)
        return sympy_expr

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
