from typing import Dict, Any, Tuple
import os
import errno
import logging
import stat

logger = logging.getLogger(__name__)

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
        return False, {"id": device.get("id"), "device": dev_path, "writable": False, "info": "无设备路径"}
    writable, reason = _check_writable(dev_path)
    info = "可写" if writable else f"不可写（{reason}）"
    return writable, {"id": device.get("id"), "device": dev_path, "writable": writable, "info": info}

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
    # 路径必须以 /dev/ 开头
    if not dev_path or not dev_path.startswith("/dev/"):
        return False, "无效的设备路径"

    # 校验路径指向块设备或字符设备，防止误操作普通文件
    try:
        st = os.stat(dev_path)
        if not (stat.S_ISBLK(st.st_mode) or stat.S_ISCHR(st.st_mode)):
            return False, "路径不是块设备或字符设备"
    except OSError:
        return False, "设备路径不存在或无法访问"

    # 原有代码先调用 os.access() 再调用 os.open()，存在 TOCTOU 竞态，且 os.access() 结果不可靠。
    # 已移除 os.access() 检查，直接尝试 os.open() 并捕获异常。
    # if not os.access(dev_path, os.W_OK):  ← 已移除
    #     return False, "权限不足或未授权"
    try:
        # O_WRONLY | O_NONBLOCK：非阻塞探测，避免对设备产生实际写入副作用
        fd = os.open(dev_path, os.O_WRONLY | os.O_NONBLOCK)
        os.close(fd)
        return True, ""
    except PermissionError:
        return False, "权限不足"
    except OSError as e:
        # 原有代码使用魔法数字 16 和 30，已替换为 errno 常量
        # if e.errno == 16:  ← 已替换为 errno.EBUSY
        # elif e.errno == 30:  ← 已替换为 errno.EROFS
        if e.errno == errno.EBUSY:
            return False, "设备被占用（可能已挂载或被其他进程占用）"
        elif e.errno == errno.EROFS:
            return False, "只读文件系统"
        else:
            return False, f"系统错误: {e.strerror}"
    except Exception as e:
        logger.error("_check_writable 未知错误: %s", e)
        return False, "未知错误"