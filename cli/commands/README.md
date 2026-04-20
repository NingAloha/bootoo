# cli/commands

命令层骨架。

当前文件已建：
- `scan.py`
- `plan.py`
- `write.py`
- `verify.py`

后续建议至少提供：
- `scan`
- `plan`
- `write`
- `verify`
- `doctor`

约束：
- 命令层只负责参数接收、交互编排和结果呈现
- 具体规划逻辑应落在 `core/planner`
- 具体执行逻辑应落在 `core/executor`
