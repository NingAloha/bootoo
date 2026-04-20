"""Boot planning domain model skeleton."""

from dataclasses import dataclass


@dataclass(slots=True)
class BootPlan:
    mode: str
    source: str
