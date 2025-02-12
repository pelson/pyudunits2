from ._version import __version__ as __version__

# Public API
from ._unit import (
    Unit as Unit,
    BasisUnit as BasisUnit,
    DateUnit as DateUnit,
    DateTime as DateTime,
    NamedUnit as NamedUnit,
    Converter as Converter,
)
from ._unit_system import (
    UnitSystem as UnitSystem,
)
from ._exceptions import (
    UnresolvableUnitException as UnresolvableUnitException,
    IncompatibleUnitsError as IncompatibleUnitsError,
)

Unit.__module__ = __name__
BasisUnit.__module__ = __name__
DateUnit.__module__ = __name__
NamedUnit.__module__ = __name__
Converter.__module__ = __name__
UnitSystem.__module__ = __name__
UnresolvableUnitException.__module__ = __name__
IncompatibleUnitsError.__module__ = __name__
