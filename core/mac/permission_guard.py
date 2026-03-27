from typing import Dict, Any, Tuple
import os

def check_device_writable(device: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    检查设备是否可写，并返回详细结果。
    输入参数：
        - device: 设备信息字典，需包含 device（路径）和 id 字段
    返回值：
        - Tuple[bool, Dict[str, Any]]
            - bool: True 表示可写，False 表示不可写
            - Dict[str, Any]: 结果详情，字段包括 id/device/writable/info
    """
    dev_path = device.get("device")
    if not dev_path:
        result = {"id": device.get("id"), "device": dev_path, "writable": False, "info": "无设备路径"}
        return False, result
    writable, reason = _check_writable(dev_path)
    info = "可写" if writable else f"不可写（{reason}）"
    result = {"id": device.get("id"), "device": dev_path, "writable": writable, "info": info}
    return writable, result

def _check_writable(dev_path: str) -> Tuple[bool, str]:
    """
    检查指定设备路径是否可写。
    输入参数：
        - dev_path: 设备路径（str）
    返回值：
        - Tuple[bool, str]
            - bool: True 表示可写，False 表示不可写
            - str: 不可写时的原因说明
    """
    if not os.access(dev_path, os.W_OK):
        return False, "权限不足或未授权"
    try:
        fd = os.open(dev_path, os.O_WRONLY)
        os.close(fd)
        return True, ""
    except PermissionError:
        return False, "权限不足"
    except OSError as e:
        if e.errno == 16:
            return False, "设备被占用（可能已挂载或被其他进程占用）"
        elif e.errno == 30:
            return False, "只读文件系统"
        else:
            return False, f"系统错误: {e.strerror}"
    except Exception as e:
        return False, f"未知错误: {e}"