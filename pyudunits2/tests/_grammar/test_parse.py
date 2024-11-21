import re

import pytest

import cf_units
from pyudunits2._grammar import normalize

testdata = [
    "",
    "1",
    "12",
    "1.2",
    "+1",
    "+1.2",
    "-1",
    "-1.2",
    "-1.2e0",
    "2e6",
    "2e-6",
    "2.e-6",
    ".1e2",
    ".1e2.2",
    "2e",  # <- TODO: Assert this isn't 2e1, but is in fact the unit e *2
    "m",
    "meter",
    # Multiplication
    "1 2 3",
    "1 -2 -3",
    "1m",
    "1*m",
    "2e3m",
    ".2m",
    "m·m",
    "1 m",
    "1   m",
    "m -1",
    "m -1.2",
    "m 1",
    "m 1000",
    "m 1.2",
    "m-+2",
    "m--4",
    "m*1*2",
    "m--2--3",
    # TODO: add some tests with brackets.
    "m(2.3)",
    "m(2.3m)",
    "(1.2)(2.4)",
    "(5m(6s-1))",
    "2*3*4/5m/6*7*8",
    "m/2",
    "m1",
    "m m",
    "m2",
    "m+2",
    "m¹",
    "m²",
    "m³",
    "2⁴",  # NOTE: Udunits can't do m⁴ for some reason. Bug?
    "2⁵",
    "2⁴²",
    "3⁻²",
    "m2 s2",
    "m^2*s^2",
    "1-2",
    "1-2-3",  # nb. looks a bit like a date, but it isn't!
    "m-1",
    "m^2",
    "m^+2",
    "m^-1",
    "m.2",  # This is 2*m
    "m.+2",  # 2*m
    "m.2.4",  # This is 2.4 * m
    "m0.2",  # But this is 2 m^0
    "m2.5",  # And this is 5m^2
    "m2.3.4",  # 0.4 * m^2
    "m--1",
    # Division
    "m per 2",
    "m per s",
    "m / 2",
    # Shift
    "m@10",
    "m @10",
    "m @ 10",
    "m@ 10",
    "m from2",
    "m from2e-1",
    "(m @ 10) (s @ 10)",
    # Date shift
    "s from 1990",
    "minutes since 1990",
    "hour@1990",
    "hours from 1990-1",
    "hours from 1990-1-1",
    "hours from 1990-1-1 0",
    "hours from 1990-1-1 0:1:1",
    "hours from 1990-1-1 0:0:1 +2",
    "seconds since 1970-01-01T00:00:00Z",
    "seconds since 1970-01Z",
    "seconds since 1970-01-10TZ",
    "seconds since 1970-01-10 Z",
    "seconds since 1970-01-10T00:00UTC",
    "seconds since 1970-01-10 00:00 GMT",
    "s since 2020-0101",  # Same as 2020-01T01
    "seconds since 20200101",  # Same as 2020-01-01
    "s since 1990-01-02 Z",  # But not "s since 1990-01-02 GMT"
    "s since 1990-1-2+5:2:2",
    "s since 1990-1-2+5:2",
    "s since 1990-1-2 5 6:0",  # Undocumented packed_clock format?
    "s since 19900102T5",  # Packed format (undocumented?)
    "s since 19900101T190030 +2",
    "s since 19900101T190030 GMT",
    "s since 199022T1",  # UGLY! (bug?).
    "s since 1990 +2:0:2.9",
    "s since 1990-2T1",
    "s since -1990 +2:0:2.9",
    "hours since 2001-12-31 23:59:59.999UTC",
    "hours since 2001-12-31 23:59:59.999 Z",
    "hours since 2001-12-31 23:59:59.999 GMT",
    "days since 1970-01-01T00:00:00 UTC",
    "hours since 2001-12-31TZ",
    "hours from 1990-1-1 -19:4:2",
    "hours from 1990-1-1 3+1",
    "seconds from 1990-1-1 0:0:0 +2550",
    "s since 1990-1-2+5:2:2",
    "hours from 1990-1-1 0:1:60",
    "hours from 1990-1-1 0:1:62",
    "(hours since 1900) (s since 1980)",  # Really fruity behaviour.
    "s since +1990 +2:0:2.9",
    "s since -1990 +2:0:2.9",
    # Unicode / constants
    "π",
    "e",
    "°C",
    # Logarithms (ln, lb, log, lg)
    "lg(re W)",
    "0.1 lg(re 1 mW)",
    "0.1 ln(re km^2)",
    "0.1 ln(re (K @ 10))",
    "lg(RE km)",
    "lb(re km)",
    "lb(re lb)",  # lb is also a valid unit identifier.
    "log(re km)",
    "lg(re log(re m))",  # udunits2 supports logs of logs.
    "log(re 1)^0",  # You can only raise to a zero power in udunits
    "log(re 1)-0",
    "log(re 1)0",
]

invalid = [
    "1 * m",
    "m--m",
    "-m",
    "m^n",
    ".1e2.",
    "m+-1",
    "--1",
    "+-1",
    "--3.1",
    "$",
    "£",
    "hours from 1990-0-0 0:0:0",
    "hours since 1900-1 10:12 10:0 1",
    "s since 1990:01:02T1900 +1",
    "s since 1990:01:02T1900 TZ",
    "s since 1990-01-02T1900 TZ",
    "s since 1990:01:02 GMT",
    "1990-1-1 12:00:00",  # This form is only valid after the shift op.
]


