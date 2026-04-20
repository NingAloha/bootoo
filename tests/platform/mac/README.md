# tests/platform/mac

放 `core/platform/mac` 的测试。

重点覆盖：
- `diskutil` 命令参数映射
- plist 输出解析
- `dd` / `asr` 输出解析
- 分区和挂载信息的边界情况

当前进展：
- 已新增 `test_device_probe.py`
- 当前测试覆盖：
  - whole disk + 普通分区的 `diskutil` plist 归一化
  - 内置系统盘的基础风险判定
  - APFS container 下 `APFSVolumes` 的挂载信息归一化

后续建议继续补：
- 外置 U 盘真实样本的字段映射测试
- `diskutil info -plist` 中外置盘 `Removable` / `Ejectable` / `VirtualOrPhysical` 的边界测试
- 失败输出与非法 plist 的异常路径测试
