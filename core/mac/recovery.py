"""
失败回滚与修复建议。
写入失败后，提供重新分区、重新挂载等恢复操作，并给出用户可读的修复建议。
"""

import subprocess
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


# ── 内部操作 ────────────────────────────────────────────────────────────────────

def _remount_device(device_path: str) -> Dict[str, Any]:
    """尝试重新挂载设备。"""
    try:
        result = subprocess.run(
            ["diskutil", "mountDisk", device_path],
            capture_output=True,
            timeout=30,
        )
        ok = result.returncode == 0
        return {
            "ok": ok,
            "message": "重新挂载成功" if ok else result.stderr.decode("utf-8", errors="replace").strip(),
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "message": "重新挂载超时"}
    except Exception as e:
        logger.error("_remount_device 异常: %s", e)
        return {"ok": False, "message": "重新挂载失败"}


def _repartition_device(device_path: str, fs_type: str = "exFAT", name: str = "Untitled") -> Dict[str, Any]:
    """
    对设备执行整盘抹除并重新分区（MBR + 单分区）。
    仅在用户确认后调用，此操作不可逆。
    """
    if not device_path or not device_path.startswith("/dev/"):
        return {"ok": False, "message": "无效的设备路径"}
    try:
        result = subprocess.run(
            ["diskutil", "eraseDisk", fs_type, name, "MBR", device_path],
            capture_output=True,
            timeout=120,
        )
        ok = result.returncode == 0
        return {
            "ok": ok,
            "message": "重新分区成功" if ok else result.stderr.decode("utf-8", errors="replace").strip(),
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "message": "重新分区超时"}
    except Exception as e:
        logger.error("_repartition_device 异常: %s", e)
        return {"ok": False, "message": "重新分区失败"}


# ── 修复建议生成 ────────────────────────────────────────────────────────────────

def _build_suggestions(error_code: str) -> List[str]:
    """根据错误码返回用户可读的修复建议列表。"""
    suggestions_map: Dict[str, List[str]] = {
        "DD_FAILED": [
            "确认目标设备已正确插入并被系统识别（diskutil list）",
            "确认以 sudo/root 权限运行",
            "尝试先卸载设备后重试写入",
            "检查镜像文件完整性（SHA256）",
        ],
        "ASR_FAILED": [
            "确认 DMG 镜像未损坏（hdiutil verify <image>）",
            "确认目标设备容量足够",
            "确认以 sudo/root 权限运行",
            "尝试先卸载设备后重试写入",
        ],
        "UNMOUNT_FAILED": [
            "关闭正在访问该设备的应用程序",
            "在终端执行 lsof | grep /dev/diskX 查找占用进程",
            "尝试手动弹出设备后重新插入",
        ],
        "FORMAT_FAILED": [
            "确认分区路径正确（如 /dev/disk2s1）",
            "确认设备未被其他进程占用",
            "尝试先卸载整个磁盘再格式化",
        ],
        "VERIFY_CAPACITY_FAIL": [
            "使用容量更大的 U 盘",
            "确认镜像文件未损坏或被截断",
        ],
        "VERIFY_PARTITION_FAIL": [
            "写入可能不完整，建议重新写入",
            "尝试重新分区后再次写入",
            "检查设备是否支持目标文件系统",
        ],
        "VERIFY_FILES_FAIL": [
            "镜像可能不包含完整引导文件，确认镜像来源",
            "尝试重新下载镜像并校验 SHA256",
            "确认镜像与目标系统类型匹配",
        ],
        "PERMISSION_DENIED": [
            "以 sudo/root 权限重新运行",
            "确认当前用户在 admin 组（dscl . -read /Groups/admin GroupMembership）",
        ],
        "DEVICE_BUSY": [
            "关闭访问该设备的所有应用",
            "执行 diskutil unmountDisk /dev/diskX 后重试",
        ],
    }
    return suggestions_map.get(error_code, ["检查设备连接状态后重试", "如问题持续，请提交 Issue 并附上日志"])


# ── 对外接口 ────────────────────────────────────────────────────────────────────

def get_recovery_suggestions(error_code: str) -> Dict[str, Any]:
    """
    根据错误码返回用户可读的修复建议，不执行任何实际操作。
    输入参数：
        - error_code: 错误码（str），如 'DD_FAILED'、'UNMOUNT_FAILED'
    返回值：
        - Dict[str, Any]: {ok, code, message, data}
            - data.suggestions: 修复建议列表（List[str]）
    """
    suggestions = _build_suggestions(error_code)
    return {
        "ok": True,
        "code": "SUCCESS",
        "message": f"针对 {error_code} 的修复建议",
        "data": {"error_code": error_code, "suggestions": suggestions},
    }


def attempt_remount(device_path: str) -> Dict[str, Any]:
    """
    尝试重新挂载设备（写入失败后的轻量恢复）。
    输入参数：
        - device_path: 设备路径（str），如 "/dev/disk2"
    返回值：
        - Dict[str, Any]: {ok, code, message, data}
    """
    if not device_path or not device_path.startswith("/dev/"):
        return {"ok": False, "code": "RECOVERY_FAILED", "message": "无效的设备路径", "data": None}

    result = _remount_device(device_path)
    return {
        "ok": result["ok"],
        "code": "SUCCESS" if result["ok"] else "RECOVERY_FAILED",
        "message": result["message"],
        "data": {"device_path": device_path} if result["ok"] else None,
    }


def attempt_repartition(device_path: str, fs_type: str = "exFAT", name: str = "Untitled") -> Dict[str, Any]:
    """
    对设备执行整盘抹除并重新分区（不可逆，调用前需用户确认）。
    输入参数：
        - device_path: 设备路径（str），如 "/dev/disk2"
        - fs_type: 文件系统类型（str），默认 "exFAT"
        - name: 卷标名（str），默认 "Untitled"
    返回值：
        - Dict[str, Any]: {ok, code, message, data}
    """
    if not device_path or not device_path.startswith("/dev/"):
        return {"ok": False, "code": "RECOVERY_FAILED", "message": "无效的设备路径", "data": None}

    result = _repartition_device(device_path, fs_type, name)
    return {
        "ok": result["ok"],
        "code": "SUCCESS" if result["ok"] else "RECOVERY_FAILED",
        "message": result["message"],
        "data": {"device_path": device_path, "fs_type": fs_type, "name": name} if result["ok"] else None,
    }
