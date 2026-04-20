"""Read-only device probing based on diskutil plist output."""

from __future__ import annotations

from dataclasses import dataclass
import plistlib
from typing import Callable

from core.domain.device import (
    Device,
    DeviceBusKind,
    DevicePartition,
    DeviceSnapshot,
    FilesystemKind,
    PartitionTableKind,
)

from .command_runner import CommandRunnerError, run_command


class DeviceProbeError(RuntimeError):
    """Raised when diskutil probing or plist decoding fails."""


PlistRunner = Callable[[list[str]], dict]


@dataclass(slots=True)
class DiskutilDeviceProbe:
    """Normalize diskutil plist output into domain device models."""

    plist_runner: PlistRunner | None = None

    def probe(self) -> DeviceSnapshot:
        """Probe available whole disks and their partitions."""

        list_payload = self._run_plist(["diskutil", "list", "-plist"])
        devices: list[Device] = []

        for disk_entry in list_payload.get("AllDisksAndPartitions", []):
            disk_identifier = str(disk_entry.get("DeviceIdentifier", "")).strip()
            if not disk_identifier:
                continue

            disk_info = self._run_plist(["diskutil", "info", "-plist", disk_identifier])
            partitions = self._build_children(disk_entry)
            devices.append(self._build_device(disk_entry, disk_info, partitions))

        return DeviceSnapshot(devices=tuple(devices))

    def _build_children(self, disk_entry: dict) -> tuple[DevicePartition, ...]:
        children: list[DevicePartition] = []

        for partition_entry in disk_entry.get("Partitions", []):
            children.append(self._build_partition(partition_entry))

        for apfs_volume_entry in disk_entry.get("APFSVolumes", []):
            children.append(self._build_apfs_volume(apfs_volume_entry))

        return tuple(children)

    def _run_plist(self, args: list[str]) -> dict:
        if self.plist_runner is not None:
            return self.plist_runner(args)

        try:
            result = run_command(args).require_success()
            payload = plistlib.loads(result.stdout)
        except (CommandRunnerError, plistlib.InvalidFileException, ValueError) as exc:
            raise DeviceProbeError(str(exc)) from exc

        if not isinstance(payload, dict):
            raise DeviceProbeError("diskutil plist payload is not a dictionary")
        return payload

    def _build_device(
        self,
        disk_entry: dict,
        disk_info: dict,
        partitions: tuple[DevicePartition, ...],
    ) -> Device:
        identifier = _string_value(disk_info, "DeviceIdentifier") or _string_value(
            disk_entry,
            "DeviceIdentifier",
        )
        path = _string_value(disk_info, "DeviceNode") or f"/dev/{identifier}"
        content_hint = _string_value(disk_info, "Content") or None
        is_internal = _bool_value(disk_info, "Internal")
        is_virtual = _is_virtual_device(disk_info)

        return Device(
            identifier=identifier,
            path=path,
            size_bytes=_int_value(disk_info, "TotalSize", "Size"),
            bus_kind=_normalize_bus_kind(_string_value(disk_info, "BusProtocol")),
            partition_table=_normalize_partition_table(
                _string_value(disk_info, "PartitionMapScheme") or content_hint,
            ),
            is_internal=is_internal,
            is_removable=_bool_value(
                disk_info,
                "Removable",
                "RemovableMedia",
                "Ejectable",
                default=not is_internal,
            ),
            is_virtual=is_virtual,
            is_mounted=any(partition.is_mounted for partition in partitions),
            is_read_only=_is_read_only_device(disk_info),
            is_system_risk=_is_system_risk_device(is_internal, partitions),
            content_hint=content_hint,
            partitions=partitions,
        )

    def _build_partition(self, partition_entry: dict) -> DevicePartition:
        identifier = _string_value(partition_entry, "DeviceIdentifier")
        path = _string_value(partition_entry, "DeviceNode") or f"/dev/{identifier}"
        mount_point = _string_value(partition_entry, "MountPoint") or None

        return DevicePartition(
            identifier=identifier,
            path=path,
            name=_string_value(partition_entry, "VolumeName", "Name"),
            role=_string_value(partition_entry, "Content", "VolumeRole", default="generic"),
            filesystem=_normalize_filesystem(
                _string_value(partition_entry, "FilesystemType", "APFSVolumeType", "Content"),
            ),
            size_bytes=_int_value(partition_entry, "Size"),
            mount_point=mount_point,
            is_mounted=bool(mount_point),
            is_bootable=_is_bootable_partition(partition_entry),
        )

    def _build_apfs_volume(self, volume_entry: dict) -> DevicePartition:
        identifier = _string_value(volume_entry, "DeviceIdentifier")
        path = _string_value(volume_entry, "DeviceNode") or f"/dev/{identifier}"
        mount_point = _string_value(volume_entry, "MountPoint") or None

        return DevicePartition(
            identifier=identifier,
            path=path,
            name=_string_value(volume_entry, "VolumeName", "Name"),
            role=_infer_apfs_volume_role(volume_entry),
            filesystem=FilesystemKind.APFS,
            size_bytes=_int_value(volume_entry, "Size"),
            mount_point=mount_point,
            is_mounted=bool(mount_point),
            is_bootable=_is_bootable_partition(volume_entry),
        )


