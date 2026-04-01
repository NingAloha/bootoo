import os
import hashlib
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

_SUPPORTED_EXTENSIONS = {'.dmg', '.iso', '.img'}

def _check_image_exists(path: str) -> bool:
    """
    检查镜像文件是否存在
    :param path: 镜像文件路径
    :return: 存在返回 True，否则 False
    """
    return os.path.isfile(path)

def _get_image_format(path: str) -> str:
    """
    简单识别镜像格式（基于扩展名，可扩展为更复杂的识别）
    :param path: 镜像文件路径
    :return: 格式字符串，如 'dmg', 'iso', 'img'，未知返回 'unknown'
    """
    ext = os.path.splitext(path)[1].lower()
    # 原有代码使用列表 ['.dmg', '.iso', '.img']，已改为集合常量 _SUPPORTED_EXTENSIONS，O(1) 查找
    # if ext in ['.dmg', '.iso', '.img']:  ← 已替换
    if ext in _SUPPORTED_EXTENSIONS:
        return ext[1:]
    return 'unknown'

def _get_image_size(path: str) -> Optional[int]:
    """
    获取镜像文件大小（字节），文件不存在或无法读取时返回 None。
    :param path: 镜像文件路径
    :return: 文件大小（int，字节），失败返回 None
    """
    try:
        return os.path.getsize(path)
    except Exception:
        return None

def _calc_sha256(path: str) -> Optional[str]:
    """
    计算镜像文件的 SHA256 值
    :param path: 镜像文件路径
    :return: sha256 字符串，文件不存在时返回 None
    """
    if not os.path.isfile(path):
        return None
    sha256 = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                # 原有代码块大小为 8192 字节，已调整为 65536（64KB），减少系统调用次数
                # f.read(8192)  ← 已替换
                sha256.update(chunk)
    except OSError as e:
        logger.error("SHA256 计算失败: %s", e)
        return None
    return sha256.hexdigest()

def check_image(path: str) -> Dict[str, Any]:
    """
    对外接口：检查镜像文件的存在性、格式、大小和 SHA256
    返回统一结构：{ok, code, message, data}
    """
    abs_path = os.path.expanduser(path)
    if not _check_image_exists(abs_path):
        # 原有代码在 message 中拼接 abs_path，可能泄露文件系统路径，已移至 data 字段
        # "message": f"镜像文件不存在: {abs_path}"  ← 已替换
        return {
            "ok": False,
            "code": "IMAGE_NOT_FOUND",
            "message": "镜像文件不存在",
            "data": {"path": abs_path}
        }
    fmt = _get_image_format(abs_path)
    size = _get_image_size(abs_path)
    sha256 = _calc_sha256(abs_path)
    return {
        "ok": True,
        "code": "SUCCESS",
        "message": "镜像检查通过",
        "data": {
            "path": abs_path,
            "format": fmt,
            "size": size,
            "sha256": sha256,
        }
    }