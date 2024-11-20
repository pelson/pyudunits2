import pyudunits2


def test_version():
    assert pyudunits2.__version__ is not None


def test_public_api():
    # We keep close control of the public API, and validate all names that are
    # allowed here.
    public_vars = {
        name
        for name in vars(pyudunits2).keys()
        if not name.startswith("_") and name not in ["tests"]
    }
    assert public_vars == {
        "Unit",
        "Converter",
        "BasisUnit",
        "DateUnit",
        "DateTime",
        "NamedUnit",
        "UnitSystem",
        "UnresolvableUnitException",
        "IncompatibleUnitsError",
    }


def test_readme_example(capsys):
    # TODO: pull this out from the README automatically (or use doctest).

    ut_system = pyudunits2.UnitSystem.from_udunits2_xml()
    unit = ut_system.unit("km/h")  # May raise an UnresolvableUnitException

    meters = ut_system.unit("meters")

    print(
        f"Unit {unit} is a length unit?: {unit.dimensionality() == meters.dimensionality()}"
    )

    out, _ = capsys.readouterr()
    assert out.strip() == "Unit km/h is a length unit?: False"
