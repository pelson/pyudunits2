from __future__ import annotations

import contextlib
import logging
import typing

from . import graph as unit_graph
from .graph import Node, Visitor


_log = logging.getLogger(__name__)


class ChainedExpr:
    # Represents 2 or more multiplications raised to a numeric power.
    def __init__(self):
        self._chain: list[tuple[unit_graph.Terminal, int]] = []

    def add_term(self, term: unit_graph.Terminal, raised_to: int) -> None:
        self._chain.append((term, raised_to))

    def terms(self) -> unit_graph.Node:
        # Sort the expression chain by contents that can potentially be
        # combined.
        t = sorted(
            self._chain,
            key=lambda item: (
                str(type(item[0].content)),
                str(item[0].content),
            ),
            reverse=True,
        )
        terms = []

        # Iterate over each of the nodes, and try to combine with the previous
        # one.
        for node, raised_to in t[::-1]:
            term = node
            if raised_to == 0:
                continue
            elif raised_to != 1:
                term = unit_graph.Raise(
                    node, unit_graph.Number(raised_to, raw_content=None)
                )

            if terms:
                last_term = terms[-1]
            else:
                # There is nothing to combine with, so let's move to the
                # next term.
                terms.append(term)
                continue

            # Try to combine this node with the previous one.

            if isinstance(last_term, unit_graph.Terminal) and last_term == node:
                # a · a^n == a^(n+1)

                # We can combine the two terms, so pop the last one.
                assert terms.pop() is last_term
                new_exponent = raised_to + 1
                if new_exponent == 0:
                    # Both terms have cancelled out to 1. We don't need any
                    # terms to represent this.
                    _log.debug(
                        'Combined form "a · a^n"; '
                        f"Expr: {last_term} · {node}^{raised_to} == 1"
                    )
                    continue
                else:
                    new_term = unit_graph.Raise(
                        node,
                        unit_graph.Number(new_exponent, raw_content=None),
                    )
                _log.debug(
                    'Combined form "a · a^n"; '
                    f"Expr: {last_term} · {node}^{raised_to} == {new_term}"
                )
                terms.append(new_term)

            elif (
                isinstance(last_term, unit_graph.Terminal)
                and isinstance(last_term, unit_graph.Number)
                and isinstance(node, unit_graph.Number)
                and type(node.content) is type(last_term.content)
                and isinstance(raised_to, int)
                and raised_to > 0
            ):
                # a · b^n == a*(b^n); Where a and b are numbers of the same
                #                     type (float / int)

                # We can combine the two terms, so pop the last one.
                assert terms.pop() is last_term
                new_term = unit_graph.Number(
                    last_term.content * (node.content**raised_to),
                    raw_content=None,
                )
                _log.debug(
                    'Combined form "a · b^n"; '
                    f"Expr: {last_term} · {node}^{raised_to} == {new_term}"
                )
                terms.append(new_term)

            elif (
                isinstance(last_term, unit_graph.Raise)
                and isinstance(last_term.rhs, unit_graph.Number)
                and last_term.lhs == node
            ):
                # a^n · a^m == a^(n+m); Where n and m are numbers.

                # We can combine the two terms, so pop the last one.
                assert terms.pop() is last_term
                new_exponent = last_term.rhs.content + raised_to
                if new_exponent == 0:
                    # Both terms have cancelled out to 1. We don't need any
                    # terms to represent this.
                    _log.debug(
                        'Combined form "a^n · a^m" == a^(n+m); '
                        f"Expr: {last_term} · {node}^{raised_to} == 1"
                    )
                    continue
                elif new_exponent == 1:
                    # We don't need to raise anymore.
                    new_term = last_term.lhs
                else:
                    new_term = unit_graph.Raise(
                        node,
                        unit_graph.Number(new_exponent, raw_content=None),
                    )
                _log.debug(
                    'Combined form "a^n · a^m == a^(n+m)"; '
                    f"Expr: {last_term} · {node}^{raised_to} == {new_term}"
                )
                terms.append(new_term)

            else:
                terms.append(term)

        result = unit_graph.Number(1, raw_content=None)
        if len(terms) == 1:
            result = terms[0]
        elif len(terms) > 1:
            result = terms.pop()
            for term in terms[::-1]:
                result = unit_graph.Multiply(term, result)
        return result


