"""
写后校验：容量检查、引导分区存在性、必要文件存在性。
在写入完成后调用，确认目标设备状态符合预期。
"""

import subprocess
import plistlib
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# 各系统类型的必要文件路径（相对于挂载点）
_REQUIRED_FILES: Dict[str, List[str]] = {
    "windows": ["bootmgr", "boot/bcd"],
    "linux":   ["boot/grub/grub.cfg", "isolinux/isolinux.cfg"],
    "macos":   [".IABootFiles", "System/Library/CoreServices/boot.efi"],
}


def _get_disk_info_plist(device_path: str) -> Optional[dict]:
    """调用 diskutil info -plist 返回解析后的 plist dict，失败返回 None。"""
    try:
        result = subprocess.run(
            ["diskutil", "info", "-plist", device_path],
            capture_output=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None
        return plistlib.loads(result.stdout)
    except Exception:
        return None


def _get_partition_list(device_path: str) -> List[dict]:
    """
    返回设备的分区列表（plist 格式），失败返回空列表。
    使用 diskutil list -plist 获取完整分区表。
    """
    try:
        result = subprocess.run(
            ["diskutil", "list", "-plist", device_path],
            capture_output=True,
            timeout=10,
        )
        if result.returncode != 0:
            return []
        info = plistlib.loads(result.stdout)
        # AllDisksAndPartitions 结构
        for disk in info.get("AllDisksAndPartitions", []):
            if disk.get("DeviceIdentifier") in (
                device_path.replace("/dev/", ""),
                device_path,
            ):
                return disk.get("Partitions", []) + disk.get("APFSVolumes", [])
        return []
    except Exception:
        return []


def verify_capacity(device_path: str, image_size_bytes: int) -> Dict[str, Any]:
    """
    校验目标设备容量是否不小于镜像大小。
    输入参数：
        - device_path: 目标设备路径（str），如 "/dev/disk2"
        - image_size_bytes: 镜像文件大小（int，字节）
    返回值：
        - Dict[str, Any]: {ok, code, message, data}
    """
    if not device_path or not device_path.startswith("/dev/"):
        return {"ok": False, "code": "VERIFY_CAPACITY_FAIL", "message": "无效的设备路径", "data": None}

    info = _get_disk_info_plist(device_path)
    if info is None:
        return {"ok": False, "code": "VERIFY_CAPACITY_FAIL", "message": "无法获取设备信息", "data": None}

    device_size = info.get("TotalSize") or info.get("Size") or 0
    ok = int(device_size) >= image_size_bytes
    return {
        "ok": ok,
        "code": "SUCCESS" if ok else "VERIFY_CAPACITY_FAIL",
        "message": "容量校验通过" if ok else f"设备容量不足：设备 {device_size} 字节，镜像 {image_size_bytes} 字节",
        "data": {"device_size": device_size, "image_size": image_size_bytes},
    }


def verify_partition_exists(device_path: str) -> Dict[str, Any]:
    """
    校验目标设备写入后是否存在至少一个可识别分区。
    输入参数：
        - device_path: 目标设备路径（str），如 "/dev/disk2"
    返回值：
        - Dict[str, Any]: {ok, code, message, data}
    """
    if not device_path or not device_path.startswith("/dev/"):
        return {"ok": False, "code": "VERIFY_PARTITION_FAIL", "message": "无效的设备路径", "data": None}

    partitions = _get_partition_list(device_path)
    ok = len(partitions) > 0
    return {
        "ok": ok,
        "code": "SUCCESS" if ok else "VERIFY_PARTITION_FAIL",
        "message": f"检测到 {len(partitions)} 个分区" if ok else "未检测到任何分区，写入可能失败",
        "data": {"partition_count": len(partitions), "partitions": [
            p.get("DeviceIdentifier") for p in partitions if p.get("DeviceIdentifier")
        ]},
    }


def verify_required_files(mount_point: str, os_type: str = "windows") -> Dict[str, Any]:
    """
    校验挂载点下是否存在指定系统类型的必要引导文件。
    输入参数：
        - mount_point: 设备挂载点路径（str），如 "/Volumes/EFI"
        - os_type: 系统类型（str），支持 "windows"、"linux"、"macos"，默认 "windows"
    返回值：
        - Dict[str, Any]: {ok, code, message, data}
    """
    import os

    if not mount_point:
        return {"ok": False, "code": "VERIFY_FILES_FAIL", "message": "挂载点路径为空", "data": None}

    key = os_type.lower()
    required = _REQUIRED_FILES.get(key)
    if required is None:
        # 未知系统类型，跳过文件校验
        return {
            "ok": True,
            "code": "SUCCESS",
            "message": f"未知系统类型 '{os_type}'，跳过文件校验",
            "data": {"os_type": os_type, "checked": False},
        }

    missing = []
    for rel_path in required:
        full_path = os.path.join(mount_point, rel_path)
        if not os.path.exists(full_path):
            missing.append(rel_path)

    ok = len(missing) == 0
    return {
        "ok": ok,
        "code": "SUCCESS" if ok else "VERIFY_FILES_FAIL",
        "message": "必要文件校验通过" if ok else f"缺少必要文件: {missing}",
        "data": {"os_type": os_type, "missing_files": missing, "checked_files": required},
    }


def verify_write_result(
    device_path: str,
    image_size_bytes: int,
    mount_point: Optional[str] = None,
    os_type: str = "windows",
) -> Dict[str, Any]:
    """
    写后综合校验：依次执行容量校验、分区存在性校验、必要文件校验（可选）。
    输入参数：
        - device_path: 目标设备路径（str），如 "/dev/disk2"
        - image_size_bytes: 镜像文件大小（int，字节）
        - mount_point: 挂载点路径（str，可选），提供时执行文件校验
        - os_type: 系统类型（str），默认 "windows"
    返回值：
        - Dict[str, Any]:
            - ok: 所有校验是否通过（bool）
            - code: 状态码（str）
            - message: 说明信息（str）
            - data: 各步骤结果 dict
    """
    results: Dict[str, Any] = {}

    # 1. 容量校验
    cap = verify_capacity(device_path, image_size_bytes)
    results["capacity"] = cap
    if not cap["ok"]:
        return {
            "ok": False,
            "code": "VERIFY_CAPACITY_FAIL",
            "message": cap["message"],
            "data": results,
        }

    # 2. 分区存在性校验
    part = verify_partition_exists(device_path)
    results["partition"] = part
    if not part["ok"]:
        return {
            "ok": False,
            "code": "VERIFY_PARTITION_FAIL",
            "message": part["message"],
            "data": results,
        }

    # 3. 必要文件校验（仅在提供挂载点时执行）
    if mount_point:
        files = verify_required_files(mount_point, os_type)
        results["files"] = files
        if not files["ok"]:
            return {
                "ok": False,
                "code": "VERIFY_FILES_FAIL",
                "message": files["message"],
                "data": results,
            }

    return {
        "ok": True,
        "code": "SUCCESS",
        "message": "写后校验全部通过",
        "data": results,
    }
