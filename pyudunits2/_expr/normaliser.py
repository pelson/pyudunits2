from __future__ import annotations

import logging
import typing

from . import graph as unit_graph
from .graph import Node, Visitor


_log = logging.getLogger(__name__)


class NormalisedExpressionGraph(Visitor):
    """
    A visitor which tidies up a unit definition graph. For optimal performance,
    any unchanged node is returned as None (this optimisation may change in
    the future with frozen dataclasses).

    Any date-like shift definition encountered will raise. It is expected that
    a call to this visitor will already have separated out the first shift
    operation of a date-like unit.

    """

    def __init__(self, original_unit_expr, identifier_references):
        self.original_unit_expr = original_unit_expr
        self.identifier_references = identifier_references

    if typing.TYPE_CHECKING:

        def visit(self, node: unit_graph.Node) -> unit_graph.Node | None:
            # When returning None, we are signalling that there is no
            # normalisation needed.
            ...

    def generic_visit(self, node: unit_graph.Node):
        raise NotImplementedError(f"Not implemented for {type(node)}")

    def visit_internal(self, node):
        return super().visit(node)

    def visit_Multiply(self, node: unit_graph.Multiply):
        normed_lhs = super().visit(node.lhs)
        normed_rhs = super().visit(node.rhs)
        if normed_lhs is not None:
            # node = dataclasses.replace(node, lhs=normed_lhs)
            node = unit_graph.Multiply(normed_lhs, node.rhs)
        if normed_rhs is not None:
            node = unit_graph.Multiply(node.lhs, normed_rhs)
        if normed_lhs is not None or normed_rhs is not None:
            return node
        return None

    def visit_Divide(self, node: unit_graph.Divide) -> unit_graph.Divide | None:
        normed_lhs = super().visit(node.lhs)
        normed_rhs = super().visit(node.rhs)
        if normed_lhs is not None:
            # node = dataclasses.replace(node, lhs=normed_lhs)
            node = unit_graph.Divide(normed_lhs, node.rhs)
        if normed_rhs is not None:
            node = unit_graph.Divide(node.lhs, normed_rhs)
        if normed_lhs is not None or normed_rhs is not None:
            return node
        return None

    def visit_Identifier(self, node: unit_graph.Identifier):
        return None

    def visit_Number(self, node: unit_graph.Number):
        return None

    def visit_Raise(self, node: unit_graph.Raise):
        normed_lhs = self.visit(node.lhs)
        normed_rhs = self.visit(node.rhs)
        if normed_lhs is not None:
            # node = dataclasses.replace(node, lhs=normed_lhs)
            node = unit_graph.Raise(normed_lhs, node.rhs)
        if normed_rhs is not None:
            node = unit_graph.Raise(node.lhs, normed_rhs)
        if normed_lhs is not None or normed_rhs is not None:
            return node
        return None

    def visit_Logarithm(self, node: unit_graph.Logarithm):
        normed_term = self.visit(node.term)
        if normed_term is not None:
            node = unit_graph.Logarithm(node.function, normed_term)
            return node
        return None

    def visit_Shift(self, node: unit_graph.Shift):
        from .._unit import Unit

        normed_unit = self.visit(node.unit)

        if normed_unit is None:
            # Return of None means that it is already normalised.
            normed_unit = node.unit
        normed_node = NormalisedNode._from_guaranteed_norm(normed_unit)

        unit = Unit(
            definition=normed_node,
            identifier_references=self.identifier_references,
        )

        if unit.is_time_unit():
            raise ValueError(
                f"Refusing to represent dates in a nested unit {self.original_unit_expr}"
            )

        if not isinstance(node.shift_from, unit_graph.Number):
            raise ValueError("Normalisation of non-numeric shift not possible")

        if normed_unit is not None:
            node = unit_graph.Shift(normed_unit, node.shift_from)
            return node
        return None


class NormalisedNode:
    """
    A container holding a node that has been normalised.
    """

    def __init__(self, unit_expr: Node, identifier_references):
        new_unit_expr = NormalisedExpressionGraph(
            unit_expr,
            identifier_references,
        ).visit(unit_expr)
        if new_unit_expr is None:
            new_unit_expr = unit_expr
        self.unit_expr = new_unit_expr

    @classmethod
    def _from_guaranteed_norm(cls, node: Node) -> NormalisedNode:
        # To be used when normalisation has been called already, and you are
        # promising that the node being given is normalised.
        inst = NormalisedNode.__new__(cls)
        inst.unit_expr = node
        return inst
