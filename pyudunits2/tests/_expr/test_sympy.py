from pyudunits2._expr.sympy import ToSympy


from pyudunits2._grammar import parse
import sympy.core.expr

from sympy.parsing.sympy_parser import parse_expr as sympy_parse
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
    ["unit_str", "sympy_expr"],
    [
        ["2", "2"],
        [".1", "0.1"],
        ["1e-2", "0.01"],
        ["s", "s"],
        ["s @ 2", "s - 2"],
        ["(s @ 2)^2", "(s - 2)**2"],
        ["m/s", "m/s"],
        ["5lg(re m2)", "5*log(m**2)/log(10)"],
        ["5ln(re m2)", "5*log(m**2)"],
        ["a lb(re m @ 4)", "a*log(m - 4)/log(2)"],
    ],
    ids=ArgEnumerator(),
)
def test_to_sympy(unit_str: str, sympy_expr: str):
    expr = parse(unit_str)

    result = ToSympy().visit(expr)
    assert isinstance(result, sympy.core.expr.Expr)
    assert str(result) == str(sympy_parse(sympy_expr))
