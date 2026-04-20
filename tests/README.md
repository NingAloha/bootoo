# tests

测试目录以新架构测试骨架为主。

当前应重点围绕这些目录重建：
- `domain/`
- `planner/`
- `executor/`
- `platform/mac/`

补充说明：
- `tests/mac/apple_silicon/` 仍保留一个历史占位测试文件，用于提示旧实现测试尚未迁移完成
- 新测试应优先进入分层目录，而不是继续扩写旧路径
