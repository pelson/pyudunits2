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

    @classmethod
    def from_raw(cls, raw_definition: str) -> Expression:
        from ._grammar import parse

        return Expression(raw_definition, parse(raw_definition))

    def _symbolic_form(self) -> sympy.core.expr.Expr:
        if self._expanded_symbolic_form is None:
            prepared = None
            from ._expr.sympy import ToSympy

            print("TY:", type(self.expression))
            prepared = ToSympy().visit(self.expression)
            from pprint import pprint

            print(
                "EXPR:",
            )
            pprint(self.expression)
            self._expanded_symbolic_form = prepared
        return self._expanded_symbolic_form

    def __eq__(self, other: Expression) -> bool:
        # print('EQ EXPR:', self, other)
        if type(self) is not type(other):
            return NotImplemented

        from sympy import simplify, expand

        a = self._symbolic_form()
        b = other._symbolic_form()
        if a == b:
            # Symbolically identical short-circuit.
            return True

        eq = a - b
        sim = simplify(eq)
        print("SIM:", sim)
        return expand(sim, trig=False) == 0


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
