from __future__ import annotations

from decimal import Decimal

from sympy import Symbol


from sympy.parsing.sympy_parser import parse_expr as sympy_parse
import sympy

import logging
import typing

from .. import _expr_graph as unit_graph
import sympy.core.expr

_log = logging.getLogger(__name__)


# identity = sympy.Number(1)
qty = sympy.symbols("qty")


class ToSympy(unit_graph.Visitor):
    """
    A unit expression isn't a simple mathematical symbolic representation.
    For example, lg(re years) is really a scaling transformation lg(re qty) and
    the unit definition is the inner `years`.

    Therefore, this visitor returns both the scaling transformation and the
    unit definition as separate symbols. We don't do validation that the scaling
    transformation is dimensionless here.

    """

    if typing.TYPE_CHECKING:

        def visit(
            self, node: unit_graph.Node
        ) -> tuple[sympy.core.expr.Expr, sympy.core.expr.Expr]: ...

    def generic_visit(self, node: unit_graph.Node):
        raise NotImplementedError(f"Not implemented for {type(node)}")

    def visit_Identifier(self, node: unit_graph.Identifier):
        return qty, Symbol(node.content)

    # def visit_ExpressionNode(self, node: ExpressionNode):
    #     return node.content._symbolic_form()

    def visit_Number(self, node: unit_graph.Number):
        if isinstance(node.content, str):
            return qty, sympy_parse(node.content)
        elif isinstance(node.content, Decimal):
            return qty, sympy_parse(str(node.content))
        elif isinstance(node.content, (int, float)):
            return qty, sympy_parse(str(node.content))
        else:
            raise ValueError(f"Unknown number type {type(node.content)}")

    def visit_Shift(self, node: unit_graph.Shift):
        t1, d1 = self.visit(node.unit)
        # A shift is really a value transformation, not a unit definition.
        t2, d2 = self.visit(node.shift_from)
        assert t2 == qty
        # TODO: Perhaps assert that d2 is dimensionless?
        return t1 + d2, d1

    def visit_Raise(self, node: unit_graph.Raise):
        t1, d1 = self.visit(node.lhs)
        t2, d2 = self.visit(node.rhs)
        assert t2 == qty
        # udunits2 claims `x/kelvin = (x/degC) + 273.15` and `x/kelvin^2 = (x/degC^2)`
        # Suggesting that the transformation is dropped for shifts.
        return t1**d2, d1**d2

    def visit_Multiply(self, node: unit_graph.Multiply):
        t1, d1 = self.visit(node.lhs)
        t2, d2 = self.visit(node.rhs)
        return t1 * t2, d1 * d2

    def visit_Divide(self, node: unit_graph.Divide):
        t1, d1 = self.visit(node.lhs)
        t2, d2 = self.visit(node.rhs)
        assert t2 == qty
        return t1, d1 / d2

    def visit_Logarithm(self, node: unit_graph.Logarithm):
        bases = {
            "lb": 2,
            "lg": 10,
            "ln": None,  # Sympy defaults to natual log.
            "log": None,  # Unspecified by udunits2...
        }
        base = bases[node.function]

        t1, d1 = self.visit(node.term)

        if base is None:
            return sympy.log(t1 * qty), d1
        else:
            return sympy.log(t1 * qty, bases[node.function]), d1
