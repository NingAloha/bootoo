# bootoo 目录重画方案

这份文档现在只保留“目录迁移视图”，详细职责都下沉到对应目录的 `README.md`。

## 新目标结构

```
bootoo/
├── core/
│   ├── api/
│   ├── domain/
│   ├── planner/
│   ├── executor/
│   ├── platform/
│   │   └── mac/
│   ├── mac/
│   └── config/
├── tests/
│   ├── domain/
│   ├── planner/
│   ├── executor/
│   ├── platform/mac/
│   └── mac/apple_silicon/
├── scripts/mac/
├── resources/
└── docs/
```

## 阅读顺序

先看这些 README：
- `core/README.md`
- `core/domain/README.md`
- `core/planner/README.md`
- `core/executor/README.md`
- `core/platform/README.md`
- `core/platform/mac/README.md`
- `tests/README.md`

## 迁移原则

1. 旧 `core/mac` 继续可用，不一次性删除
2. 新功能优先写入新架构目录
3. 平台命令实现逐步下沉到 `core/platform/mac`
4. CLI/API 最终改为依赖 planner/executor

## 下一阶段建议

1. 先在 `core/domain` 中落第一批类型
2. 再定义 `planner` 请求和 `ExecutionPlan`
3. 然后把旧 `device_detection` 的只读能力迁到 `platform/mac`
