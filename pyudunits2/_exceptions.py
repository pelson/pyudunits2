class UnresolvableUnitException(ValueError):
    """
    Raised when a unit cannot be resolved in a unit system.

    """

    pass


class IncompatibleUnitsError(ValueError):
    """
    Raised when two units cannot be converted from one to the other
    """
