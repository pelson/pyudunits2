from __future__ import annotations

import dataclasses
import decimal


@dataclasses.dataclass(frozen=True)
class Node:
    """
    Represents a node in an expression graph.

    """

    def children(self) -> list[Node]:
        """
        Return the children of this node.

        """
        return [
            getattr(self, field.name)
            for field in dataclasses.fields(self)
            if isinstance(getattr(self, field.name), Node)
        ]


@dataclasses.dataclass(frozen=True)
class Terminal(Node):
    """
    A generic terminal node in an expression graph.

    """

    def children(self):
        return []

    # def __str__(self):
    #     return f"{self.raw_content}"

    @property
    def content(self):
        # Provide a convenient interface to the terminal.
        raise NotImplementedError("Subclass must implement")


@dataclasses.dataclass(frozen=True)
class Unhandled(Terminal):
    raw_content: str

    @property
    def content(self):
        return self.raw_content

    def __str__(self):
        return str(self.raw_content)


@dataclasses.dataclass(frozen=True)
class Number(Terminal):
    value: decimal.Decimal | int
    raw_content: str | None

    @property
    def content(self):
        return self.value

    def __str__(self):
        return str(self.value)


@dataclasses.dataclass(frozen=True)
class Identifier(Terminal):
    """The unit itself (e.g. meters, m, km and π)"""

    name: str

    @property
    def content(self):
        return self.name

    def __str__(self):
        return str(self.name)


@dataclasses.dataclass(frozen=True)
class UnaryOp(Node):
    function: str
    term: Node

    # def children(self) -> list[Node]:
    #     return [self.term]

    def __repr__(self):
        return f"{self.function}({self.term})"


@dataclasses.dataclass(frozen=True)
class BinaryOp(Node):
    lhs: Node
    rhs: Node


class Raise(BinaryOp):
    def __str__(self):
        return f"{self.lhs}^{self.rhs}"


class Multiply(BinaryOp):
    def __str__(self):
        return f"{self.lhs}·{self.rhs}"


class Divide(BinaryOp):
    def __str__(self):
        # TODO: It may be necessary to put brackets around
        #  the rhs, depending on context (e.g. if rhs is a multiply)
        return f"{self.lhs}/{self.rhs}"


@dataclasses.dataclass(frozen=True)
class Shift(Node):
    """
    You have: years @ 5
    You want: years
    udunits2: Units are not convertible

    You have: K @ 273.15
    You want: K
        1 K @ 273.15 = 274.15 K
        x/K = (x/(K @ 273.15)) + 273.15

    You have: years @ 5.0
    You want: years
        1 years @ 5.0 = 6 years
        x/years = (x/(years @ 5.0)) + 5

    You have: lg(re years @ 5.0)
    udunits2: Don't recognize "lg(re years @ 5.0)"

    You have: lg(re (years @ 5.0))
    You want: years
        1 lg(re (years @ 5.0)) = 15 years
        x/years = 3.16888e-08*(3.15569e+07*(pow(10, (x/(lg(re (years @ 5.0)))))) + 1.57785e+08)

    """

    unit: Node

    #: The product unit to be shifted.
    shift_from: Node

    def __str__(self):
        return f"({self.unit} @ {self.shift_from})"


class Logarithm(UnaryOp):
    def __str__(self):
        return f"({self.function}(re {self.term}))"


class Visitor:
    """
    This class may be used to help traversing an expression graph.

    It follows the same pattern as the Python ``ast.NodeVisitor``.
    Users should typically not need to override either ``visit`` or
    ``generic_visit``, and should instead implement ``visit_<ClassName>``.

    This class is used in cf_units.tex to generate a tex representation
    of an expression graph.

    """

    def visit(self, node: Node):
        """Visit a node."""
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: Node):
        """
        Called if no explicit visitor function exists for a node.

        Can also be called by ``visit_<ClassName>`` implementations
        if children of the node are to be processed.

        """
        return [self.visit(child) for child in node.children()]
