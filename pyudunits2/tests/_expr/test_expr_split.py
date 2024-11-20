from types import NoneType

from pyudunits2._expr.split import SplitExpr

from pyudunits2._grammar import parse
from pyudunits2._expr import graph as g

import pytest


class ArgEnumerator:
    def __init__(self):
        self._counter = 0

    def __call__(self, item):
        self._counter += 1
        if self._counter % 2:
            return f"{(self._counter - 1)//2}__{item}"
        else:
            return str(item)


@pytest.mark.parametrize(
    ["unit_str", "value_transformation", "base_definition"],
    [
        ["2", None, "2"],
        ["5·m", None, "5·m"],
        [".1", None, "0.1"],
        ["1e-2", None, "0.01"],
        ["s", None, "s"],
        ["s @ 2", "(value @ 2)", "s"],
        ["(s @ 2)*1", "value·1", "s"],
        ["5 (s @ 2)^2", "5·value", "s^2"],
        ["m/s", None, "m/s"],
        ["lg(re years)", "(lg(re value))", "years"],
        ["lg(re years/2)", "(lg(re value))", "years/2"],
        ["2 lg(re years)", "2·(lg(re value))", "years"],
        ["5lg(re m2)", "5·(lg(re value))", "m^2"],
        ["5ln(re m2)", "5·(ln(re value))", "m^2"],
        ["ln(re m2)·5", "(ln(re value))·5", "m^2"],
        ["a lb(re m @ 4)", "a·(lb(re value))", "m"],
        ["(lb(re m)) @ 2", "((lb(re value)) @ 2)", "m"],
        ["a lb(re m @ 3) @ 4", "(a·(lb(re value)) @ 4)", "m"],
        ["a lb(re lg(re m2/s))", "a·(lb(re (lg(re value))))", "m^2/s"],
        # ["lg(re m2)*lg(re s)", "log(4*qty)/log(2)", "m2/s"],  # Udunits can't handle this
    ],
    ids=ArgEnumerator(),
)
def test__split_expression(
    unit_str: str, value_transformation: str | None, base_definition: str
):
    expr = parse(unit_str)

    res_value_transform, res_definition = SplitExpr(expr).visit(expr)
    assert isinstance(res_value_transform, (NoneType, g.Node))
    assert isinstance(res_definition, g.Node)

    assert str(res_value_transform) == str(value_transformation)
    assert str(res_definition) == base_definition
