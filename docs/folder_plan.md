# bootoo 目录重画方案

这份文档现在只保留“目录迁移视图”，详细职责都下沉到对应目录的 `README.md`。

## 新目标结构

```
bootoo/
├── bootoo.py
├── cli/
├── core/
│   ├── api/
│   ├── domain/
│   ├── planner/
│   ├── executor/
│   ├── platform/
│   │   └── mac/
│   └── config/
├── tests/
│   ├── domain/
│   ├── planner/
│   ├── executor/
│   ├── platform/mac/
│   └── mac/apple_silicon/   # 历史占位测试，后续应迁移或清理
├── scripts/mac/
├── resources/
└── docs/
```

## 阅读顺序

先看这些 README：
- `README.md`
- `cli/README.md`
- `core/README.md`
- `core/api/README.md`
- `core/domain/README.md`
- `core/planner/README.md`
- `core/executor/README.md`
- `core/platform/README.md`
- `core/platform/mac/README.md`
- `tests/README.md`

## 迁移原则

1. 新功能优先写入新架构目录
2. 平台命令实现直接落在 `core/platform/mac`
3. CLI/API 最终改为依赖 planner/executor
4. 历史残留路径只做归档或迁移，不再继续扩展

## 下一阶段建议

1. 先在 `core/domain` 中落第一批类型
2. 再定义 `planner` 请求和 `ExecutionPlan`
3. 然后在 `platform/mac` 中补齐只读探测与执行适配能力
4. 最后把 `api`、`cli`、测试目录和脚本入口统一接到新闭环
