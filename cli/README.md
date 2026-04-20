# cli

纯 CLI 入口层。

目标风格：
- 终端内呈现接近 GUI 的交互体验
- 命令入口清晰
- 展示逻辑与核心执行逻辑解耦

当前入口关系：
- `bootoo.py` 负责项目级启动
- `cli/app.py` 负责 CLI 主入口
- `cli/commands/`、`cli/presenters/`、`cli/views/` 负责命令、展示适配和终端视图

建议分层：
- `app.py`：主入口
- `commands/`：命令定义
- `views/`：终端展示组件
- `presenters/`：把核心结果转成视图模型

当前状态：
- `cli/app.py` 和各命令文件仍以占位实现为主
- 后续应通过 `core/api` 接入 `planner` / `executor`，不直接在 CLI 中拼平台命令
