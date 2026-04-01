import subprocess
import plistlib
import logging
from core.mac.device_detection import list_available_devices
from typing import Dict, Any

# 对外接口：unmount_device、format_disk、get_disk_info
# 参数全部统一为 partition_path 或 device_path，直接传递即可，无需额外拼接或处理

logger = logging.getLogger(__name__)

_VALID_FS_TYPES = {"exFAT", "MS-DOS FAT32", "APFS", "JHFS+"}

def unmount_device(device_path: str) -> Dict[str, Any]:
    """
    卸载指定的磁盘或分区。
    输入参数：
        - device_path: 设备或分区路径（str），如"/dev/disk2" 或 "/dev/disk2s1"
    返回值：
        - Dict[str, Any]:
            - ok: 是否卸载成功（bool）
            - code: 状态码（str），如 'SUCCESS'、'UNMOUNT_FAILED'
            - message: 说明信息（str）
            - data: 详细信息（dict，包含 device_path，失败时为 None）
    """
    # 输入校验：设备路径必须以 /dev/ 开头
    if not device_path or not device_path.startswith("/dev/"):
        return {"ok": False, "code": "UNMOUNT_FAILED", "message": "无效的设备路径", "data": None}
    try:
        result = subprocess.run(
            ["diskutil", "unmountDisk", device_path],
            capture_output=True,
            timeout=30,
            # 原有代码使用 check=True，但同时检查 returncode，两者冲突：
            # check=True 在非零返回码时直接抛出异常，returncode 的失败分支永远不会执行。
            # 已改为不使用 check=True，改为手动判断 returncode。
            # check=True  ← 已移除
        )
        ok = result.returncode == 0
        return {
            "ok": ok,
            "code": "SUCCESS" if ok else "UNMOUNT_FAILED",
            # 原有代码使用 result.stderr.decode()，未指定编码和错误处理，可能抛出 UnicodeDecodeError
            # result.stderr.decode()  ← 已替换
            "message": "卸载成功" if ok else result.stderr.decode("utf-8", errors="replace"),
            "data": {"device_path": device_path} if ok else None,
        }
    except subprocess.TimeoutExpired:
        logger.error("unmount_device 超时: %s", device_path)
        return {"ok": False, "code": "UNMOUNT_FAILED", "message": "卸载超时", "data": None}
    except Exception as e:
        logger.error("unmount_device 异常: %s", e)
        return {"ok": False, "code": "UNMOUNT_FAILED", "message": "卸载设备失败", "data": None}


def format_disk(partition_path: str, fs_type: str = "exFAT", name: str = "Untitled") -> Dict[str, Any]:
    """
    格式化指定分区。
    输入参数：
        - partition_path: 分区路径（str），如"/dev/disk2s1"
        - fs_type: 文件系统类型（str），如"exFAT"、"APFS"，默认"exFAT"
        - name: 卷标名（str），默认"Untitled"
    返回值：
        - Dict[str, Any]:
            - ok: 是否格式化成功（bool）
            - code: 状态码（str），如 'SUCCESS'、'FORMAT_FAILED'
            - message: 说明信息（str）
            - data: 详细信息（dict，包含 partition_path, fs_type, name, unmount_ok，失败时为 None）
    """
    # 输入校验
    if not partition_path or not partition_path.startswith("/dev/"):
        return {"ok": False, "code": "FORMAT_FAILED", "message": "无效的分区路径", "data": None}
    if fs_type not in _VALID_FS_TYPES:
        return {"ok": False, "code": "FORMAT_FAILED", "message": f"不支持的文件系统类型: {fs_type}", "data": None}
    # 卷标长度限制
    if fs_type in ["exFAT", "MS-DOS FAT32"]:
        max_len = 11
    else:
        max_len = 27
    if len(name) > max_len:
        logger.warning("卷标过长，已自动截断为前 %d 字符", max_len)
        # 原有代码使用 print() 输出警告，已改为 logger.warning
        # print(f"警告：卷标过长，已自动截断为前{max_len}字符。")  ← 已移除
        name = name[:max_len]
    # 卷标字符过滤：仅保留 ASCII 可打印字符，避免特殊字符导致 diskutil 行为异常
    name = "".join(c for c in name if 32 <= ord(c) < 127)
    if not name:
        name = "Untitled"
    # 格式化前先尝试卸载分区
    unmount_res = unmount_device(partition_path)
    unmount_ok = unmount_res["ok"]
    if not unmount_ok:
        logger.warning("分区卸载失败，继续尝试格式化。原因：%s", unmount_res["message"])
        # 原有代码使用 print() 输出警告，已改为 logger.warning
        # print(f"警告：分区卸载失败，可能影响格式化成功率。信息：{unmount_res['message']}")  ← 已移除
    try:
        result = subprocess.run(
            ["diskutil", "eraseVolume", fs_type, name, partition_path],
            capture_output=True,
            timeout=120,
            # 原有代码使用 check=True，与 returncode 判断冲突，已移除（同 unmount_device）
            # check=True  ← 已移除
        )
        ok = result.returncode == 0
        return {
            "ok": ok,
            "code": "SUCCESS" if ok else "FORMAT_FAILED",
            "message": "格式化成功" if ok else result.stderr.decode("utf-8", errors="replace"),
            "data": {"partition_path": partition_path, "fs_type": fs_type, "name": name, "unmount_ok": unmount_ok} if ok else None,
        }
    except subprocess.TimeoutExpired:
        logger.error("format_disk 超时: %s", partition_path)
        return {"ok": False, "code": "FORMAT_FAILED", "message": "格式化超时", "data": None}
    except Exception as e:
        logger.error("format_disk 异常: %s", e)
        return {"ok": False, "code": "FORMAT_FAILED", "message": "格式化分区失败", "data": None}


