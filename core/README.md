# core 架构说明

`core/` 现在分成两套并行结构：
- 旧实现区：`core/mac`，当前 CLI 直接调用，保留并逐步迁移
- 新架构区：`core/domain`、`core/planner`、`core/executor`、`core/platform`

## 目标分层

```
core/
├── api/             # 对外接口层，负责组装输入/输出，不直接承载底层业务
├── domain/          # 领域模型与通用约束
├── planner/         # 方案规划与校验
├── executor/        # 执行计划与步骤执行
├── platform/
│   └── mac/         # 平台适配器，封装 diskutil/dd/asr 等命令
├── mac/             # 旧版 Apple Silicon 实现，作为迁移来源
├── config/          # 配置和规则
└── README.md
```

## 每层职责

### `api/`
- 负责 CLI / GUI / 自动化调用入口
- 只处理参数整形、结果包装、错误映射
- 不直接写 `subprocess` 或平台命令

### `domain/`
- 定义核心对象：设备、镜像资源、分区方案、启动方案、执行计划
- 定义跨平台都成立的约束和状态
- 不依赖 macOS 命令细节

### `planner/`
- 把“用户要什么盘”转成“系统该怎么做”
- 负责模式选择：`whole-disk`、`partitioned`
- 负责兼容性判断、风险校验、步骤生成

### `executor/`
- 接收 planner 产出的计划
- 逐步执行并记录状态
- 负责失败中止、结果采集、可选回滚

### `platform/mac/`
- 封装所有 macOS 相关实现
- 例如 `diskutil`、`dd`、`asr`、挂载/卸载、plist 解析
- 为上层提供稳定适配器，不暴露命令细节

### `mac/`
- 当前可运行实现所在目录
- 新架构未落完前，CLI 仍依赖这里
- 后续按能力逐步迁移，不一次性删除

## 迁移策略

1. 先在新目录下写清抽象和接口边界
2. 再把旧 `core/mac` 的能力下沉到 `platform/mac` 和 `executor`
3. 最后让 `api` 改为调用 planner/executor，而不是直连旧函数

## 当前状态

- 新目录：用于承载重构后的底层设计
- 旧目录：仍是当前主工作实现
- 两套结构短期内并存，这是刻意设计，不是重复
