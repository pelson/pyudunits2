class ArgEnumerator:
    def __init__(self):
        self._counter = 0

    def __call__(self, item):
        self._counter += 1
        if self._counter % 2:
            return f"{(self._counter - 1)//2}__{item}"
        else:
            return str(item)


# @pytest.mark.parametrize(
#     ["unit_str", "sympy_transformation", "sympy_def"],
#     [
#         ["2", "qty", "2"],
#         [".1", "qty", "0.1"],
#         ["1e-2", "qty", "0.01"],
#         ["s", "qty", "s"],
#         ["s @ 2", "qty + 2", "s"],
#         ["5 (s @ 2)^2", "qty*(qty + 2)**2", "5*s**2"],  # From udunits: 5 (s @ 2)^2 = 5 s**2 # TODO: While correct, this is inconsistent with udunits
#         ["m/s", "qty", "m/s"],
#         ["lg(re years)", "log(qty)/log(10)", "years"],
#
#         ["lg(re years/2)", "log(qty)/log(10)", "years/2"],  # From udunits: 10 lg(re years/2) = 5e+09 years
#         ["2 lg(re years)", "log(qty)/log(10)", "2*years"],  # Note that we don't raise years**2 here.
#
#         ["5lg(re m2)", "log(qty)/log(10)", "5*m**2"],
#         ["5ln(re m2)", "log(qty)", "5*m**2"],
#         ["a lb(re m @ 4)", "log(4*qty)/log(2)", "a*m"],
#     ],
#     ids=ArgEnumerator(),
# )
# def test_to_sympy2(unit_str: str, sympy_transformation: str, sympy_def: str):
#     expr = parse(unit_str)
#
#     res_value_transform, res_definition = ToSympy().visit(expr)
#     assert isinstance(res_value_transform, sympy.core.expr.Expr)
#     assert isinstance(res_definition, sympy.core.expr.Expr)
#
#     assert str(res_value_transform) == str(sympy_parse(sympy_transformation))
#     assert str(res_definition) == str(sympy_parse(sympy_def))
#
