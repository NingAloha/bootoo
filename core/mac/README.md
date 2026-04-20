# core/mac

这个目录现在只保留旧架构占位文件。

旧的 Apple Silicon 实现已经清空，不再作为开发入口。保留本目录只是为了：
- 给迁移中的 import 一个明确失败点
- 保留旧目录名，减少结构突变
- 提示能力未来应迁往 `core/platform/mac`、`core/planner`、`core/executor`

新开发不要继续写入本目录。
