"""Tests for diskutil plist normalization."""

from core.domain.device import DeviceBusKind, FilesystemKind, PartitionTableKind
from core.platform.mac.device_probe import DiskutilDeviceProbe


def test_probe_maps_whole_disk_and_partitions() -> None:
    responses = {
        ("diskutil", "list", "-plist"): {
            "AllDisksAndPartitions": [
                {
                    "DeviceIdentifier": "disk4",
                    "Partitions": [
                        {
                            "DeviceIdentifier": "disk4s1",
                            "DeviceNode": "/dev/disk4s1",
                            "VolumeName": "EFI",
                            "Content": "EFI",
                            "Size": 524288000,
                        },
                        {
                            "DeviceIdentifier": "disk4s2",
                            "DeviceNode": "/dev/disk4s2",
                            "VolumeName": "BOOTOO",
                            "FilesystemType": "ExFAT",
                            "Content": "Microsoft Basic Data",
                            "MountPoint": "/Volumes/BOOTOO",
                            "Size": 15931539456,
                        },
                    ],
                }
            ]
        },
        ("diskutil", "info", "-plist", "disk4"): {
            "DeviceIdentifier": "disk4",
            "DeviceNode": "/dev/disk4",
            "TotalSize": 16456925184,
            "BusProtocol": "USB",
            "PartitionMapScheme": "GUID_partition_scheme",
            "Internal": False,
            "RemovableMedia": True,
            "VirtualOrPhysical": "Physical",
            "ReadOnly": False,
            "Content": "GUID_partition_scheme",
        },
    }

    def fake_runner(args: list[str]) -> dict:
        return responses[tuple(args)]

    snapshot = DiskutilDeviceProbe(plist_runner=fake_runner).probe()
    device = snapshot.get_by_identifier("disk4")

    assert device is not None
    assert device.path == "/dev/disk4"
    assert device.size_bytes == 16456925184
    assert device.bus_kind is DeviceBusKind.USB
    assert device.partition_table is PartitionTableKind.GPT
    assert device.is_external
    assert not device.is_virtual
    assert device.content_hint == "GUID_partition_scheme"
    assert device.partition_count == 2
    assert device.has_mounted_partitions

    efi_partition, data_partition = device.partitions
    assert efi_partition.is_bootable
    assert data_partition.filesystem is FilesystemKind.EXFAT
    assert data_partition.mount_point == "/Volumes/BOOTOO"
    assert data_partition.is_mounted


def test_probe_marks_internal_root_device_as_system_risk() -> None:
    responses = {
        ("diskutil", "list", "-plist"): {
            "AllDisksAndPartitions": [
                {
                    "DeviceIdentifier": "disk0",
                    "Partitions": [
                        {
                            "DeviceIdentifier": "disk0s2",
                            "DeviceNode": "/dev/disk0s2",
                            "VolumeName": "Macintosh HD",
                            "FilesystemType": "APFS",
                            "MountPoint": "/",
                            "Size": 499963174912,
                        }
                    ],
                }
            ]
        },
        ("diskutil", "info", "-plist", "disk0"): {
            "DeviceIdentifier": "disk0",
            "DeviceNode": "/dev/disk0",
            "TotalSize": 500277790720,
            "BusProtocol": "PCI-Express",
            "PartitionMapScheme": "GUID_partition_scheme",
            "Internal": True,
            "RemovableMedia": False,
            "VirtualOrPhysical": "Physical",
            "WritableMedia": True,
        },
    }

    def fake_runner(args: list[str]) -> dict:
        return responses[tuple(args)]

    snapshot = DiskutilDeviceProbe(plist_runner=fake_runner).probe()
    device = snapshot.get_by_identifier("disk0")

    assert device is not None
    assert device.bus_kind is DeviceBusKind.PCI
    assert device.is_internal
    assert device.is_system_risk


def test_probe_maps_apfs_container_volumes_from_list_payload() -> None:
    responses = {
        ("diskutil", "list", "-plist"): {
            "AllDisksAndPartitions": [
                {
                    "DeviceIdentifier": "disk3",
                    "Content": "Apple_APFS_Container",
                    "OSInternal": False,
                    "Size": 245107195904,
                    "Partitions": [],
                    "APFSVolumes": [
                        {
                            "DeviceIdentifier": "disk3s1s1",
                            "MountPoint": "/",
                            "Size": 245107195904,
                            "VolumeName": "Macintosh HD",
                        },
                        {
                            "DeviceIdentifier": "disk3s5",
                            "MountPoint": "/System/Volumes/Data",
                            "Size": 245107195904,
                            "VolumeName": "Data",
                        },
                    ],
                }
            ]
        },
        ("diskutil", "info", "-plist", "disk3"): {
            "DeviceIdentifier": "disk3",
            "DeviceNode": "/dev/disk3",
            "TotalSize": 245107195904,
            "BusProtocol": "Apple Fabric",
            "Content": "Apple_APFS_Container",
            "Internal": False,
            "RemovableMedia": False,
            "VirtualOrPhysical": "Unknown",
            "WritableMedia": True,
        },
    }

    def fake_runner(args: list[str]) -> dict:
        return responses[tuple(args)]

    snapshot = DiskutilDeviceProbe(plist_runner=fake_runner).probe()
    device = snapshot.get_by_identifier("disk3")

    assert device is not None
    assert device.partition_count == 2
    assert device.has_mounted_partitions
    assert device.is_mounted
    assert device.is_system_risk

    system_volume, data_volume = device.partitions
    assert system_volume.filesystem is FilesystemKind.APFS
    assert system_volume.role == "system"
    assert system_volume.is_bootable
    assert data_volume.role == "data"
