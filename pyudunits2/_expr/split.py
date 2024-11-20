from __future__ import annotations

import logging
import typing

from . import graph as unit_graph

_log = logging.getLogger(__name__)


class SplitExpr(unit_graph.Visitor):
    """
    Split the given expression into a value transformation component and
    a unit definition component.

    For example, the unit `5 log(re m/s)` is really a unit of m/s with a value
    transformation of `5 log(re value)`. This can be used to convert from
    one unit to another - naturally, the definition must have the same
    dimensionality as the target unit, and the value being converted will need
    to be transformed by inverting `value = 5 log(re value_in_base_unit)`.

    """

    def __init__(self, root_node: unit_graph.Node):
        self._root_node = root_node

    if typing.TYPE_CHECKING:

        def visit(
            self, node: unit_graph.Node
        ) -> tuple[unit_graph.Node | None, unit_graph.Node]: ...

    def generic_visit(self, node: unit_graph.Node):
        if isinstance(node, unit_graph.Terminal):
            return None, node
        raise NotImplementedError(f"Not implemented for {type(node)}")

    def visit_Shift(self, node: unit_graph.Shift):
        # When shifting, you want to transform the value, since otherwise you
        # will not end up with dimensionless conversions.
        # For example, K @ 271 converted to K should shift the value 271, and
        # then the K/K will cancel out.
        t1, d1 = self.visit(node.unit)
        if t1 is None:
            t1 = unit_graph.Identifier(name="value")
        # Looking at UDUNITS2, the shift is completely ignored in conversions
        # unless it is the terminating operation.
        if node is self._root_node:
            return unit_graph.Shift(t1, node.shift_from), d1
        else:
            return t1, d1

    def visit_Raise(self, node: unit_graph.Raise):
        t1, d1 = self.visit(node.lhs)
        t2, d2 = self.visit(node.rhs)
        assert t2 is None
        return t1, unit_graph.Raise(d1, d2)

    def visit_Multiply(self, node: unit_graph.Multiply):
        t1, d1 = self.visit(node.lhs)
        t2, d2 = self.visit(node.rhs)
        if t1 is not None and t2 is not None:
            raise ValueError("Unable to apply two unit transformations")

        if t1 is not None:
            return unit_graph.Multiply(t1, d2), d1

        elif t2 is not None:
            return unit_graph.Multiply(d1, t2), d2
        else:
            return None, unit_graph.Multiply(d1, d2)

    def visit_Divide(self, node: unit_graph.Divide):
        t1, d1 = self.visit(node.lhs)
        t2, d2 = self.visit(node.rhs)
        if t1 is not None and t2 is not None:
            raise ValueError("Unable to apply two unit transformations")
        return t1 or t2, unit_graph.Divide(d1, d2)

    def visit_Logarithm(self, node: unit_graph.Logarithm):
        t1, d1 = self.visit(node.term)
        if t1 is None:
            t1 = unit_graph.Identifier(name="value")
        return unit_graph.Logarithm(function=node.function, term=t1), d1