def get_disk_info(path: str) -> Dict[str, Any]:
    """
    查询磁盘或分区信息。
    输入参数：
        - path: 设备或分区路径（str），如"/dev/disk2" 或 "/dev/disk2s1"
    返回值：
        - Dict[str, Any]:
            - ok: 是否查询成功（bool）
            - code: 状态码（str），如 'SUCCESS'、'INFO_FAILED'
            - message: 说明信息（str）
            - data: 详细信息（dict，查询到的信息，失败时为 None）
    """
    if not path or not path.startswith("/dev/"):
        return {"ok": False, "code": "INFO_FAILED", "message": "无效的设备路径", "data": None}
    try:
        result = subprocess.run(
            ["diskutil", "info", "-plist", path],
            capture_output=True,
            timeout=10,
            # check=True  ← 已移除，原因同 unmount_device
        )
        if result.returncode != 0:
            return {
                "ok": False,
                "code": "INFO_FAILED",
                "message": result.stderr.decode("utf-8", errors="replace"),
                "data": None,
            }
        # 原有代码在函数内部 import plistlib，已移至文件顶部
        # import plistlib  ← 已移除
        info = plistlib.loads(result.stdout)
        return {"ok": True, "code": "SUCCESS", "message": "查询成功", "data": info}
    except subprocess.TimeoutExpired:
        logger.error("get_disk_info 超时: %s", path)
        return {"ok": False, "code": "INFO_FAILED", "message": "查询超时", "data": None}
    except Exception as e:
        logger.error("get_disk_info 异常: %s", e)
        return {"ok": False, "code": "INFO_FAILED", "message": "查询磁盘信息失败", "data": None}


def format_gb(size_bytes: int) -> str:
    gb = size_bytes / (1024 ** 3)
    return f"{gb:.2f} GB"


def print_disk_summary(info: dict):
    """
    实用磁盘信息摘要输出。
    """
    if not info:
        print("无磁盘信息")
        return
    # 兼容不同key
    fs_type = info.get("FilesystemName") or info.get("Content") or "-"
    device = info.get("DeviceNode") or info.get("DeviceIdentifier") or "-"
    size = info.get("TotalSize") or info.get("Size") or 0
    size_gb = f"{int(size) / (1024 ** 3):.2f} GB" if size else "-"
    vol_name = info.get("VolumeName") or "-"
    mount_point = info.get("MountPoint") or "-"
    is_system = info.get("Internal") or info.get("OSInternalMedia") or False
    print(f"设备路径: {device}")
    print(f"卷标名: {vol_name}")
    print(f"文件系统类型: {fs_type}")
    print(f"总容量: {size_gb}")
    print(f"挂载点: {mount_point}")
    print(f"是否内置/系统盘: {is_system}")


def ask_volume_name(default_name="Untitled") -> str:
    name = input(f"请输入卷标名（默认{default_name}）: ")
    return name.strip() or default_name

def list_partitions(device_info: dict) -> list:
    """
    返回磁盘所有分区的设备路径和卷标名列表。
    """
    partitions = []
    for part_key in ("Partitions", "APFSVolumes"):
        for part in device_info.get(part_key, []):
            dev = part.get("DeviceIdentifier")
            if dev:
                path = f"/dev/{dev}"
                name = part.get("VolumeName") or "-"
                partitions.append((path, name))
    return partitions