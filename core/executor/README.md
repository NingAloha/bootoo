# core/executor

`executor/` 负责执行 planner 生成的计划。

这一层不决定“做什么盘”，只负责“按计划落实”，并把执行结果、失败位置、回滚机会记录下来。

## 目标职责

- 接收 `ExecutionPlan`
- 逐步执行 `PlanStep`
- 维护执行状态与阶段进度
- 收集中间产物
- 处理失败中止和可选回滚
- 生成统一结果

## 建议文件

- `engine.py`
  - 执行计划入口
- `step_runner.py`
  - 通用步骤调度
- `disk_steps.py`
  - 卸载、抹盘、分区、格式化等步骤
- `artifact_steps.py`
  - 镜像恢复、文件复制、资源展开
- `boot_steps.py`
  - EFI 和引导文件相关步骤
- `verify_steps.py`
  - 执行后校验步骤
- `rollback.py`
  - 失败回滚策略

## 步骤模型建议

每个步骤至少应有：
- `id`
- `kind`
- `description`
- `inputs`
- `preconditions`
- `run()`
- `rollback()`（可选）

## 设计原则

- 这一层负责执行顺序，不负责规划策略
- 步骤要尽量小，便于定位失败点
- 失败信息要带上下文，便于 API/CLI 输出
- 回滚应显式标注“可做”或“不可做”，不要假装所有动作都能回滚

## 与 platform 的关系

- `executor` 不直接拼接 shell 命令
- 所有平台相关动作通过 `platform/*` 适配器调用
