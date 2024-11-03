import textwrap
import pytest
from pyudunits2.__main__ import main


def test__explain_unit(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["pyudunits2", "explain-unit", "mg"])
    main()
    out, err = capsys.readouterr()
    expected_output = textwrap.dedent("""
        Unit: mg
        In basis form: 0.001·0.001·kilogram
        Dimensionality: {'kilogram': 1}
    """).strip()
    assert err == ""
    assert out.strip() == expected_output


def test__conversion_expr__possible(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv", ["pyudunits2", "conversion-expr", "mg", "lg(re grams)"]
    )
    main()
    out, err = capsys.readouterr()
    expected_output = textwrap.dedent("""
        To convert from "mg" to "(lg(re grams))", apply the following expression:
        log(0.001*value)/log(10)
    """).strip()
    assert err == ""
    assert out.strip() == expected_output


def test__conversion_expr__inversion(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["pyudunits2", "conversion-expr", "m/s", "s/m"])
    main()
    out, err = capsys.readouterr()
    expected_output = textwrap.dedent("""
            To convert from "m/s" to "s/m", apply the following expression:
            1/value
        """).strip()
    assert err == ""
    assert out.strip() == expected_output


def test__conversion_expr__impossible(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["pyudunits2", "conversion-expr", "mg", "meters"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
    out, err = capsys.readouterr()
    expected_output = textwrap.dedent("""
        It is not possible to convert from "mg" to "meters"
    """).strip()
    assert err == ""
    assert out.strip() == expected_output
