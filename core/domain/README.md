# core/domain

`domain/` 存放项目最底层、最稳定的业务模型。

这里不关心 macOS、`diskutil`、`dd`、`asr`，只关心系统在描述什么对象、它们之间有什么约束。

## 目标职责

- 定义设备模型
- 定义镜像/介质资源模型
- 定义分区布局模型
- 定义启动方案模型
- 定义执行计划模型
- 定义通用错误与状态枚举

## 建议文件

- `device.py`
  - `Device`
  - `DevicePartition`
  - `DeviceSnapshot`
  - `DeviceBusKind`
  - `FilesystemKind`
  - `PartitionTableKind`
- `artifact.py`
  - `ImageArtifact`
  - `ArtifactKind`
  - `ArtifactCapabilities`
- `layout.py`
  - `PartitionLayout`
  - `PartitionSpec`
  - `FilesystemKind`
- `boot.py`
  - `BootPlan`
  - `BootMode`
  - `BootAsset`
- `plan.py`
  - `ExecutionPlan`
  - `PlanStep`
  - `PlanContext`
- `result.py`
  - 统一结果结构和步骤结果
- `errors.py`
  - 领域级错误，不带平台命令细节

## 设计原则

- 这里定义“是什么”，不定义“怎么做”
- 类型应该稳定，尽量少依赖外部命令输出结构
- 字段要服务于 planner 和 executor，不服务于某个 CLI 展示

## 当前进展

- `device.py` 已完成第一版最小设备模型
- 当前设备模型已覆盖：
  - 设备总线类型
  - 分区表类型
  - 文件系统类型
  - 内置 / 外置 / 虚拟 / 只读 / 系统高风险等基础语义
  - 设备快照与分区挂载状态
- 这套模型当前主要服务于 `core/platform/mac/device_probe.py` 的 `diskutil` 输出归一化
- 下一步应继续补 `artifact.py`、`plan.py`，避免 planner 重新退回裸 dict

## 例子

系统不应该直接问“要不要跑 `dd`”，而应该先表达：
- 输入资源是不是整盘镜像
- 目标设备是否允许破坏性改写
- 目标布局是整盘占用还是系统区 + 数据区
- 引导能力来自镜像恢复还是文件部署

这些都属于 `domain`。
