# bootoo 任务清单（按当前重构状态修订）

## 对齐结论
- 当前仓库已经从旧写盘实现切到“新架构骨架 + 占位模块”阶段，不适合再用“先补 scan/validate/write/verify 的传统写盘 MVP”作为主线。
- 当前更合理的推进顺序应是：先补 `domain -> planner -> executor -> platform/mac -> api/cli` 的最小闭环，再接真实写盘与校验能力。
- 本清单已按仓库现状修订，保留写盘目标，但把任务拆到新架构职责下。

## 当前现状
- [x] 目录骨架已建立：`cli/`、`core/api/`、`core/domain/`、`core/planner/`、`core/executor/`、`core/platform/`、`tests/`
- [x] 第一批占位文件已存在：`cli/app.py`、`core/api/bootoo_api.py`、`core/domain/*.py`、`core/planner/*.py`、`core/executor/*.py`
- [x] `core/platform/mac/*.py` 占位适配器文件已建立
- [x] 文档已明确新分层职责：见根目录与各层 `README.md`
- [x] `core/domain/device.py` 已完成第一版设备领域模型
- [x] `core/platform/mac/device_probe.py` 已实现基于 `diskutil list/info -plist` 的最小只读探测
- [x] `tests/platform/mac/test_device_probe.py` 已覆盖首批 plist 解析场景
- [ ] 各层真实类型、规则、执行逻辑仍待补齐
- [ ] CLI 命令仍是占位，尚未连通 planner / executor / platform
- [ ] `tests/mac/apple_silicon/` 仍有历史占位测试，尚未迁移到新分层测试目录

## 目标与边界
- 目标：先完成 Apple Silicon macOS 下的最小可执行闭环，再逐步补强真实写盘能力。
- 产品形态：当前以纯 CLI 为主，终端交互接近 GUI。
- 核心模型：从“直接整盘写镜像”升级为“介质方案 -> 执行计划 -> 平台执行”。
- 平台边界：当前只支持 macOS + Apple Silicon，不覆盖 Intel Mac，不做 Windows/Linux 本地客户端。

## 阶段 0：工程基线补齐
- [ ] 明确 Python 版本与依赖管理方案，并写入 `pyproject.toml`
- [ ] 梳理入口与运行方式：`bootoo.py`、`cli/app.py`、脚本入口的职责边界
- [ ] 统一日志格式与日志落点
- [ ] 统一错误码、用户提示、内部异常包装规范
- [ ] 补齐基础开发配置：格式化、lint、pytest、最小 CI

## 阶段 1：domain 落型
- [x] 在 `core/domain/device.py` 完成 `Device`、`DevicePartition`、`DeviceSnapshot`
- [x] 在 `core/domain/device.py` 补充设备总线、文件系统、分区表等基础枚举
- [ ] 在 `core/domain/artifact.py` 完成镜像资源模型、资源类型、能力描述
- [ ] 在 `core/domain/layout.py` 完成分区布局、分区规格、文件系统枚举
- [ ] 在 `core/domain/boot.py` 完成启动方案模型与模式枚举
- [ ] 在 `core/domain/plan.py` 完成 `ExecutionPlan`、`PlanStep`、上下文与风险字段
- [ ] 在 `core/domain/result.py`、`errors.py` 完成统一结果结构与领域错误
- [ ] 明确哪些字段服务于 planner / executor，避免被 CLI 展示结构反向驱动

## 阶段 2：planner 最小闭环
- [ ] 在 `request_parser.py` 把 CLI/API 输入转成 planner 请求对象
- [ ] 在 `capability_resolver.py` 识别 artifact 支持的模式与限制
- [ ] 在 `layout_planner.py` 生成 `whole-disk` / `partitioned` 两类布局结果
- [ ] 在 `boot_planner.py` 表达启动资产部署或整盘恢复方案
- [ ] 在 `validation.py` 落执行前校验：设备安全性、容量、模式兼容性、平台边界
- [ ] 在 `plan_builder.py` 输出真正可执行的 `ExecutionPlan`
- [ ] 明确 planner 输出的步骤意图、前置条件、风险等级、可选回滚点

