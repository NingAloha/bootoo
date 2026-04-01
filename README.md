# bootoo

适用于 Apple Silicon Mac 的启动盘制作工具。专注 M 系列芯片，把设备检测、写盘流程、引导兼容、错误恢复做到稳定易用。

---

## 项目背景

Mac 平台缺乏一个真正简单易用的启动盘制作工具。Rufus 仅限 Windows，Etcher 对 Windows/Linux 系统盘支持不完善，Boot Camp 早已不支持 M 系列芯片。bootoo 由此而来，专注 Apple Silicon，不分散到其他平台。

---

## 当前范围（Scope）

- 仅支持 M 系列芯片（Apple Silicon）Mac
- 不包含 Intel Mac 支持
- 不包含 Windows/Linux 本地运行版本

---

## 项目结构

```
bootoo/
├── core/
│   ├── mac/                    # Apple Silicon 核心实现
│   │   ├── device_detection.py     # 设备扫描与筛选
│   │   ├── permission_guard.py     # 权限与可写性检查
│   │   ├── image_utils.py          # 镜像校验（格式/大小/SHA256）
│   │   ├── disk_ops.py             # 卸载、格式化、磁盘信息查询
│   │   ├── write_engine.py         # 写入引擎（dd/asr，进度回调）
│   │   ├── verify.py               # 写后校验（容量/分区/引导文件）
│   │   ├── recovery.py             # 失败恢复与修复建议
│   │   ├── log.py                  # 统一日志入口
│   │   └── errors.py               # 统一错误类型与错误码
│   ├── api/
│   │   ├── bootoo_api.py           # 对外稳定接口层
│   │   ├── contracts.py            # 进度回调协议（待实现）
│   │   └── models.py               # 请求/响应数据结构（待实现）
│   └── config/
│       ├── default.yaml            # 默认参数（待填充）
│       ├── device_rules.yaml       # 设备过滤规则（待填充）
│       └── image_rules.yaml        # 镜像类型白名单（待填充）
├── ui/                         # GUI（待开发）
├── scripts/mac/                # 开发期调试脚本
├── docs/                       # 架构、开发、兼容性文档
├── resources/test_iso/         # 测试镜像（勿提交大文件）
└── tests/mac/apple_silicon/    # 单元测试与集成测试
```

---

## 核心流程

```
设备扫描 → 权限检查 → 镜像校验 → 卸载 → 写入 → 写后校验 → 成功收尾 / 失败恢复
```

---

## core/mac 模块说明

| 模块 | 状态 | 主要接口 |
|------|------|----------|
| `device_detection.py` | ✅ 完成 | `list_all_devices()`, `list_available_devices(min_size_bytes)` |
| `permission_guard.py` | ✅ 完成 | `check_device_writable(device)` |
| `image_utils.py` | ✅ 完成 | `check_image(path)` |
| `disk_ops.py` | ✅ 完成 | `unmount_device()`, `format_disk()`, `get_disk_info()` |
| `write_engine.py` | ✅ 完成 | `write_image_auto(src, dst, progress_callback)` |
| `verify.py` | ✅ 完成 | `verify_write_result()`, `verify_capacity()`, `verify_partition_exists()`, `verify_required_files()` |
| `recovery.py` | ✅ 完成 | `get_recovery_suggestions()`, `attempt_remount()`, `attempt_repartition()` |
| `log.py` | ✅ 完成 | `setup_logging()`, `get_logger(name)` |
| `errors.py` | ✅ 完成 | 错误码常量 + 异常类（`BootooError` 及子类） |

---

## core/api 接口说明

所有接口返回统一结构：`{"ok": bool, "code": str, "message": str, "data": dict | None}`

| 接口 | 说明 |
|------|------|
| `check_image_file(path)` | 镜像存在性、格式、大小、SHA256 |
| `get_all_devices()` | 获取所有磁盘（含系统盘） |
| `get_available_devices(min_size_bytes)` | 获取可写入的外置设备 |
| `check_selected_device_writable(device)` | 检查设备可写性 |
| `unmount_device(device_path)` | 卸载磁盘或分区 |
| `format_disk(partition_path, fs_type, name)` | 格式化分区 |
| `get_disk_info(path)` | 查询磁盘/分区信息 |
| `write_image(src, dst, progress_callback)` | 写入镜像（自动选 dd/asr） |
| `verify_result(device_path, image_size_bytes, mount_point, os_type)` | 写后综合校验 |
| `verify_device_capacity(device_path, image_size_bytes)` | 单独容量校验 |
| `verify_device_partition(device_path)` | 单独分区存在性校验 |
| `verify_boot_files(mount_point, os_type)` | 引导文件校验 |
| `get_suggestions(error_code)` | 根据错误码获取修复建议 |
| `remount_device(device_path)` | 尝试重新挂载设备 |
| `repartition_device(device_path, fs_type, name)` | 整盘抹除并重新分区（不可逆） |

---

## 快速开始

```python
from core.api.bootoo_api import (
    get_available_devices,
    check_image_file,
    write_image,
    verify_result,
    get_suggestions,
)

# 1. 扫描可用设备
devices = get_available_devices()

# 2. 校验镜像
img = check_image_file("~/Downloads/ubuntu.iso")

# 3. 写入（需 sudo）
result = write_image(
    src="~/Downloads/ubuntu.iso",
    dst="/dev/disk2",
    progress_callback=lambda p: print(f"{p:.1f}%"),
)

# 4. 写后校验
if result["ok"]:
    verify_result("/dev/disk2", img["data"]["size"])
else:
    print(get_suggestions(result["code"])["data"]["suggestions"])
```

---

## 日志配置

```python
from core.mac.log import setup_logging
import logging

# 程序入口处调用一次
setup_logging(level=logging.INFO, log_file="bootoo.log")
```

---

## 错误码参考

| 错误码 | 含义 |
|--------|------|
| `DEVICE_SCAN_FAILED` | 设备扫描失败 |
| `PERMISSION_DENIED` | 权限不足 |
| `DEVICE_BUSY` | 设备正忙 |
| `IMAGE_NOT_FOUND` | 镜像文件不存在 |
| `IMAGE_FORMAT_INVALID` | 镜像格式不支持 |
| `UNMOUNT_FAILED` | 卸载失败 |
| `FORMAT_FAILED` | 格式化失败 |
| `DD_FAILED` | dd 写入失败 |
| `ASR_FAILED` | asr 写入失败 |
| `VERIFY_CAPACITY_FAIL` | 容量校验失败 |
| `VERIFY_PARTITION_FAIL` | 分区校验失败 |
| `VERIFY_FILES_FAIL` | 引导文件校验失败 |
| `RECOVERY_FAILED` | 恢复操作失败 |

---

## 多语言集成与分支说明

核心功能以 Python 为主，底层性能或系统相关模块可用 C/C++/Swift 实现，通过统一 API 层集成。当前分支（Apple Silicon Mac 版）由 **NingAloha** 全权负责。

如需协作、贡献新平台支持或有多语言集成相关建议，欢迎通过 Issue 或 PR 交流。
