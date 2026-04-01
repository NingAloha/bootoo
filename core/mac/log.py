"""
统一日志入口，支持文件输出与终端输出。
调用方只需 from core.mac.log import get_logger，无需关心底层配置。
"""

import logging
import logging.handlers
import os
import sys
from typing import Optional

# 默认日志格式
_TEXT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 模块级标志，避免重复初始化
_initialized = False


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 3,
) -> None:
    """
    初始化全局日志配置。应在程序入口处调用一次。
    输入参数：
        - level: 日志级别，默认 INFO
        - log_file: 日志文件路径（可选），为 None 时仅输出到终端
        - max_bytes: 单个日志文件最大字节数，默认 5MB
        - backup_count: 保留的历史日志文件数，默认 3
    """
    global _initialized
    if _initialized:
        return

    formatter = logging.Formatter(_TEXT_FORMAT, datefmt=_DATE_FORMAT)
    root = logging.getLogger()
    root.setLevel(level)

    # 终端 handler（stderr）
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    # 文件 handler（可选，滚动写入）
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    _initialized = True


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的 logger。
    输入参数：
        - name: logger 名称，通常传 __name__
    返回值：
        - logging.Logger
    """
    return logging.getLogger(name)
