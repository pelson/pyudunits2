from __future__ import annotations

# Gold dust. https://github.com/Unidata/MetPy/issues/1362
import dataclasses
import logging
import typing
from pathlib import Path

from lxml import etree

from ._unit_reference import Prefix, Name, UnitReference
from ._unit import BasisUnit, Unit
from ._unit_system import UnitSystem, LazilyDefinedUnit


_log = logging.getLogger(__name__)
XML_path = Path(__file__).parent / "udunits2_combined.xml"


@dataclasses.dataclass
class Tag:
    # A mutable representation of an XML tag.
    # We drop the namespace intentionally - it has no value in the UDUNITS2
    # XML representation.
    # We strip text intentionally - it is known to be spacious in the
    # UDUNITS2 XML representation.

    name: str
    children: list[Tag]
    text: str | None

    @classmethod
    def from_element(cls, element: etree.Element) -> Tag:
        _, _, tag_name = element.tag.partition("}")

        text = (element.text or "").strip()
        children = []

        if len(element) > 0:
            for child in element:
                children.append(cls.from_element(child))
        return cls(name=tag_name, text=text, children=children)

    def pop_first_matching_tag(self, tag_name: str) -> Tag | None:
        for child in self.children[:]:
            if child.name == tag_name:
                self.children.remove(child)
                return child
        return None

    def pop_exactly_one(self, tag_name: str) -> Tag:
        raise NotImplementedError("s")

    def pop_iter_tags(self, tag_name: str) -> typing.Generator[Tag]:
        for child in self.children[:]:
            if child.name == tag_name:
                self.children.remove(child)
                yield child


class UDUNITS2XMLParser:
    @classmethod
    def handle_name_tag(cls, tag: Tag) -> Name:
        singular_name_tag = tag.pop_first_matching_tag("singular")

        if singular_name_tag is None:
            raise ValueError(f"Name for {tag} missing the singular tag")
        else:
            assert not singular_name_tag.children
            singular_name: str = singular_name_tag.text or ""

        # plural_name = content.pop('plural', None)
        plural_name_tag = tag.pop_first_matching_tag("plural")
        if plural_name_tag is not None:
            plural_name = plural_name_tag.text
        else:
            plural_name = None

        no_plural = tag.pop_first_matching_tag("noplural")
        if no_plural is not None:
            assert plural_name is None
            assert not no_plural.children and not no_plural.text
        elif plural_name is None:
            # In the UDUNITS2 XML files, things like meters aren't defined.
            # You have to interpret a name as trivially plural iff there is
            # not a noplural tag.
            if singular_name.endswith(("s", "ss", "sh", "ch", "x", "z")):
                plural_name = singular_name + "es"
            else:
                plural_name = singular_name + "s"

        if tag.children or tag.text:
            raise ValueError(f"Unhandled content in unit {tag} (name {singular_name})")
        return Name(
            singular=singular_name,
            plural=plural_name,
        )

    @classmethod
    def handle_prefix(cls, tag: Tag) -> Prefix:
        name_tag = tag.pop_first_matching_tag("name")
        value_tag = tag.pop_first_matching_tag("value")

        if name_tag is None:
            raise ValueError(f"Name missing in prefix {tag}")
        assert not name_tag.children
        name: str = name_tag.text or ""

        if value_tag is None:
            raise ValueError(f"Value missing in prefix {tag}")
        assert not value_tag.children
        # Keep the value as a string. We can parse it later.
        value: str = value_tag.text or ""

        symbols = set()
        for symbol in tag.pop_iter_tags("symbol"):
            symbols.add(symbol.text)

        if tag.children or tag.text:
            raise ValueError(f"Unhandled content in prefix {tag} (name {name})")

        return Prefix(
            name=name,
            value=value,
            symbols=tuple(symbols),
        )

    @classmethod
    def parse_file(cls, path: Path) -> UnitSystem:
        with path.open("rt") as fh:
            tree = etree.parse(fh)
        root = tree.getroot()

        [unit_system] = root.xpath('//*[local-name()="unit-system"]')
        unit_system_t = Tag.from_element(unit_system)

        system = UnitSystem()

        for prefix_tag in unit_system_t.pop_iter_tags("prefix"):
            system.add_prefix(cls.handle_prefix(prefix_tag))

        for unit_tag in unit_system_t.pop_iter_tags("unit"):
            name_tag = unit_tag.pop_first_matching_tag("name")
            if name_tag is None:
                name = None
            else:
                name = cls.handle_name_tag(name_tag)

            symbols = []
            for symbol_tag in unit_tag.pop_iter_tags("symbol"):
                symbols.append(symbol_tag.text)

            alias_names = []
            alias_symbols = []

            aliases = unit_tag.pop_first_matching_tag("aliases")
            if aliases is not None:
                assert not aliases.text
                for alias in aliases.children[:]:
                    aliases.children.remove(alias)
                    if alias.name == "name":
                        alias_names.append(cls.handle_name_tag(alias))
                    elif alias.name == "symbol":
                        assert alias.text and not alias.children
                        alias_symbols.append(alias.text)
                    elif alias.name == "noplural":
                        # Dropped. Seen in avogadro_constant.
                        continue
                    else:
                        raise ValueError(f"Unhandled alias content: {alias}")

            unit_tag.pop_first_matching_tag("comment")

            human_definition = unit_tag.pop_first_matching_tag("definition")
            _ = human_definition

            basis_def = unit_tag.pop_first_matching_tag("def")
            reference = UnitReference(
                name=name,
                symbols=tuple(symbols),
                alias_names=tuple(alias_names),
                alias_symbols=tuple(alias_symbols),
            )
            unit: Unit | LazilyDefinedUnit
            if basis_def is not None:
                assert not basis_def.children
                unit = LazilyDefinedUnit(
                    unit_system=system,
                    definition=basis_def.text or "",
                    names=reference,
                )
            else:
                dimensionless = unit_tag.pop_first_matching_tag("dimensionless")
                if dimensionless is not None:
                    dimensionless = True
                else:
                    dimensionless = False
                    base_tag = unit_tag.pop_first_matching_tag("base")
                    assert base_tag is not None
                    assert not base_tag.text and not base_tag.children

                # Udunits2 knows about time units as a special case. For example
                # https://github.com/Unidata/UDUNITS-2/blob/c83da987387db1174cd2266b73dd5dd556f4476b/lib/udunits-1.c#L50
                # Instead of implementing this special casing in the units handling,
                # we attach a special attribute to a time basis unit.
                is_time_unit = reference.name.singular == "second"

                unit = BasisUnit(
                    names=reference,
                    dimensionless=dimensionless,
                    is_time_unit=is_time_unit,
                )

            if unit_tag.children:
                raise ValueError(
                    f"Unhandled unit content for unit {unit}: \n{unit_tag}"
                )

            system.add_unit(unit)

        if unit_system_t.children:
            raise ValueError(f"Unhandled content {unit_system_t}")

        return system


def read_all() -> UnitSystem:
    system = UDUNITS2XMLParser.parse_file(XML_path)
    return system
