# bootoo

`bootoo` 正在进行底层重构。

当前仓库不再保留旧的写盘实现，现阶段以“新架构骨架 + 第一批占位模块”为主，后续会基于这套分层逐步补回可执行能力。

## 当前目标

- 纯 CLI 产品形态
- 终端交互风格接近 GUI
- 核心模型从“整盘写镜像”升级为“介质方案 -> 执行计划 -> 平台执行”

## 当前目录

```text
bootoo/
├── bootoo.py            # 项目入口，转发到 CLI
├── cli/                 # CLI 入口、命令、展示层
├── core/
│   ├── api/             # 对外接口边界
│   ├── domain/          # 领域模型
│   ├── planner/         # 方案规划
│   ├── executor/        # 计划执行
│   ├── platform/mac/    # macOS 平台适配器
│   └── config/          # 配置与规则
├── tests/               # 分层测试与历史占位测试
├── scripts/mac/         # 本地调试脚本
├── resources/           # 测试资源
└── docs/                # 架构与迁移说明
```

## 说明

- 旧实现代码已经按新骨架清空
- 旧 `core/mac` 占位目录已经移除，当前只保留新架构骨架
- `core/platform/mac/` 已创建第一批占位适配器文件，但尚未补齐真实逻辑
- 新开发应优先落在 `cli/`、`core/domain/`、`core/planner/`、`core/executor/`、`core/platform/mac/`

## 下一步

建议按这个顺序补齐最小闭环：
- [core/domain/device.py](/Users/ningaloha/Documents/Repository/bootoo/core/domain/device.py)
- [core/domain/artifact.py](/Users/ningaloha/Documents/Repository/bootoo/core/domain/artifact.py)
- [core/domain/layout.py](/Users/ningaloha/Documents/Repository/bootoo/core/domain/layout.py)
- [core/domain/plan.py](/Users/ningaloha/Documents/Repository/bootoo/core/domain/plan.py)
- [core/planner/request_parser.py](/Users/ningaloha/Documents/Repository/bootoo/core/planner/request_parser.py)
- [core/planner/plan_builder.py](/Users/ningaloha/Documents/Repository/bootoo/core/planner/plan_builder.py)
- [core/platform/mac/device_probe.py](/Users/ningaloha/Documents/Repository/bootoo/core/platform/mac/device_probe.py)
- [core/api/bootoo_api.py](/Users/ningaloha/Documents/Repository/bootoo/core/api/bootoo_api.py)
- [cli/app.py](/Users/ningaloha/Documents/Repository/bootoo/cli/app.py)
