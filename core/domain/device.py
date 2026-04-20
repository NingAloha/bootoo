"""Device domain models.

This module defines stable, platform-agnostic device objects for planner and
executor code. Platform adapters are free to parse any macOS-specific command
output they need, but they should normalize the result into these models before
it reaches the rest of the system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DeviceBusKind(str, Enum):
    """Physical or logical bus classification for a device."""

    UNKNOWN = "unknown"
    USB = "usb"
    THUNDERBOLT = "thunderbolt"
    PCI = "pci"
    VIRTUAL = "virtual"


class FilesystemKind(str, Enum):
    """Filesystem classification used across device and layout models."""

    UNKNOWN = "unknown"
    APFS = "apfs"
    HFS_PLUS = "hfs+"
    EXFAT = "exfat"
    FAT32 = "fat32"
    NTFS = "ntfs"
    EXT4 = "ext4"
    ISO9660 = "iso9660"
    UDF = "udf"
    RAW = "raw"


class PartitionTableKind(str, Enum):
    """Partition table scheme for a whole device."""

    UNKNOWN = "unknown"
    GPT = "gpt"
    MBR = "mbr"
    APM = "apm"
    RAW = "raw"


@dataclass(slots=True, frozen=True)
class DevicePartition:
    """A stable partition view used by validation and planning."""

    identifier: str
    path: str
    name: str = ""
    role: str = "generic"
    filesystem: FilesystemKind = FilesystemKind.UNKNOWN
    size_bytes: int = 0
    mount_point: str | None = None
    is_mounted: bool = False
    is_bootable: bool = False

    @property
    def has_mount_point(self) -> bool:
        """Return whether the partition currently exposes a mount path."""

        return bool(self.mount_point)


@dataclass(slots=True, frozen=True)
class Device:
    """A normalized target device candidate."""

    identifier: str
    path: str
    size_bytes: int
    bus_kind: DeviceBusKind = DeviceBusKind.UNKNOWN
    partition_table: PartitionTableKind = PartitionTableKind.UNKNOWN
    is_internal: bool = False
    is_removable: bool = False
    is_virtual: bool = False
    is_mounted: bool = False
    is_read_only: bool = False
    is_system_risk: bool = False
    content_hint: str | None = None
    partitions: tuple[DevicePartition, ...] = field(default_factory=tuple)

    @property
    def partition_count(self) -> int:
        """Return the number of normalized child partitions."""

        return len(self.partitions)

    @property
    def has_mounted_partitions(self) -> bool:
        """Return whether any partition is currently mounted."""

        return any(partition.is_mounted for partition in self.partitions)

    @property
    def is_external(self) -> bool:
        """Return whether the device should be treated as non-internal."""

        return not self.is_internal


@dataclass(slots=True, frozen=True)
class DeviceSnapshot:
    """A point-in-time view of discovered devices."""

    devices: tuple[Device, ...] = field(default_factory=tuple)

    def get_by_identifier(self, identifier: str) -> Device | None:
        """Return a device by stable identifier if present."""

        for device in self.devices:
            if device.identifier == identifier:
                return device
        return None
