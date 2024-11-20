from .graph import Visitor, Node
import typing
from . import graph as unit_graph


class Substitute(Visitor):
    # TODO: Implement a base "copy" visitor.

    def __init__(self, substitutions: typing.Mapping[Node, Node]):
        self._subs = substitutions

    if typing.TYPE_CHECKING:

        def visit(self, node: unit_graph.Node) -> Node: ...

    def generic_visit(self, node: unit_graph.Node):
        if isinstance(node, unit_graph.Terminal):
            if isinstance(node, unit_graph.Identifier) and node in self._subs:
                node = self._subs[node]
            return node
        raise NotImplementedError(f"Not implemented for {type(node)}")

    def visit_Shift(self, node: unit_graph.Shift):
        return unit_graph.Shift(self.visit(node.unit), self.visit(node.shift_from))

    def visit_Raise(self, node: unit_graph.Raise):
        return unit_graph.Raise(self.visit(node.lhs), self.visit(node.rhs))

    def visit_Multiply(self, node: unit_graph.Raise):
        return unit_graph.Multiply(self.visit(node.lhs), self.visit(node.rhs))

    def visit_Divide(self, node: unit_graph.Divide):
        return unit_graph.Divide(self.visit(node.lhs), self.visit(node.rhs))

    def visit_Logarithm(self, node: unit_graph.Logarithm):
        return unit_graph.Logarithm(term=self.visit(node.term), function=node.function)
