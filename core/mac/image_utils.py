import os
import hashlib
from typing import Optional, Dict, Any

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
    if ext in ['.dmg', '.iso', '.img']:
        return ext[1:]
    return 'unknown'

def _calc_sha256(path: str) -> Optional[str]:
    """
    计算镜像文件的 SHA256 值
    :param path: 镜像文件路径
    :return: sha256 字符串，文件不存在时返回 None
    """
    if not os.path.isfile(path):
        return None
    sha256 = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def check_image(path: str) -> Dict[str, Any]:
    """
    对外接口：检查镜像文件的存在性、格式和 SHA256
    返回统一结构：{ok, code, message, data}
    """
    abs_path = os.path.expanduser(path)
    exists = _check_image_exists(abs_path)
    if not exists:
        return {
            "ok": False,
            "code": "IMAGE_NOT_FOUND",
            "message": f"镜像文件不存在: {abs_path}",
            "data": None
        }
    fmt = _get_image_format(abs_path)
    sha256 = _calc_sha256(abs_path)
    return {
        "ok": True,
        "code": "SUCCESS",
        "message": "镜像检查通过",
        "data": {
            "path": abs_path,
            "format": fmt,
            "sha256": sha256
        }
    }

if __name__ == "__main__":
    # 示例测试路径，可根据实际情况修改
    test_paths = [
        "resources/test_iso/blank_1mb.iso",
        "resources/test_iso/blank_10mb.dmg",
        "resources/test_iso/blank_10mb.img"
    ]

    for path in test_paths:
        result = check_image(path)
        print(f"测试文件: {os.path.expanduser(path)}")
        print(f"  ok: {result['ok']}")
        print(f"  code: {result['code']}")
        print(f"  message: {result['message']}")
        if result["data"]:
            print(f"  data: {result['data']}")
        print("-" * 40)