# core/planner

`planner/` 负责把需求转成执行计划。

如果说 `domain` 定义了对象，那么 `planner` 负责做决策：
- 这个镜像能不能做成目标盘
- 应该走整盘模式还是分区模式
- 需要哪些步骤
- 哪些步骤存在高风险

## 目标职责

- 解析用户意图和输入约束
- 识别资源能力与限制
- 生成磁盘布局
- 生成引导方案
- 输出 `ExecutionPlan`
- 在执行前尽量发现不可行条件

## 建议文件

- `request_parser.py`
  - 把 CLI/API 输入转成 planner 级请求
- `capability_resolver.py`
  - 识别 artifact 支持哪些写入模式
- `layout_planner.py`
  - 规划分区表、分区大小、文件系统
- `boot_planner.py`
  - 规划 EFI、启动文件、镜像恢复策略
- `plan_builder.py`
  - 把布局和启动方案转成步骤序列
- `validation.py`
  - 执行前预检和规则校验

## 目标输出

planner 的输出不应该是“调用哪个 shell 命令”，而应该是：
- 一个 `ExecutionPlan`
- 每个步骤的目的
- 每个步骤的输入和前置条件
- 风险等级
- 可选回滚点

## 模式建议

优先支持两种显式模式：
- `whole-disk`
  - 镜像直接恢复到整盘
- `partitioned`
  - 先构建分区布局，再部署系统区和数据区

planner 需要决定：
- 某个 artifact 是否只允许 `whole-disk`
- 某个 artifact 是否允许 `partitioned`
- 某个设备在当前模式下是否安全

## 边界

- `planner` 不执行真实磁盘命令
- `planner` 不依赖 `subprocess`
- `planner` 可以依赖 `domain`
- `planner` 可以读取 `platform` 提供的只读探测结果，但不直接调用破坏性操作