def _string_value(payload: dict, *keys: str, default: str = "") -> str:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return default


def _bool_value(payload: dict, *keys: str, default: bool = False) -> bool:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, bool):
            return value
    return default


def _int_value(payload: dict, *keys: str, default: int = 0) -> int:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, int):
            return value
    return default


def _normalize_bus_kind(raw_value: str) -> DeviceBusKind:
    value = raw_value.lower()
    if "usb" in value:
        return DeviceBusKind.USB
    if "thunderbolt" in value:
        return DeviceBusKind.THUNDERBOLT
    if "pci" in value:
        return DeviceBusKind.PCI
    if "virtual" in value or "image" in value:
        return DeviceBusKind.VIRTUAL
    return DeviceBusKind.UNKNOWN


def _normalize_partition_table(raw_value: str) -> PartitionTableKind:
    value = raw_value.lower()
    if "guid" in value or "gpt" in value:
        return PartitionTableKind.GPT
    if "fdisk" in value or "mbr" in value:
        return PartitionTableKind.MBR
    if "apple_partition_scheme" in value or "apm" in value:
        return PartitionTableKind.APM
    if "raw" in value:
        return PartitionTableKind.RAW
    return PartitionTableKind.UNKNOWN


def _normalize_filesystem(raw_value: str) -> FilesystemKind:
    value = raw_value.lower()
    if "apfs" in value:
        return FilesystemKind.APFS
    if "hfs" in value:
        return FilesystemKind.HFS_PLUS
    if "exfat" in value:
        return FilesystemKind.EXFAT
    if "ms-dos" in value or "fat32" in value or "fat" in value:
        return FilesystemKind.FAT32
    if "ntfs" in value:
        return FilesystemKind.NTFS
    if "ext4" in value:
        return FilesystemKind.EXT4
    if "iso9660" in value:
        return FilesystemKind.ISO9660
    if "udf" in value:
        return FilesystemKind.UDF
    if "raw" in value:
        return FilesystemKind.RAW
    return FilesystemKind.UNKNOWN


def _is_virtual_device(disk_info: dict) -> bool:
    physical_kind = _string_value(disk_info, "VirtualOrPhysical")
    if physical_kind.lower() == "virtual":
        return True
    return _normalize_bus_kind(_string_value(disk_info, "BusProtocol")) is DeviceBusKind.VIRTUAL


def _is_read_only_device(disk_info: dict) -> bool:
    if _bool_value(disk_info, "ReadOnly", "ReadOnlyMedia"):
        return True
    writable = disk_info.get("WritableMedia")
    if isinstance(writable, bool):
        return not writable
    return False


def _is_bootable_partition(partition_entry: dict) -> bool:
    if _bool_value(partition_entry, "Bootable"):
        return True
    role = _string_value(partition_entry, "Content", "VolumeRole").lower()
    filesystem = _string_value(partition_entry, "FilesystemType", "APFSVolumeType").lower()
    mount_point = _string_value(partition_entry, "MountPoint").lower()
    return "efi" in role or "boot" in role or "efi" in filesystem or mount_point == "/"


def _infer_apfs_volume_role(volume_entry: dict) -> str:
    mount_point = _string_value(volume_entry, "MountPoint")
    volume_name = _string_value(volume_entry, "VolumeName")

    if mount_point == "/":
        return "system"
    if mount_point.startswith("/System/Volumes/"):
        return mount_point.removeprefix("/System/Volumes/").lower() or "system"
    if volume_name:
        return volume_name.lower()
    return "apfs-volume"


def _is_system_risk_device(is_internal: bool, partitions: tuple[DevicePartition, ...]) -> bool:
    if is_internal:
        return True
    for partition in partitions:
        if partition.mount_point == "/":
            return True
        if partition.mount_point and partition.mount_point.startswith("/System/Volumes/"):
            return True
    return False
