from __future__ import annotations
from typing import Any, Dict, List
import subprocess
import plistlib
import logging

# 原有模块级全局变量（已移除，无实际用途，_scan_devices 直接返回列表即可）：
# devices: List[Dict[str, Any]] = []

logger = logging.getLogger(__name__)

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
        - content: 设备内容类型（str，如"Apple_APFS_Container"）
    """
    try:
        result = subprocess.run(
            ["diskutil", "list", "-plist"],
            capture_output=True,
            check=True,
            timeout=10,
        )
        plist_data = plistlib.loads(result.stdout)
    except subprocess.TimeoutExpired:
        logger.error("diskutil list 超时")
        return []
    except subprocess.CalledProcessError as e:
        logger.error("diskutil list 执行失败: %s", e.stderr)
        return []
    except Exception as e:
        logger.error("扫描设备时发生未知错误: %s", e)
        return []

    result_list = []
    for disk in plist_data.get("AllDisksAndPartitions", []):
        device_id = disk.get("DeviceIdentifier")
        # 跳过无效设备标识符，防止构造出 "/dev/None" 等非法路径
        if not device_id or not isinstance(device_id, str):
            continue
        device_path = f"/dev/{device_id}"
        size_bytes = int(disk.get("Size", 0) or 0)
        internal = bool(disk.get("Internal", disk.get("OSInternal", False)))
        removable = bool(disk.get("Removable", False))
        content = disk.get("Content", "") or ""
        mounted = False
        volumes = []
        for part_key in ("Partitions", "APFSVolumes"):
            for part in disk.get(part_key, []):
                if part.get("MountPoint"):
                    mounted = True
                if part.get("VolumeName"):
                    volumes.append(part["VolumeName"])
        is_system_risk = (device_id == "disk0") or internal or (content == "Apple_APFS_Container")
        result_list.append({
            "id": device_id,
            "device": device_path,
            "size_bytes": size_bytes,
            "internal": internal,
            "removable": removable,
            "mounted": mounted,
            "volumes": volumes,
            "is_system_risk": is_system_risk,
            "content": content,  # BUG FIX [2026-04-01]: 原先未将 content 存入设备字典，导致 _validate_target 中 forbidden_content 过滤永远无效
        })

    return result_list

_1GB = 1 * 1024 * 1024 * 1024

def _validate_target(device: Dict[str, Any], min_size_bytes: int = _1GB) -> bool:
    """
    校验设备是否为可用目标盘。
    输入参数：
        - device: 单个设备信息字典（同 _scan_devices 返回结构）
        - min_size_bytes: 最小容量要求（int，字节数），默认 1GB
    返回值：
        - bool，True 表示可用，False 表示不可用
    """
    _FORBIDDEN_CONTENT = {
        "Apple_APFS_Container", "Apple_APFS", "Apple_HFS", "Apple_CoreStorage_Container"
    }
    if not device:
        return False
    # BUG FIX [2026-04-01]: _scan_devices 原先未将 content 写入设备字典，
    # 导致此处 device.get("content") 始终返回 ""，forbidden_content 过滤完全失效。
    # 已在 _scan_devices 中补充 "content" 字段，此处逻辑无需修改。
    # 原有问题代码（已保留作参考）：
    # content = device.get("content", "")  ← 键名正确，但字典中无此键，故永远为 ""
    content = device.get("content", "")
    if device.get("internal"):
        return False
    if device.get("is_system_risk"):
        return False
    if content in _FORBIDDEN_CONTENT:
        return False
    if device.get("size_bytes", 0) < min_size_bytes:
        return False
    return True

def list_all_devices() -> List[Dict[str, Any]]:
    """
    获取所有磁盘设备信息列表。
    输入参数：无
    返回值：List[Dict[str, Any]]，结构同 _scan_devices
    """
    return _scan_devices()

def list_available_devices(min_size_bytes: int = _1GB) -> List[Dict[str, Any]]:
    """
    获取所有可用（可写入/非系统盘）磁盘设备信息列表。
    输入参数：
        - min_size_bytes: 最小容量要求（int，字节数），默认 1GB
    返回值：List[Dict[str, Any]]，结构同 _scan_devices
    """
    all_devices = _scan_devices()
    return [d for d in all_devices if _validate_target(d, min_size_bytes)]