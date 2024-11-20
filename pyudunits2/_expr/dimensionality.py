from .graph import Visitor
import typing
from . import graph as unit_graph


class DimensionalityCounter(Visitor):
    if typing.TYPE_CHECKING:

        def visit(self, node: unit_graph.Node) -> dict[unit_graph.Identifier, float]:
            pass

    def generic_visit(self, node: unit_graph.Node):
        raise NotImplementedError(f"Not implemented for {type(node)}")

    def visit_Number(self, node: unit_graph.Identifier):
        return {}

    def visit_Identifier(self, node: unit_graph.Identifier):
        return {node: 1}

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
            scope[ut] *= node.rhs.content
        return scope

    def visit_Shift(self, node: unit_graph.Shift):
        # We can drop the shift value when doing dimensionality analysis.
        return self.visit(node.unit)

    def visit_Logarithm(self, node: unit_graph.Logarithm):
        # We can drop the logarithm when doing dimensionality analysis.
        return self.visit(node.term)