@pytest.mark.parametrize("_, unit_str", enumerate(testdata))
def test_normed_units_equivalent(_, unit_str):
    # nb: The "_" argument makes it easier to see which test was being run.

    # Get the udunits symbolic form for the raw unit.
    raw_symbol = cf_units.Unit(unit_str).symbol

    # Now get the parsed form of the unit, and then convert that to
    # symbolic form. The two should match.
    unit_expr = normalize(unit_str)
    if (
        unit_expr.startswith("(")
        and unit_expr.endswith(")")
        and unit_expr.count("(") == 1
    ):
        unit_expr = unit_expr[1:-1]
    parsed_expr_symbol = cf_units.Unit(unit_expr).symbol

    # Whilst the symbolic form from udunits is ugly, it *is* accurate,
    # so check that the two represent the same unit.
    assert raw_symbol == parsed_expr_symbol


@pytest.mark.parametrize("_, unit_str", enumerate(invalid))
def test_invalid_units(_, unit_str):
    # Confirm that invalid udunits-2 units are also invalid in our grammar.

    try:
        cf_units.Unit(unit_str)
        cf_valid = True
    except ValueError:
        cf_valid = False

    # Double check that udunits2 can't parse this.
    assert cf_valid is False, f"Unit {unit_str!r} is unexpectedly valid in UDUNITS2"

    try:
        normalize(unit_str)
        can_parse = True
    except SyntaxError:
        can_parse = False

    # Now confirm that we couldn't parse this either.
    msg = f"Parser unexpectedly able to deal with {unit_str}"
    assert can_parse is False, msg


def multi_enumerate(items):
    # Like enumerate, but flattens out the resulting index and items.
    return [[i, *item] for i, item in enumerate(items)]


not_udunits = [
    ["foo", "foo"],
    ["mfrom1", "mfrom^1"],
    ["m⁴", "m^4"],  # udunits bug.
    ["2¹²³⁴⁵⁶⁷⁸⁹⁰", "2^1234567890"],
    ["m⁻²", "m^-2"],
    ["0.1 ln(re K @ 10)", "0.1·(ln(re (K @ 10)))"],
    ["LOG(re W)", "LOG·re·W"],  # LOG cannot be uppercase. But can be an id.
    ["log(re 1)^2", "(log(re 1))^2"],  # It is not possible to raise a log term.
    ["log(re 1)2", "(log(re 1))^2"],  # It is not possible to raise a log term.
    ["log(re 1)-1", "(log(re 1))^-1"],  # It is not possible to raise a log term.
    ["log(re re)", "(log(re re))"],  # parses, but not UT_UNKNOWN.
    # Unicode (subset of the subset).
    ["À"] * 2,
    ["Á"] * 2,
    ["Ö"] * 2,
    ["Ø"] * 2,
    ["ö"] * 2,
    ["ø"] * 2,
    ["ÿ"] * 2,
    ["µ"] * 2,
    ["µ°F·Ω⁻¹", "µ°F·Ω^-1"],
    #  Not a valid unit (but with Z instead of GMT it would be fine)
    ["s since 1990-01-02 GMT", "(s @ 1990-01-02 GMT)"],
    ["UTC"] * 2,  # Nothing special - it is a valid identifier name normally.
]


@pytest.mark.parametrize("_, unit_str, expected", multi_enumerate(not_udunits))
def test_invalid_in_udunits_but_still_parses(_, unit_str, expected):
    # Some units read fine in our grammar, but not in UDUNITS.

    try:
        cf_units.Unit(unit_str)
        cf_valid = True
    except ValueError:
        cf_valid = False

    # Double check that udunits2 can't parse this.
    assert cf_valid is False

    unit_expr = normalize(unit_str)
    assert unit_expr == expected


known_issues = [
    ["days since 2000)", SyntaxError],  # Unbalanced parentheses work in udunits2.
]


@pytest.mark.parametrize("_, unit_str, expected", multi_enumerate(known_issues))
def test_known_issues(_, unit_str, expected):
    # Unfortunately the grammar is not perfect.
    # These are the cases that don't work yet but which do work with udunits.

    # Make sure udunits can read it.
    _ = cf_units.Unit(unit_str).symbol

    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(SyntaxError):
            unit_expr = normalize(unit_str)
    else:
        unit_expr = normalize(unit_str)
        assert unit_expr != expected


def test_syntax_parse_error_quality():
    # Check that the syntax error is giving us good context.

    msg = re.escape(r"no viable alternative at input 'm^m' (inline, line 1)")
    with pytest.raises(SyntaxError, match=msg) as err:
        normalize("m^m 2s")
    # The problem is with the m after "^", so make sure the exception is
    # pointing at it (including the leading speechmark).
    assert err.value.offset == 4


def test_unknown_symbol_error():
    msg = re.escape(r"mismatched input '×' expecting <EOF>")
    with pytest.raises(SyntaxError, match=msg) as err:
        # The × character is explicitly excluded in the UDUNITS2
        # implementation. It would make some sense to support it in the
        # future though.
        normalize("Thing×Another")
    # The 7th character (including the speechmark) is the problem, check that
    # the exception points at the right location.
    # correct location...
    #  File "inline", line 1
    #  'Thing×Another'
    #        ^
    assert err.value.offset == 7


not_allowed = [
    "hours from 1990-1-1 -20:4:18 +2",
    "m++2",
    "m s^(-1)",
    "m per /s",
    "s @ UTC",
]


@pytest.mark.parametrize("_, unit_str", enumerate(not_allowed))
def test_invalid_syntax_units(_, unit_str):
    # Check that units that aren't allowed with UDUNITS-2 are also not
    # allowed with our grammar.

    with pytest.raises(ValueError):
        _ = cf_units.Unit(unit_str).symbol

    with pytest.raises(SyntaxError):
        normalize(unit_str)