class Expander(Visitor):
    def __init__(self):
        self._expansion: list[ChainedExpr] = [ChainedExpr()]
        self._offset_terms: list[ChainedExpr] = [ChainedExpr()]

    def generic_visit(self, node: unit_graph.Node):
        raise NotImplementedError(f"Not implemented for {type(node)}")

    def visit_internal(self, node):
        return super().visit(node)

    def visit(self, node):
        _ = self.visit_internal(node)
        terms = self._expansion[-1].terms()
        if self._offset_terms[-1]._chain:
            terms = unit_graph.Shift(terms, self._offset_terms[-1].terms())
        return terms

    @contextlib.contextmanager
    def expr_context(
        self,
    ) -> typing.Generator[tuple[ChainedExpr, ChainedExpr]]:
        expansion = ChainedExpr()
        offset = ChainedExpr()
        self._expansion.append(expansion)
        self._offset_terms.append(offset)
        yield expansion, offset
        self._expansion.pop()
        self._offset_terms.pop()

    def visit_Multiply(self, node: unit_graph.Multiply):
        self.visit_internal(node.lhs)
        with self.expr_context() as (expansion, offset):
            self.visit_internal(node.rhs)

        for term, raise_to in expansion._chain:
            self._expansion[-1].add_term(term, raise_to)

        for term, raise_to in offset._chain:
            # TODO: Figure out what this should be.
            self._offset_terms[-1].add_term(term, raise_to)

    def visit_Divide(self, node: unit_graph.Divide):
        self.visit_internal(node.lhs)
        with self.expr_context() as (expansion, offset):
            self.visit_internal(node.rhs)

        for term, raise_to in expansion._chain:
            self._expansion[-1].add_term(term, -raise_to)

        for term, raise_to in offset._chain:
            # TODO: Figure out what this should be.
            self._offset_terms[-1].add_term(term, raise_to)

        # expansion = ChainedExpr()
        # self._expansion.append(expansion)
        # self.visit_internal(node.rhs)
        # self._expansion.pop()
        # for term, raise_to in expansion._chain:
        #     self._expansion[-1].add_term(term, -raise_to)
        # self._expansion[-1]._offset -= expansion._offset

    def visit_Identifier(self, node: unit_graph.Identifier):
        self._expansion[-1].add_term(node, 1)

    def visit_Number(self, node: unit_graph.Number):
        self._expansion[-1].add_term(node, 1)

    def visit_Raise(self, node: unit_graph.Raise):
        with self.expr_context() as (expansion, offset):
            self.visit_internal(node.lhs)

        assert isinstance(node.rhs, unit_graph.Number)
        for term, raise_to in expansion._chain:
            self._expansion[-1].add_term(term, raise_to * node.rhs.content)
        for term, raise_to in offset._chain:
            self._offset_terms[-1].add_term(term, raise_to * node.rhs.content)

    def visit_Shift(self, node: unit_graph.Shift):
        self.visit_internal(node.unit)
        with self.expr_context() as (expansion, offset):
            self.visit_internal(node.shift_from)

        if offset._chain:
            raise ValueError("Chain:", str(offset.terms()))
        assert not offset._chain

        # Copy over the expansion into the offset.
        for term, raise_to in expansion._chain:
            # print("F:", term, raise_to)
            self._offset_terms[-1].add_term(term, raise_to)
        # self._offset_terms[-1].node.shift_from.content


class SimplifyingVisitor(Visitor):
    def visit_Divide(self, node: unit_graph.Divide):
        lhs = self.visit(node.lhs)
        rhs = self.visit(unit_graph.Raise(node.rhs, unit_graph.Number(-1)))
        return self.visit(unit_graph.Multiply(lhs, rhs))

    def generic_visit(self, node: unit_graph.Node):
        raise NotImplementedError(f"Not implemented for {type(node)}")

    def _no_op(self, node: unit_graph.Node):
        return node

    def visit(self, node: Node):
        result = self.visit_internal(node)
        # Sort and strip the result.

        return result

    def visit_internal(self, node: unit_graph.Node):
        # Like visit, except we don't simplify the final unit.
        result = super().visit(node)
        return result

    visit_Identifier = _no_op
    visit_Number = _no_op

    def visit_Multiply(self, node: unit_graph.Multiply):
        lhs = self.visit_internal(node.lhs)
        rhs = self.visit_internal(node.rhs)
        # TODO: Sort & try to combine terms if we can.

        if isinstance(lhs, unit_graph.Identifier) and isinstance(
            rhs, unit_graph.Identifier
        ):
            if lhs.content == rhs.content:
                return unit_graph.Raise(lhs, 2)
            else:
                lhs, rhs = sorted([lhs, rhs], key=lambda identifier: identifier.content)
                return unit_graph.Multiply(lhs, rhs)
        elif (
            isinstance(lhs, unit_graph.Identifier)
            and isinstance(rhs, unit_graph.Raise)
            and isinstance(rhs.lhs, unit_graph.Identifier)
        ):
            if lhs.content == rhs.content:
                return unit_graph.Raise(lhs, 2)
            else:
                lhs, rhs = sorted([lhs, rhs], key=lambda identifier: identifier.content)
                return unit_graph.Multiply(lhs, rhs)

        return unit_graph.Multiply(lhs, rhs)

    def visit_Raise(self, node: unit_graph.Raise):
        assert isinstance(node.rhs, unit_graph.Number)
        lhs = self.visit_internal(node.lhs)
        if isinstance(lhs, unit_graph.Terminal):
            return unit_graph.Raise(lhs, node.rhs)
        elif isinstance(lhs, unit_graph.Multiply):
            # Expand multiplications such (AB)^2 becomes A^2.B^2
            g = unit_graph.Multiply(
                unit_graph.Raise(self.visit_internal(lhs.lhs), node.rhs),
                unit_graph.Raise(self.visit_internal(lhs.rhs), node.rhs),
            )
            return g
        else:
            return unit_graph.Raise(self.visit_internal(lhs.lhs), node.rhs)
