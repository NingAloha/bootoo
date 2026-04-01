# bootoo

适用于 Apple Silicon Mac 的启动盘制作工具。专注 M 系列芯片，把设备检测、写盘流程、引导兼容、错误恢复做到稳定易用。

> 当前范围：仅支持 M 系列芯片（Apple Silicon）Mac，不包含 Intel Mac 及 Windows/Linux 本地运行版本。

---

## 下载与安装

1. 前往 [Releases](../../releases) 页面，下载最新版 `bootoo-vX.X.X-arm64-macos.zip`
2. 解压：

```bash
unzip bootoo-vX.X.X-arm64-macos.zip
```

3. 赋予执行权限：

```bash
chmod +x bootoo
```

4. 可选：移动到 PATH 以便全局使用：

```bash
sudo mv bootoo /usr/local/bin/bootoo
```

无需安装 Python，开箱即用。

---

## 使用方式

### 扫描设备

```bash
# 列出可用外置设备
./bootoo scan

# 列出所有设备（含系统盘和内置盘）
./bootoo scan --all
```

### 写入镜像

**写入操作需要 sudo 权限，否则会提示权限不足。**

```bash
sudo ./bootoo write ~/Downloads/ubuntu.iso /dev/disk2
```

流程说明：
1. 自动校验镜像格式与大小
2. 确认目标设备在可用列表中
3. 提示确认（输入 `yes` 继续，避免误操作）
4. 自动卸载设备
5. 写入并显示进度条
6. 写入完成或失败时给出提示

支持格式：`.iso` / `.img`（使用 dd）、`.dmg`（使用 asr）

### 写后校验

```bash
# 获取镜像字节数
stat -f%z ~/Downloads/ubuntu.iso

# 基础校验（容量 + 分区）
./bootoo verify /dev/disk2 <镜像字节数>

# 完整校验（含引导文件，需提供挂载点）
./bootoo verify /dev/disk2 <镜像字节数> /Volumes/USB linux
# os_type 支持：windows / linux / macos（默认 windows）
```

### 查看帮助

```bash
./bootoo help
```

---

## 典型完整流程

```bash
# 1. 确认设备路径
./bootoo scan

# 2. 写入（需 sudo）
sudo ./bootoo write ~/Downloads/ubuntu-24.04-desktop-amd64.iso /dev/disk2

# 3. 写后校验
./bootoo verify /dev/disk2 $(stat -f%z ~/Downloads/ubuntu-24.04-desktop-amd64.iso)
```

---

## 项目结构

```
bootoo/
├── core/
│   ├── mac/                    # Apple Silicon 核心实现
│   │   ├── device_detection.py     # 设备扫描与筛选
│   │   ├── permission_guard.py     # 权限与可写性检查（自动卸载）
│   │   ├── image_utils.py          # 镜像校验（格式/大小/SHA256）
│   │   ├── disk_ops.py             # 卸载、格式化、磁盘信息查询
│   │   ├── write_engine.py         # 写入引擎（dd/asr，进度回调）
│   │   ├── verify.py               # 写后校验（容量/分区/引导文件）
│   │   ├── recovery.py             # 失败恢复与修复建议
│   │   ├── log.py                  # 统一日志入口
│   │   └── errors.py               # 统一错误类型与错误码
│   ├── api/
│   │   └── bootoo_api.py           # 对外稳定接口层
│   └── config/                 # 运行配置（待填充）
├── dist/
│   ├── bin/                    # 可执行文件
│   └── release/                # 发布归档
├── scripts/mac/                # 开发期调试脚本
├── tests/mac/apple_silicon/    # 单元测试
└── docs/                       # 架构与开发文档
```

---

## 开发者接口

所有接口返回统一结构：`{"ok": bool, "code": str, "message": str, "data": dict | None}`

支持 `--json` 输出模式，便于 GUI 或脚本集成：

```bash
./bootoo scan --json
sudo ./bootoo write ~/Downloads/ubuntu.iso /dev/disk2 --json
./bootoo verify /dev/disk2 3276800000 --json
```

Python API 示例：

```python
from core.api.bootoo_api import get_available_devices, write_image, verify_result

devices = get_available_devices()
result  = write_image("~/Downloads/ubuntu.iso", "/dev/disk2",
                      progress_callback=lambda p: print(f"{p:.1f}%"))
if result["ok"]:
    verify_result("/dev/disk2", 3276800000)
```

详细接口文档见 [core/api/README.md](core/api/README.md)，模块文档见 [core/mac/README.md](core/mac/README.md)。

---

## 错误码参考

| 错误码 | 含义 |
|--------|------|
| `PERMISSION_DENIED` | 权限不足，请用 sudo 运行 |
| `DEVICE_BUSY` | 设备正忙（已自动尝试卸载） |
| `IMAGE_NOT_FOUND` | 镜像文件不存在 |
| `IMAGE_FORMAT_INVALID` | 镜像格式不支持 |
| `UNMOUNT_FAILED` | 卸载失败 |
| `DD_FAILED` | dd 写入失败 |
| `ASR_FAILED` | asr 写入失败 |
| `VERIFY_CAPACITY_FAIL` | 设备容量不足 |
| `VERIFY_PARTITION_FAIL` | 写入后未检测到分区 |
| `VERIFY_FILES_FAIL` | 引导文件缺失 |
| `RECOVERY_FAILED` | 恢复操作失败 |

---

## 分支说明

当前分支（`apple_silicon`）由 **NingAloha** 全权负责，专注 M 系列芯片 Mac。如需协作或贡献新平台支持，欢迎通过 Issue 或 PR 交流。
