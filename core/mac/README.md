## core/mac 文件夹结构说明

```
core/mac/
├── device_detection.py     # 设备扫描与筛选
├── permission_guard.py     # 权限与可写性检查
├── image_utils.py          # 镜像校验（格式/大小/SHA256）
├── disk_ops.py             # 卸载、格式化、磁盘信息查询
├── write_engine.py         # 写入引擎（dd/asr，进度回调）
├── verify.py               # 写后校验（容量/分区/引导文件）
├── recovery.py             # 失败恢复与修复建议
├── log.py                  # 统一日志入口
├── errors.py               # 统一错误类型与错误码
├── commands/               # 预留子目录（当前为空）
└── README.md
```

---

## 模块说明

### device_detection.py

设备扫描与筛选，通过 `diskutil list -plist` 枚举所有磁盘，过滤系统盘、内置盘、APFS 容器和容量不足的设备。

私有函数：

- `_scan_devices() -> List[Dict[str, Any]]`
  - 扫描本机所有磁盘，返回设备信息列表。
  - 每个字典字段：`id`, `device`, `size_bytes`, `internal`, `removable`, `mounted`, `volumes`, `is_system_risk`, `content`

- `_validate_target(device: Dict[str, Any], min_size_bytes: int = 1GB) -> bool`
  - 校验设备是否为可用目标盘（非内置、非系统风险、非 APFS 容器、容量达标）。

公共接口：

- `list_all_devices() -> List[Dict[str, Any]]`
  - 返回所有磁盘设备（含系统盘）。

- `list_available_devices(min_size_bytes: int = 1GB) -> List[Dict[str, Any]]`
  - 返回通过 `_validate_target` 筛选的可写入外置设备。

---

### permission_guard.py

权限与可写性检查，使用 `O_WRONLY | O_NONBLOCK` 探测，不产生写入副作用。

私有函数：

- `_check_writable(dev_path: str) -> Tuple[bool, str]`
  - 检查设备路径是否可写，返回 `(bool, 原因说明)`。
  - 区分 `EBUSY`（设备忙）、`EROFS`（只读）、`EACCES`（权限不足）等错误。

公共接口：

- `check_device_writable(device: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]`
  - 输入设备字典（需含 `device` 和 `id` 字段）。
  - 返回 `(bool, {id, device, writable, info})`。

---

### image_utils.py

镜像文件校验，支持 `.dmg`、`.iso`、`.img`，自动展开 `~/` 路径。

私有函数：

- `_check_image_exists(path: str) -> bool`
- `_get_image_format(path: str) -> str` — 返回 `'dmg'`、`'iso'`、`'img'`、`'unknown'`
- `_get_image_size(path: str) -> Optional[int]`
- `_calc_sha256(path: str) -> Optional[str]` — 65KB 分块读取

公共接口：

- `check_image(path: str) -> Dict[str, Any]`
  - 返回 `{ok, code, message, data}`，`data` 含 `path/format/size/sha256`。
  - 错误码：`IMAGE_NOT_FOUND`、`IMAGE_FORMAT_INVALID`

---

### disk_ops.py

封装 `diskutil` 相关操作，所有路径须以 `/dev/` 开头。

公共接口：

- `unmount_device(device_path: str) -> Dict[str, Any]`
  - 卸载磁盘或分区，超时 30s。
  - 错误码：`UNMOUNT_FAILED`

- `format_disk(partition_path: str, fs_type: str = "exFAT", name: str = "Untitled") -> Dict[str, Any]`
  - 支持 `exFAT`、`MS-DOS FAT32`、`APFS`、`JHFS+`。
  - 卷标自动截断（exFAT/FAT32 限 11 字符，其余限 27 字符）并过滤非 ASCII 字符。
  - 格式化前自动尝试卸载分区。
  - 错误码：`FORMAT_FAILED`

- `get_disk_info(path: str) -> Dict[str, Any]`
  - 通过 `diskutil info -plist` 查询，超时 10s。
  - 错误码：`INFO_FAILED`

辅助函数（内部使用）：

- `format_gb(size_bytes: int) -> str`
- `print_disk_summary(info: dict)`
- `ask_volume_name(default_name: str) -> str`
- `list_partitions(device_info: dict) -> list`

---

### write_engine.py

写入引擎，自动选择 `dd`（ISO/IMG）或 `asr`（DMG），支持进度回调。

私有函数：

- `_is_dmg(path: str) -> bool`
- `_get_image_size(src: str) -> Optional[int]`
- `_dd_write(src, dst, block_size=1MB, progress_callback) -> Dict[str, Any]`
  - macOS BSD `dd` 不支持 `status=progress`，改用 SIGINFO 信号每秒轮询进度。
  - 错误码：`DD_FAILED`、`SRC_ERROR`

