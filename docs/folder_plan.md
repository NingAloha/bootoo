# bootoo 文件夹详细方案（先 core）

## 总览
本方案针对当前目录结构给出可直接落地的职责划分与文件级建议，优先保障 `core` 的可实施性。

## core（优先开发）

### core/mac
职责：M 芯片 Mac 的核心写盘能力，包含检测、校验、执行、恢复。当前分支仅支持 Apple Silicon，后续如需适配 Intel Mac/其他平台需单独开发。
  功能：统一错误类型和错误码。建议所有磁盘操作异常、权限不足、卸载失败等都在此集中处理。

建议文件：
- `core/mac/device_detection.py`
  - 功能：枚举外置磁盘、识别设备路径、容量、文件系统、可写状态。
  - 输入：无或筛选参数。
  - 输出：标准化设备列表（list[dict]）。
- `core/mac/permission_guard.py`
  - 功能：检查是否具备执行关键磁盘命令的权限。
  - 输出：布尔值 + 诊断信息。
- `core/mac/image_utils.py`
  - 功能：镜像存在性检查、格式识别、可选 hash 校验。
- `core/mac/disk_ops.py`
  - 功能：封装 `diskutil` 相关操作（卸载、抹盘、格式化、信息查询）。
- `core/mac/write_engine.py`
  - 功能：封装写入引擎（`dd`/`asr`），提供进度回调。
- `core/mac/verify.py`
  - 功能：写后校验（容量、引导分区存在、必要文件存在）。
- `core/mac/recovery.py`
  - 功能：失败回滚和修复建议（重新分区、重新挂载）。
- `core/mac/log.py`
  - 功能：统一日志入口，支持文件输出与终端输出。
- `core/mac/errors.py`
  - 功能：统一错误类型和错误码。

建议子目录：
- `core/mac/commands/`
  - 用于集中管理命令构造与执行器，避免散落 `subprocess` 调用。

核心流程：
1. 设备扫描与筛选
2. 权限和环境检查
3. 镜像校验
4. 卸载与抹盘
5. 执行写入
6. 写后校验
7. 成功收尾或失败恢复

注意：
- 设备检测能力已覆盖主流 Apple Silicon Mac 场景，极端/特殊硬件后续遇到再补充。
- 设备状态变化（如热插拔）需在写盘前后再次校验。
- 权限建议在运行时即要求 sudo/root，避免写盘阶段权限不足。
- 错误与异常建议全部在 errors.py 统一处理，便于维护。

### core/api
职责：给 CLI/UI 的稳定调用边界，避免上层直接依赖底层细节。

建议文件：
- `core/api/bootoo_api.py`
  - 对外方法：`scan_devices()`、`validate_target()`、`write_image()`、`verify_result()`。
- `core/api/models.py`
  - 定义请求/响应数据结构（可用 dataclass/pydantic）。
- `core/api/contracts.py`
  - 定义进度回调协议与错误协议。

接口设计建议：
- 所有接口返回统一结构：`{ok, code, message, data}`。
- 进度统一为 0-100 整数，且附带阶段名。

### core/config
职责：运行配置、默认参数、策略开关。

建议文件：
- `core/config/default.yaml`
  - 默认块大小、重试次数、超时、日志级别。
- `core/config/device_rules.yaml`
  - 设备过滤规则（最小容量、黑名单路径等）。
- `core/config/image_rules.yaml`
  - 镜像类型白名单、校验策略。

配置原则：
- 配置可覆盖，但默认值必须可直接运行。
- 风险配置需有保护（例如禁止默认覆盖系统盘）。

## ui

### ui/mac
职责：仅负责交互与展示，不直接执行磁盘命令。

建议文件：
- `ui/mac/MainView`：设备选择、镜像选择、开始按钮。
- `ui/mac/WriteFlowView`：展示阶段进度与日志。
- `ui/mac/ResultView`：结果页与失败恢复建议。

### ui/components
职责：可复用组件（进度条、状态徽标、日志面板、确认弹窗）。

## scripts

### scripts/mac
职责：开发期和手动运维入口。

建议文件：
- `scripts/mac/dev_scan.sh`：快速扫描磁盘。
- `scripts/mac/dev_write.sh`：本地写盘调试入口。
- `scripts/mac/dev_verify.sh`：写后校验入口。

### scripts/utils
职责：通用脚本（日志收集、环境检查、格式化等）。

## docs
职责：保持架构、开发流程、兼容性和故障排查文档同步。

建议优先补齐：
- `docs/architecture.md`
- `docs/dev_guide.md`
- `docs/troubleshooting.md`

## resources
职责：放测试镜像、图标和文档素材。

建议：
- `resources/test_iso` 仅放测试用途镜像，禁止提交大文件到 Git（可配 LFS 或下载脚本）。

## tests

### tests/mac/apple_silicon
职责：核心流程集成测试和回归测试。

建议测试点：
- 识别正确设备
- 拒绝系统盘
- 写入失败时可恢复
- 中断后可重试

### tests/mac/shared
职责：mac 共用工具测试，如命令执行器、日志和错误映射。

### tests/common
职责：跨模块通用测试工具和 mock 数据。

## 建议的 core 启动任务（今天可开工）
1. 先创建 `device_detection.py`、`image_utils.py`、`errors.py`。
2. 实现 `scan_devices()` 与 `validate_target()` 两个最小可用接口。
3. 添加 6-10 个单测，覆盖正常路径和高风险失败路径。
4. 再进入 `write_engine.py` 的写盘主流程。
