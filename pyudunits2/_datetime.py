from __future__ import annotations
import dataclasses


@dataclasses.dataclass(frozen=True)
class Time:
    hour: int
    minute: int
    second: int
    microseconds: int

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
    time: Time
    tz_offset: Time | str = "UTC"

    # @classmethod
    # def parse(cls, content: str | int) -> DateTime:
    #     if isinstance(content, int):
    #         content = str(content)
    #     year = content[:4]
