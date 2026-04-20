# core 架构说明

`core/` 已建立新架构骨架，并落了第一批占位模块：
- `core/api`
- `core/domain`
- `core/planner`
- `core/executor`
- `core/platform`

## 目标分层

```
core/
├── api/             # 对外接口层，负责组装输入/输出，不直接承载底层业务
├── domain/          # 领域模型与通用约束
├── planner/         # 方案规划与校验
├── executor/        # 执行计划与步骤执行
├── platform/
│   └── mac/         # 平台适配器，封装 diskutil/dd/asr 等命令
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

## 迁移策略

1. 先在新目录下写清抽象和接口边界
2. 再把平台能力补进 `platform/mac` 和 `executor`
3. 最后让 `api` 改为调用 planner/executor

## 当前状态

- 当前目录用于承载重构后的底层设计
- `domain`、`planner`、`executor`、`api`、`platform/mac` 已有占位 Python 文件
- 平台适配器文件名已经稳定，但内部逻辑仍待补齐
- 旧实现占位层已经移除，避免继续产生并行结构错觉
