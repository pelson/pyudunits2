import argparse
import sys

from ._grammar import parse
from ._ud_xml import ToBasisVisitor, read_all, IdentifierLookupVisitor


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


def convert_handler(args: argparse.Namespace) -> None:
    raise NotImplementedError("Conversion not yet implemented")


def conv_expr_handler(args: argparse.Namespace) -> None:
    from_unit = parse(args.from_unit)
    to_unit = parse(args.to_unit)
    unit_system = read_all()

    converter_expr = unit_system.conversion_expr(from_unit, to_unit)
    print(
        f'To convert from "{from_unit}" to "{to_unit}", apply the following expression:'
    )
    print(converter_expr)


def explain_handler(args: argparse.Namespace) -> None:
    unit = parse(args.unit)
    unit_system = read_all()
    basis_unit = ToBasisVisitor(IdentifierLookupVisitor(unit_system)).visit(unit)
    print(f"Unit: {unit}")
    print(f"In basis form: {basis_unit}")


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
