# core/api 文件夹结构说明

```
core/api/
├── bootoo_api.py       # 对外稳定接口层
├── contracts.py        # 进度回调协议（待实现）
├── models.py           # 请求/响应数据结构（待实现）
└── README.md
```

---

## 设计原则

- 所有接口返回统一结构：`{"ok": bool, "code": str, "message": str, "data": dict | None}`
- 上层（CLI/UI）只依赖此层，不直接调用 `core/mac` 内部模块
- 进度统一为 0–100 浮点数，通过 `progress_callback` 回调传递

---

## bootoo_api.py 接口说明

### 镜像校验

#### `check_image_file(path: str) -> Dict[str, Any]`

检查镜像文件的存在性、格式、大小和 SHA256。

| 参数 | 类型 | 说明 |
|------|------|------|
| `path` | str | 镜像文件路径，支持 `~/` 展开 |

`data` 字段（成功）：`path`, `format`, `size`, `sha256`
错误码：`IMAGE_NOT_FOUND`、`IMAGE_FORMAT_INVALID`

---

### 设备管理

#### `get_all_devices() -> List[Dict[str, Any]]`

获取所有磁盘设备（含系统盘）。

每个设备字典字段：`id`, `device`, `size_bytes`, `internal`, `removable`, `mounted`, `volumes`, `is_system_risk`, `content`

#### `get_available_devices(min_size_bytes: int = 1GB) -> List[Dict[str, Any]]`

获取通过安全筛选的可写入外置设备（过滤系统盘、内置盘、APFS 容器、容量不足）。

#### `check_selected_device_writable(device: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]`

检查设备是否可写。

| 参数 | 类型 | 说明 |
|------|------|------|
| `device` | dict | 需含 `device`（路径）和 `id` 字段 |

返回 `(bool, {id, device, writable, info})`。

---

### 磁盘操作

#### `unmount_device(device_path: str) -> Dict[str, Any]`

卸载磁盘或分区。

| 参数 | 类型 | 说明 |
|------|------|------|
| `device_path` | str | 如 `/dev/disk2` 或 `/dev/disk2s1` |

错误码：`SUCCESS`、`UNMOUNT_FAILED`

#### `format_disk(partition_path: str, fs_type: str = "exFAT", name: str = "Untitled") -> Dict[str, Any]`

格式化分区，格式化前自动尝试卸载。

| 参数 | 类型 | 说明 |
|------|------|------|
| `partition_path` | str | 如 `/dev/disk2s1` |
| `fs_type` | str | `exFAT`、`MS-DOS FAT32`、`APFS`、`JHFS+` |
| `name` | str | 卷标名，自动截断并过滤非 ASCII 字符 |

`data` 字段（成功）：`partition_path`, `fs_type`, `name`, `unmount_ok`
错误码：`SUCCESS`、`FORMAT_FAILED`

#### `get_disk_info(path: str) -> Dict[str, Any]`

查询磁盘或分区信息（`diskutil info -plist`）。

错误码：`SUCCESS`、`INFO_FAILED`

---

### 写入

#### `write_image(src: str, dst: str, progress_callback=None) -> Dict[str, Any]`

自动判断镜像类型（`.dmg` 用 `asr`，其余用 `dd`）并写入目标设备。

| 参数 | 类型 | 说明 |
|------|------|------|
| `src` | str | 源镜像路径 |
| `dst` | str | 目标设备路径，须以 `/dev/` 开头 |
| `progress_callback` | `Callable[[float], None]` | 可选，进度 0–100 |

`data` 字段（成功）：`src`, `dst`, `image_size`
错误码：`SUCCESS`、`DD_FAILED`、`ASR_FAILED`、`SRC_ERROR`、`DST_ERROR`

---

### 写后校验

#### `verify_result(device_path, image_size_bytes, mount_point=None, os_type="windows") -> Dict[str, Any]`

综合校验入口，依次执行容量、分区存在性、引导文件三项检查，任一失败立即返回。

| 参数 | 类型 | 说明 |
|------|------|------|
| `device_path` | str | 如 `/dev/disk2` |
| `image_size_bytes` | int | 镜像文件大小（字节） |
| `mount_point` | str \| None | 提供时执行引导文件校验 |
| `os_type` | str | `"windows"`、`"linux"`、`"macos"` |

`data` 字段：`{capacity: ..., partition: ..., files: ...}`（各步骤结果）
错误码：`SUCCESS`、`VERIFY_CAPACITY_FAIL`、`VERIFY_PARTITION_FAIL`、`VERIFY_FILES_FAIL`

#### `verify_device_capacity(device_path: str, image_size_bytes: int) -> Dict[str, Any]`

单独校验设备容量是否 ≥ 镜像大小。

#### `verify_device_partition(device_path: str) -> Dict[str, Any]`

单独校验写入后是否存在至少一个可识别分区。

#### `verify_boot_files(mount_point: str, os_type: str = "windows") -> Dict[str, Any]`

校验挂载点下是否存在必要引导文件。支持 `"windows"`、`"linux"`、`"macos"`。

---

### 恢复

#### `get_suggestions(error_code: str) -> Dict[str, Any]`

根据错误码返回用户可读的修复建议，不执行任何实际操作。

`data.suggestions`：`List[str]`

覆盖的错误码：`DD_FAILED`、`ASR_FAILED`、`UNMOUNT_FAILED`、`FORMAT_FAILED`、`VERIFY_CAPACITY_FAIL`、`VERIFY_PARTITION_FAIL`、`VERIFY_FILES_FAIL`、`PERMISSION_DENIED`、`DEVICE_BUSY`

#### `remount_device(device_path: str) -> Dict[str, Any]`

尝试重新挂载设备（`diskutil mountDisk`），写入失败后的轻量恢复。

错误码：`SUCCESS`、`RECOVERY_FAILED`

#### `repartition_device(device_path: str, fs_type: str = "exFAT", name: str = "Untitled") -> Dict[str, Any]`

整盘抹除并重新分区（`diskutil eraseDisk MBR`）。**不可逆，调用前需用户确认。**

错误码：`SUCCESS`、`RECOVERY_FAILED`

---

## contracts.py / models.py

待实现。计划用于定义进度回调协议（`ProgressCallback`）和请求/响应数据结构（dataclass 或 Pydantic）。
