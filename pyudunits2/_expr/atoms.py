from .graph import Visitor
import typing
from . import graph as unit_graph


# class AtomExtractor(Visitor):
#     """
#     Behaves like sympy's atoms method, where you can search for all elements in
#     the graph of a matching type.
#
#     """
#     def __init__(self, types: typing.Union[typing.Type, typing.Sequence[typing.Type]]):
#         self._types = types
#
#     if typing.TYPE_CHECKING:
#
#         def visit(self, node: unit_graph.Node) -> typing.Sequence[unit_graph.Node]:
#             pass
#
#     def generic_visit(self, node: unit_graph.Node):
#         raise NotImplementedError(f"Not implemented for {type(node)}")
#
#     def visit_Number(self, node: unit_graph.Identifier):
#         return {}
#
#     def visit_Identifier(self, node: unit_graph.Identifier):
#         return {node.content: 1}
#
#     def visit_UnitNode(self, node: UnitNode):
#         return {node.content: 1}
#
#     def visit_Multiply(self, node: unit_graph.Multiply):
#         scope = self.visit(node.lhs)
#         for ut, order in self.visit(node.rhs).items():
#             scope[ut] = scope.get(ut, 0) + order
#         return scope
#
#     def visit_Divide(self, node: unit_graph.Divide):
#         scope = self.visit(node.lhs)
#         rhs_scope = self.visit(node.rhs)
#         for ut, order in rhs_scope.items():
#             scope[ut] = scope.get(ut, 0) - order
#         return scope
#
#     def visit_Raise(self, node: unit_graph.Raise):
#         assert isinstance(node.rhs, unit_graph.Number)
#         scope = self.visit(node.lhs)
#         for ut in scope:
#             scope[ut] += node.rhs.content - 1
#         return scope
#
#     def visit_Shift(self, node: unit_graph.Shift):
#         # We can drop the shift value when doing dimensionality analysis.
#         return self.visit(node.unit)
#
#     def visit_Logarithm(self, node: unit_graph.Logarithm):
#         # We can drop the logarithm when doing dimensionality analysis.
#         return self.visit(node.term)


class ExtractIdentifiers(Visitor):
    def visit_Identifier(
        self, node: unit_graph.Identifier
    ) -> typing.Set[unit_graph.Identifier]:
        return {node}

    def generic_visit(self, node: unit_graph.Node) -> typing.Set[unit_graph.Identifier]:
        result = set()

        for child in node.children():
            result |= self.visit(child)
        return result
