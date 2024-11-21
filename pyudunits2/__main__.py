import argparse
import sys

from ._unit_system import UnitSystem
from ._unit import Converter
from ._exceptions import IncompatibleUnitsError
from ._grammar import _debug_tokens


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("unit", help="Tool for working with pyudunits2 from the CLI")

    # Don't do anything if the subcommand is not provided.
    parser.set_defaults(handler=None)

    subparsers = parser.add_subparsers()

    convert_subcommand = subparsers.add_parser(
        "convert", help="Convert a value from one unit to another"
    )
    convert_subcommand.add_argument("value", help="The value to convert")
    convert_subcommand.add_argument("from_unit", help="The unit of the value")
    convert_subcommand.add_argument("to_unit", help="The target unit")
    convert_subcommand.set_defaults(handler=convert_handler)

    conv_expr = subparsers.add_parser(
        "conversion-expr", help="Get the equation to convert from one unit to another"
    )
    conv_expr.add_argument("from_unit", help="The unit that you have")
    conv_expr.add_argument("to_unit", help="The unit that you want")
    conv_expr.set_defaults(handler=conv_expr_handler)

    explain = subparsers.add_parser(
        "explain-unit", help="Get (non machine readable) information about a unit"
    )
    explain.add_argument("unit", help="The unit to explain")
    explain.set_defaults(handler=explain_handler)

    explain = subparsers.add_parser(
        "debug-parser",
        help="Show debug information relating to the raw parsing of a unit",
    )
    explain.add_argument("unit", help="The unit to debug parsing for")
    explain.set_defaults(handler=debug_parsing_handler)


def convert_handler(args: argparse.Namespace) -> None:
    raise NotImplementedError("Conversion not yet implemented")


def conv_expr_handler(args: argparse.Namespace) -> None:
    unit_system = UnitSystem.from_udunits2_xml()
    from_unit = unit_system.unit(args.from_unit)
    to_unit = unit_system.unit(args.to_unit)

    try:
        converter = Converter(from_unit, to_unit)
    except IncompatibleUnitsError:
        print(f'It is not possible to convert from "{from_unit}" to "{to_unit}"')
        sys.exit(1)

    print(
        f'To convert from "{from_unit}" to '
        f'"{to_unit}", apply the following expression:'
    )
    print(converter.expression)


def explain_handler(args: argparse.Namespace) -> None:
    unit_system = UnitSystem.from_udunits2_xml()
    unit = unit_system.unit(args.unit)
    basis_unit = unit.expanded()
    print(f"Unit: {unit}")
    print(f"In basis form: {basis_unit}")
    print(f"Dimensionality: {unit.dimensionality()}")


def debug_parsing_handler(args: argparse.Namespace) -> None:
    _debug_tokens(args.unit)


def main() -> None:
    parser = argparse.ArgumentParser()
    configure_parser(parser)
    args = parser.parse_args(sys.argv)
    if args.handler is None:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args.handler(args)


if __name__ == "__main__":
    main()
