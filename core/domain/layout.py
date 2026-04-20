"""Partition layout domain model skeleton."""

from dataclasses import dataclass, field


@dataclass(slots=True)
class PartitionSpec:
    name: str
    size_bytes: int | None = None
    filesystem: str = "unknown"


@dataclass(slots=True)
class PartitionLayout:
    table_kind: str
    partitions: list[PartitionSpec] = field(default_factory=list)
