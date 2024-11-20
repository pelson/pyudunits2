from __future__ import annotations

from decimal import Decimal

from sympy import Symbol


from sympy.parsing.sympy_parser import parse_expr as sympy_parse
import sympy

import logging
import typing

from . import graph as unit_graph
import sympy.core.expr

_log = logging.getLogger(__name__)


class ToSympy(unit_graph.Visitor):
    if typing.TYPE_CHECKING:

        def visit(self, node: unit_graph.Node) -> sympy.core.expr.Expr: ...

    def generic_visit(self, node: unit_graph.Node):
        raise NotImplementedError(f"Not implemented for {type(node)}")

    def visit_Identifier(self, node: unit_graph.Identifier):
        return Symbol(node.content)

    def visit_Number(self, node: unit_graph.Number):
        if isinstance(node.content, str):
            return sympy_parse(node.content)
        elif isinstance(node.content, Decimal):
            return sympy_parse(str(node.content))
        elif isinstance(node.content, (int, float)):
            return sympy_parse(str(node.content))
        else:
            raise ValueError(f"Unknown number type {type(node.content)}")

    def visit_Shift(self, node: unit_graph.Shift):
        return self.visit(node.unit) - self.visit(node.shift_from)

    def visit_Raise(self, node: unit_graph.Raise):
        return self.visit(node.lhs) ** self.visit(node.rhs)

    def visit_Multiply(self, node: unit_graph.Multiply):
        return self.visit(node.lhs) * self.visit(node.rhs)

    def visit_Divide(self, node: unit_graph.Divide):
        return self.visit(node.lhs) / self.visit(node.rhs)

    def visit_Logarithm(self, node: unit_graph.Logarithm):
        bases = {
            "lb": 2,
            "lg": 10,
            "ln": None,  # Sympy defaults to natual log.
            "log": None,  # Unspecified by udunits2...
        }
        base = bases[node.function]
        if base is None:
            return sympy.log(self.visit(node.term))
        else:
            return sympy.log(self.visit(node.term), bases[node.function])


class FromSympy(unit_graph.Visitor):
    def generic_visit(self, node: unit_graph.Node):
        raise NotImplementedError(f"Not implemented for {type(node)}")
