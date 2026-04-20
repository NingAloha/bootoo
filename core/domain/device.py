"""Device domain model skeleton."""

from dataclasses import dataclass, field


@dataclass(slots=True)
class DevicePartition:
    identifier: str
    role: str = "generic"


@dataclass(slots=True)
class Device:
    identifier: str
    path: str
    size_bytes: int
    partitions: list[DevicePartition] = field(default_factory=list)
