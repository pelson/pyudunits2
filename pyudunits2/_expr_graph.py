# Copyright cf-units contributors
#
# This file is part of cf-units and is released under the BSD license.
# See LICENSE in the root of the repository for full licensing details.
from __future__ import annotations


class Node:
    """
    Represents a node in an expression graph.

    """

    def __init__(self, **kwargs):
        self._attrs = kwargs

    def children(self) -> list[Node]:
        """
        Return the children of this node.

        """
        # Since this is py>=36, the order of the attributes is well defined.
        return list(self._attrs.values())

    def __getattr__(self, name):
        # Allow the dictionary to raise KeyError if the key doesn't exist.
        return self._attrs[name]

    def _repr_ctx(self):
        # Return a dictionary that is useful for passing to string.format.
        kwargs = ", ".join(f"{key}={value!r}" for key, value in self._attrs.items())
        return {"cls_name": self.__class__.__name__, "kwargs": kwargs}

    def __repr__(self):
        return "{cls_name}({kwargs})".format(**self._repr_ctx())


class Terminal(Node):
    """
    A generic terminal node in an expression graph.

    """

    def __init__(self, content):
        super().__init__(content=content)

    def children(self):
        return []

    def __str__(self):
        return f"{self.content}"

    def __eq__(self, other: Node) -> bool:
        if type(self) is type(other):
            return self.content == other.content
        else:
            return NotImplemented


class Operand(Terminal):
    pass


class Number(Terminal):
    pass


class Identifier(Terminal):
    """The unit itself (e.g. meters, m, km and π)"""

    content: str

    def __hash__(self):
        return hash(self.content)


class UnaryOp(Node):
    def __init__(self, function: str, term: Node):
        super().__init__(function=function, term=term)

    def children(self) -> list[Node]:
        return [self.term]

    def __repr__(self):
        return f"{self.function}({self.term})"


class BinaryOp(Node):
    def __init__(self, lhs, rhs):
        super().__init__(lhs=lhs, rhs=rhs)


class Raise(BinaryOp):
    def __str__(self):
        return f"{self.lhs}^{self.rhs}"


class Multiply(BinaryOp):
    def __str__(self):
        return f"{self.lhs}·{self.rhs}"


class Divide(BinaryOp):
    def __str__(self):
        # TODO: It may be necessary to put brackets around
        #  sthe rhs, depending on context (e.g. if rhs is a multiply)
        return f"{self.lhs}/{self.rhs}"


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

    def __init__(self, unit, shift_from):
        # The product unit to be shifted.
        super().__init__(unit=unit, shift_from=shift_from)

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
