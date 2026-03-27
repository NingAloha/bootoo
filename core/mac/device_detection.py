from __future__ import annotations
from typing import Any, Dict, List, Tuple
import subprocess
import plistlib

devices: List[Dict[str, Any]] = []

def _scan_devices() -> List[Dict[str, Any]]:
    """
    扫描本机所有磁盘设备，返回设备信息列表。
    输入参数：无
    返回值：List[Dict[str, Any]]，每个字典包含如下字段：
        - id: 设备标识符（str）
        - device: 设备路径（str，如"/dev/disk2"）
        - size_bytes: 设备容量（int，字节数）
        - internal: 是否为内置设备（bool）
        - removable: 是否为可移动设备（bool）
        - mounted: 是否已挂载（bool）
        - volumes: 设备上的卷名列表（List[str]）
        - is_system_risk: 是否为系统盘或高风险设备（bool）
    """
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
    """
    校验设备是否为可用目标盘。
    输入参数：
        - device: 单个设备信息字典（同 _scan_devices 返回结构）
    返回值：
        - bool，True 表示可用，False 表示不可用
    """
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
    """
    获取所有磁盘设备信息列表。
    输入参数：无
    返回值：List[Dict[str, Any]]，结构同 _scan_devices
    """
    return _scan_devices()

def list_available_devices() -> List[Dict[str, Any]]:
    """
    获取所有可用（可写入/非系统盘）磁盘设备信息列表。
    输入参数：无
    返回值：List[Dict[str, Any]]，结构同 _scan_devices
    """
    all_devices = _scan_devices()
    return [d for d in all_devices if _validate_target(d)]

if __name__ == "__main__":
    def format_gb(size_bytes: int) -> str:
        """
        字节转 GB 字符串。
        输入参数：size_bytes（int）
        返回值：格式化后的字符串（str）
        """
        gb = size_bytes / (1024 ** 3)
        return f"{gb:.2f} GB"

    print("所有磁盘：")
    for d in list_all_devices():
        print(f"id: {d['id']}, device: {d['device']}, size: {format_gb(d['size_bytes'])}, volumes: {d['volumes']}")
    print("\n可用磁盘：")
    for d in list_available_devices():
        print(f"id: {d['id']}, device: {d['device']}, size: {format_gb(d['size_bytes'])}, volumes: {d['volumes']}")