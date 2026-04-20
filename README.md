# bootoo

`bootoo` 正在进行底层重构。

当前仓库不再保留旧的写盘实现，现阶段只保留新的项目骨架、目录职责说明和占位模块，后续会基于这套骨架逐步补回能力。

## 当前目标

- 纯 CLI 产品形态
- 终端交互风格接近 GUI
- 核心模型从“整盘写镜像”升级为“介质方案 -> 执行计划 -> 平台执行”

## 当前目录

```text
bootoo/
├── cli/                 # CLI 入口、命令、展示层
├── core/
│   ├── api/             # 对外接口边界
│   ├── domain/          # 领域模型
│   ├── planner/         # 方案规划
│   ├── executor/        # 计划执行
│   ├── platform/mac/    # macOS 平台适配器
│   ├── mac/             # 已清空的旧实现占位区
│   └── config/          # 配置骨架
├── tests/               # 分层测试骨架
└── docs/                # 架构与迁移说明
```

## 说明

- 旧实现代码已经按新骨架清空
- 旧 `core/mac` 目录暂时保留，只作为兼容占位与迁移提示
- 新开发应优先落在 `cli/`、`core/domain/`、`core/planner/`、`core/executor/`、`core/platform/mac/`

## 下一步

建议先从这些文件开始正式落类型：
- [core/domain/device.py](/Users/ningaloha/.codex/worktrees/44bb/bootoo/core/domain/device.py)
- [core/domain/artifact.py](/Users/ningaloha/.codex/worktrees/44bb/bootoo/core/domain/artifact.py)
- [core/domain/layout.py](/Users/ningaloha/.codex/worktrees/44bb/bootoo/core/domain/layout.py)
- [core/domain/plan.py](/Users/ningaloha/.codex/worktrees/44bb/bootoo/core/domain/plan.py)
- [cli/app.py](/Users/ningaloha/.codex/worktrees/44bb/bootoo/cli/app.py)
