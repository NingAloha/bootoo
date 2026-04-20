# core/platform

`platform/` 存放不同操作系统或运行环境的底层适配器。

项目当前只支持 macOS，但从目录层面先把平台边界分出来，避免以后继续把业务逻辑和系统命令耦在一起。

## 目标职责

- 封装平台命令与系统 API
- 统一命令调用、超时、stderr/stdout 处理
- 把平台原始输出转成上层可消费的数据结构
- 把平台差异收敛在适配器层

## 当前平台

- `mac/`
  - Apple Silicon 优先
  - 负责对接 `diskutil`、`dd`、`asr`、挂载命令、plist 输出解析

## 后续扩展

未来如果支持其他平台，新增：
- `platform/linux/`
- `platform/windows/`

上层 planner / executor / domain 不应因为新增平台而发生大面积改写。