## 阶段 3：platform/mac 适配层
- [x] 在 `device_probe.py` 中封装 `diskutil list/info` 与最小只读设备探测
- [x] 在 `device_probe.py` 中接入 APFS volume 的基础归一化处理
- [x] 在 `command_runner.py` 中统一命令执行、超时、输出、错误包装
- [ ] 用真实外置 U 盘样本继续校准 `device_probe.py` 的字段映射与候选盘判断
- [ ] 在 `disk_adapter.py` 中封装卸载、抹盘、分区、格式化
- [ ] 在 `image_adapter.py` 中封装镜像探测、文件类型与元信息读取
- [ ] 在 `restore_adapter.py` 中封装 `dd` / `asr` 的调用与进度采集
- [ ] 在 `mount_adapter.py` 中处理挂载、重新挂载、挂载点解析
- [ ] 在 `verify_adapter.py` 中处理写后只读校验
- [ ] 明确 Apple Silicon 范围内的设备识别边界，避免误判系统盘和内置盘

## 阶段 4：executor 执行链路
- [ ] 在 `engine.py` 实现执行入口与阶段状态推进
- [ ] 在 `step_runner.py` 实现统一步骤调度与上下文传递
- [ ] 在 `disk_steps.py` 实现卸载、抹盘、分区、格式化步骤
- [ ] 在 `artifact_steps.py` 实现镜像恢复、资源展开、文件复制步骤
- [ ] 在 `boot_steps.py` 实现 EFI / 启动文件部署步骤
- [ ] 在 `verify_steps.py` 实现写后校验步骤
- [ ] 在 `rollback.py` 区分可回滚和不可回滚动作，并输出修复建议
- [ ] 打通进度与状态回调：准备中、执行中、校验中、完成、失败

## 阶段 5：API 与 CLI 接线
- [ ] 在 `core/api/contracts.py`、`models.py` 定义稳定输入输出模型
- [ ] 在 `core/api/bootoo_api.py` 用 planner + executor 替换当前 skeleton 返回
- [ ] 让 `cli/app.py` 成为真实入口，不再只是打印 skeleton 文案
- [ ] 实现 `scan`、`plan`、`write`、`verify`、`doctor` 命令
- [ ] 在 `cli/presenters/` 中建立核心结果到视图模型的映射
- [ ] 在 `cli/views/` 中补终端展示组件与错误提示
- [ ] 让 `scripts/mac/*.sh` 调用正式 CLI，而不是依赖临时行为

## 阶段 6：测试与稳定性
- [ ] `tests/domain/` 覆盖领域对象约束、序列化、错误对象
- [ ] `tests/planner/` 覆盖模式选择、风险拦截、步骤生成顺序
- [ ] `tests/executor/` 覆盖执行顺序、失败停止点、回滚差异、统一结果
- [x] 在 `tests/platform/mac/` 中建立首批 `diskutil` plist 归一化测试
- [ ] 在 `tests/platform/mac/` 中继续覆盖平台适配器的命令封装与错误映射
- [ ] 迁移或清理 `tests/mac/apple_silicon/` 下的历史占位测试
- [ ] 为真实磁盘流程提供 dry-run / stub / fake adapter 测试路径
- [ ] 覆盖设备热插拔、权限不足、卸载失败、镜像不兼容等异常路径
- [ ] 在不同 macOS 版本和不同 U 盘上做最小回归验证

## 推荐实现顺序
1. 先把 `core/domain` 的核心类型补完整。
2. 再让 `planner` 能稳定生成 `ExecutionPlan`。
3. 然后补 `core/platform/mac` 的只读探测和最小破坏性适配器。
4. 再打通 `executor` 执行链路。
5. 最后接 `api`、`cli`、脚本入口和测试。

## MVP 验收标准
- 能把一个明确的 artifact + target device 请求转成可审阅的 `ExecutionPlan`
- 能在 Apple Silicon macOS 上稳定探测目标设备并防误选系统盘
- 能完成至少一种最小写盘路径的端到端执行
- 失败时能返回明确的阶段、原因和下一步建议
- 关键路径具备基础自动化测试覆盖

## 暂不作为当前主线的事项
- [ ] Intel Mac 兼容
- [ ] Windows / Linux 本地客户端
- [ ] GUI 正式产品化
- [ ] C/C++ 性能优化与底层重写
