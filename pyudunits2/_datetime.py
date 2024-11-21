from __future__ import annotations
import dataclasses
import typing


@dataclasses.dataclass(frozen=True)
class Time:
    hour: int
    minute: int
    second: int = 0
    microseconds: int = 0

    def __str__(self):
        t_str = f"{self.hour:02}:{self.minute:02}"
        if self.second or self.microseconds:
            t_str += f":{self.second:02}"
        if self.microseconds:
            t_str += f".{self.microseconds:08}"
        return t_str


@dataclasses.dataclass(frozen=True)
class DateTime:
    year: int
    month: int
    day: int
    time: Time = Time(0, 0)
    tz_offset: Time | str = "UTC"
    #: The original representation of the date time before any parsing.
    raw_content: str | None = None

    def __eq__(self, other: typing.Any) -> bool:
        if not isinstance(other, DateTime):
            return NotImplemented

        # Compare everything except raw_form.
        return (
            self.year == other.year
            and self.month == other.month
            and self.day == other.day
            and self.time == other.time
            and self.tz_offset == other.tz_offset
        )


def parse_udunits_date(content: str) -> DateTime:
    raise NotImplementedError(
        f"Date time parsing not yet implemented (requested parse of {content!r})"
    )
