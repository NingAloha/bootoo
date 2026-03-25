from __future__ import annotations
"""延迟解析类型注解，方便前向引用，减少类型定义顺序带来的问题"""
from typing import Any, Dict, List, Tuple
"""类型提示工具: Any=任意类型, Dict/List/Tuple=常用容器注解，提升可读性与静态检查效果"""
import subprocess
import plistlib

devices: List[Dict[str, Any]] = []

def _scan_devices() -> List[Dict[str, Any]]:
    global devices
    try:
        result = subprocess.run(
            ["diskutil", "list", "-plist"],
            capture_output=True,
            check=True
        )
        plist_data = plistlib.loads(result.stdout)
    except Exception as e:
        devices = []
        return devices
    
    devices = []
    for disk in plist_data.get("AllDisksAndPartitions", []):
        device_id = disk.get("DeviceIdentifier")
        device_path = f"/dev/{device_id}"
        size_bytes = disk.get("Size", 0)
        internal = disk.get("Internal", disk.get("OSInternal", False))
        removable = disk.get("Removable", False)
        content = disk.get("Content", "")
        mounted = False
        volumes =[]
        for part_key in ("Partitions", "APFSVolumes"):
            for part in disk.get(part_key, []):
                if part.get("MountPoint"):
                    mounted = True
                if part.get("VolumeName"):
                    volumes.append(part["VolumeName"])
        is_system_risk = (device_id == "disk0") or bool(internal) or (content == "Apple_APFS_Container")
        devices.append({
            "id": device_id,
            "device": device_path,
            "size_bytes": size_bytes,
            "internal": internal,
            "removable": removable,
            "mounted": mounted,
            "volumes": volumes,
            "is_system_risk": is_system_risk
        })

    return devices

def _validate_target(device: Dict[str, Any]) -> bool:
    forbidden_content = {
        "Apple_APFS_Container", "Apple_APFS", "Apple_HFS", "Apple_CoreStorage_Container"
    }
    if not device:
        return False
    content = device.get("content", "")
    if device.get("internal"):
        return False
    if device.get("is_system_risk"):
        return False
    if content in forbidden_content:
        return False
    if int(device.get("size_bytes", 0)) < 1 * 1024 * 1024 * 1024:
        return False
    return True

def list_all_devices() -> List[Dict[str, Any]]:
    """返回所有扫描到的磁盘设备（含详细字段）"""
    return _scan_devices()

def list_available_devices() -> List[Dict[str, Any]]:
    """返回通过安全校验的可用磁盘设备"""
    all_devices = _scan_devices()
    return [d for d in all_devices if _validate_target(d)]

if __name__ == "__main__":
    def format_gb(size_bytes: int) -> str:
        gb = size_bytes / (1024 ** 3)
        return f"{gb:.2f} GB"

    print("所有磁盘：")
    for d in list_all_devices():
        print(f"id: {d['id']}, device: {d['device']}, size: {format_gb(d['size_bytes'])}, volumes: {d['volumes']}")
    print("\n可用磁盘：")
    for d in list_available_devices():
        print(f"id: {d['id']}, device: {d['device']}, size: {format_gb(d['size_bytes'])}, volumes: {d['volumes']}")