- `_asr_restore(src, dst, progress_callback) -> Dict[str, Any]`
  - 默认开启写后校验（已移除 `--noverify`）。
  - 使用 `proc.communicate()` 避免 stdout/stderr 混合时的管道死锁。
  - 错误码：`ASR_FAILED`

公共接口：

- `write_image_auto(src: str, dst: str, progress_callback=None) -> Dict[str, Any]`
  - 写入前校验 `src` 存在性及 `dst` 路径合法性。
  - 返回 `{ok, code, message, data}`，`data` 含 `src/dst/image_size`。
  - 错误码：`SUCCESS`、`DD_FAILED`、`ASR_FAILED`、`SRC_ERROR`、`DST_ERROR`

---

### verify.py

写后校验，依次执行容量、分区存在性、引导文件三项检查。

公共接口：

- `verify_capacity(device_path: str, image_size_bytes: int) -> Dict[str, Any]`
  - 通过 `diskutil info -plist` 获取设备容量，校验是否 ≥ 镜像大小。
  - 错误码：`VERIFY_CAPACITY_FAIL`

- `verify_partition_exists(device_path: str) -> Dict[str, Any]`
  - 通过 `diskutil list -plist` 检查写入后是否存在至少一个分区。
  - 错误码：`VERIFY_PARTITION_FAIL`

- `verify_required_files(mount_point: str, os_type: str = "windows") -> Dict[str, Any]`
  - 校验挂载点下是否存在必要引导文件。
  - 支持 `os_type`：`"windows"`、`"linux"`、`"macos"`。
  - 错误码：`VERIFY_FILES_FAIL`

- `verify_write_result(device_path, image_size_bytes, mount_point=None, os_type="windows") -> Dict[str, Any]`
  - 综合校验入口，依次执行上述三项，任一失败立即返回。
  - `data` 字段包含各步骤结果。

---

### recovery.py

失败恢复与修复建议，提供轻量恢复操作和用户可读的修复指引。

公共接口：

- `get_recovery_suggestions(error_code: str) -> Dict[str, Any]`
  - 根据错误码返回修复建议列表，不执行任何实际操作。
  - `data.suggestions`：`List[str]`，覆盖 `DD_FAILED`、`ASR_FAILED`、`UNMOUNT_FAILED`、`FORMAT_FAILED`、`VERIFY_*`、`PERMISSION_DENIED`、`DEVICE_BUSY` 等。

- `attempt_remount(device_path: str) -> Dict[str, Any]`
  - 通过 `diskutil mountDisk` 重新挂载设备（轻量恢复）。
  - 错误码：`SUCCESS`、`RECOVERY_FAILED`

- `attempt_repartition(device_path: str, fs_type: str = "exFAT", name: str = "Untitled") -> Dict[str, Any]`
  - 通过 `diskutil eraseDisk MBR` 整盘抹除并重新分区（不可逆，调用前需用户确认）。
  - 错误码：`SUCCESS`、`RECOVERY_FAILED`

---

### log.py

统一日志入口，支持终端输出（stderr）和滚动文件输出。

公共接口：

- `setup_logging(level=INFO, log_file=None, max_bytes=5MB, backup_count=3)`
  - 程序入口处调用一次，重复调用无副作用。
  - `log_file` 为 `None` 时仅输出到终端。

- `get_logger(name: str) -> logging.Logger`
  - 各模块通过 `get_logger(__name__)` 获取 logger，无需关心底层配置。

---

### errors.py

统一错误码常量与异常类层级。

错误码常量（部分）：

| 常量 | 值 |
|------|----|
| `CODE_SUCCESS` | `"SUCCESS"` |
| `CODE_DD_FAILED` | `"DD_FAILED"` |
| `CODE_ASR_FAILED` | `"ASR_FAILED"` |
| `CODE_VERIFY_CAPACITY_FAIL` | `"VERIFY_CAPACITY_FAIL"` |
| `CODE_VERIFY_PARTITION_FAIL` | `"VERIFY_PARTITION_FAIL"` |
| `CODE_VERIFY_FILES_FAIL` | `"VERIFY_FILES_FAIL"` |
| `CODE_RECOVERY_FAILED` | `"RECOVERY_FAILED"` |

异常类层级：

```
BootooError
├── DeviceScanError
├── DeviceInvalidError
├── PermissionDeniedError
├── DeviceBusyError
├── DeviceReadOnlyError
├── ImageNotFoundError
├── ImageFormatError
├── ImageHashError
├── UnmountError
├── FormatError
├── WriteError
├── VerifyError
└── RecoveryError
```

所有异常均提供 `.to_dict()` 方法，返回 `{ok, code, message, data}` 结构。
