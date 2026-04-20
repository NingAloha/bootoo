# core/platform/mac

`platform/mac/` 是 macOS 平台适配层。

它负责把 Apple Silicon Mac 上的磁盘、挂载、镜像恢复等系统能力封装成稳定接口，供 `executor` 和只读探测逻辑调用。

## 目标职责

- 封装 `diskutil`
- 封装 `dd`
- 封装 `asr`
- 处理 plist 输出解析
- 处理挂载/卸载、设备信息、分区信息
- 屏蔽命令级返回差异

## 建议文件

- `device_probe.py`
  - 读取磁盘列表、分区结构、挂载状态
- `disk_adapter.py`
  - 卸载、抹盘、分区、格式化
- `image_adapter.py`
  - 镜像探测、镜像元信息
- `restore_adapter.py`
  - `dd` / `asr` 执行封装
- `mount_adapter.py`
  - 挂载、重新挂载、挂载点解析
- `verify_adapter.py`
  - 写后只读探测、分区存在性、文件存在性
- `command_runner.py`
  - 命令执行器，统一超时、输出采集、错误包装

## 当前状态

旧的 `core/mac` 占位目录已经移除。

当前目录已创建这些占位文件：
- `device_probe.py`
- `disk_adapter.py`
- `image_adapter.py`
- `restore_adapter.py`
- `mount_adapter.py`
- `verify_adapter.py`
- `command_runner.py`

当前已落的最小能力：
- `command_runner.py`
  - 提供统一命令执行结果与失败包装
- `device_probe.py`
  - 已能调用 `diskutil list -plist` 与 `diskutil info -plist`
  - 已能把 whole disk、普通 partition、APFS volume 归一化到 `core.domain.device`
  - 当前以只读探测为主，不执行任何破坏性操作

当前已确认的探测事实：
- `diskutil list -plist` 中 whole disk 可能同时包含 `Partitions` 和 `APFSVolumes`
- APFS container 上真正挂载的系统卷信息需要从 `APFSVolumes` 中读取
- `device_probe.py` 当前已据此处理系统卷和 `/System/Volumes/*` 风险挂载点

后续 macOS 相关能力直接落在这里，不再通过旧目录过渡。
