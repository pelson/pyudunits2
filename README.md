# pyudunits2

### NOTE: This project is not yet adopted and remains a proof-of-concept. Please open an issue to express your interest in helping to maintain this project.

**`pyudunits2`** is a pure Python library designed for handling units of physical
quantities, fully based on the UDUNITS2 grammar and XML database.
It provides seamless unit conversions and symbolic unit manipulation, making
it an ideal tool for scientific and engineering applications.
Furthermore, as a result of its compatibility with the UDUNITS2 grammar,
`pyudunits2` is  suitable for working with the
[Climate Forecast (CF) conventions][CF Conventions].


## Key Features

- **UDUNITS2 Grammar**: The library has a generated parser based on a unit
  grammar definition adapted from UDUNITS2, ensuring the grammar serves as the
  canonical source of truth.
- **Unit Conversions**: Easily convert between related units using optimised and
  vectorised functions.
- **Symbolic Representation**: Unit symbols are preserved throughout
  calculations, ensuring precise definitions remain intact.
- **Optimized Performance**: When using the UDUNITS2 XML database without
  extensions, the code follows an optimized path for efficiency. (Not yet implemented)
- **Flexible Simplification**: By default, units are not reduced to base units
  until simplification is explicitly requested, allowing expressions like
  `mg kg-1` for a mass ratio and `microlitres per litre` for a volume ratio to
  be propagated through calculations.
- **Command-Line Interface (CLI)**: Includes a CLI tool for convenient unit
  conversion using the UDUNITS2 database.

## Examples

Determining if a unit is a length like unit:

```python
>>> from pyudunits2 import UnitSystem

>>> ut_system = UnitSystem.from_udunits2_xml()
>>> unit = ut_system.unit('km/h')
>>> # Note that creating a unit may raise a pyudunits2.UnresolvableUnitException

>>> meters = ut_system.unit('meters')

>>> print(f'Unit {unit} is a length unit?: {unit.dimensionality() == meters.dimensionality()}')
Unit km/h is a length unit?: False
```

Converting between units:

```python
>>> from pyudunits2 import UnitSystem, Converter
>>> import numpy as np

>>> ut_system = UnitSystem.from_udunits2_xml()
>>> degC = ut_system.unit('degC')
>>> kelvin = ut_system.unit('kelvin')
>>> converter = Converter(degC, kelvin)
>>> print(converter.expression)
value + 273.15
>>> converter.convert(np.array([32, 15, -20]))
array([305.15, 288.15, 253.15])
```

## Command line interface (CLI)

The `pyudunits2` CLI offers a number of useful tools for working with `udunits2`
units. For the complete help, see `python -m pyudunits2 --help`.

### explain-unit

It is possible to get human-readable information about a unit.
This information is not intended to be machine readable, can change in the
future, and should not be parsed for any purpose.

For example:

```
$ python -m pyudunits2 explain-unit degC
```


### conversion-expr

Produces a somewhat machine-readable form of the expression required to convert
from one unit to another.

For example:

```
$ python -m pyudunits2 conversion-expr degC degF
1.8*value + 31.2
```


## Alternative unit libraries

There are many unit libraries available within Python. A good default choice
would be [Pint](https://pint.readthedocs.io/en/stable/) which offers a
compelling user experience and a comprehensive base unit definition.

`pyudunits2` unique selling point is its re-implementation of the UDUNITS2
grammar, which is a fundamental part of the
[CF Conventions specification][CF Conventions]. Tight integration between
`pyudunits2` and `Pint` would be a desirable outcome for this library.

The [`cf-units`][cf-units] library wraps the `UDUNITS2` C-API (using Cython)
and offers an alternative approach to supporting UDUNITS2 based unit
definitions. The complexity of having a compiled `cf-units` has been shown to
be a source of pain for both maintenance and use <sup>
[1](https://github.com/SciTools/cf-units/issues/446)
[2](https://github.com/ioos/compliance-checker/pull/1094)
</sup>.  

The [`xclim`](https://github.com/Ouranosinc/xclim) library offers some powerful
`UDUNITS2`-like functionality. It is hoped that `pyudunits2` could serve as a
basis for that library in the future.


[CF Conventions]: https://cfconventions.org/
[cf-units]: https://github.com/SciTools/cf-units