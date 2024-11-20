from pyudunits2._datetime import parse_udunits_date, DateTime
from pyudunits2._grammar import parse
import pytest


@pytest.mark.xfail(strict=True)
@pytest.mark.parametrize(
    ["date_expr", "expected"],
    [
        # ['2000T1', DateTime(2000, 1, 1)],
        # ['2000', DateTime(2000, 1, 1)],
        ["00010101", DateTime(1, 1, 1)],
        ["+00010101", DateTime(1, 1, 1)],
        ["-00010101", DateTime(-1, 1, 1)],
    ],
)
def test_parse_udunits_date(date_expr: str, expected: DateTime):
    date_node = parse(f"seconds @ {date_expr}").shift_from
    # TODO: get the original content, not the parsed content.
    date_ref = parse_udunits_date(date_node.content)
    assert date_ref == expected
