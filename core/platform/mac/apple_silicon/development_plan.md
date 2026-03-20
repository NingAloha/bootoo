# Apple Silicon P0 实施思路

本文档用于指导 P0 阶段的核心能力实现，目标是先打通可安全写盘的最小闭环。

## P0 目标

- 能识别并选择可写入的外置磁盘
- 能在写入前完成基本安全校验
- 能完成一次可追踪的写入流程
- 能输出清晰的错误信息与日志

## 建议目录与文件拆分

建议先按职责拆分文件，避免早期耦合过高。

- device_management/
  - device_discovery.swift: 扫描磁盘与基础信息
  - device_filter.swift: 过滤内置盘与风险盘
- image_validation/
  - image_validator.swift: 镜像合法性校验（ISO/IMG）
- write_engine/
  - write_engine.swift: 写入流程主执行器
  - write_progress.swift: 进度模型与状态事件
- privileged_execution/
  - privileged_executor.swift: 提权与命令执行封装
- shared_models/
  - core_error.swift: 统一错误码
  - core_logger.swift: 日志结构与输出
  - core_models.swift: 设备、镜像、任务状态模型

如果你暂时不想创建太多文件，也可以先只建 4 个文件：
- device_discovery.swift
- image_validator.swift
- write_engine.swift
- privileged_executor.swift

## 模块职责与边界

### 1) 设备识别与过滤
输入：系统磁盘信息
输出：可选目标磁盘列表

职责：
- 收集外置磁盘信息（路径、容量、挂载状态）
- 过滤系统盘、内置盘
- 标记风险条件（容量过小、占用中）

不要做：
- 不负责写入
- 不负责 UI 展示

### 2) 镜像校验
输入：镜像路径
输出：镜像元信息或错误

职责：
- 校验路径存在、可读
- 校验扩展名与基础格式
- 提供镜像大小供后续容量判断

不要做：
- 不负责设备选择
- 不负责权限申请

### 3) 写入引擎
输入：目标设备 + 镜像 + 执行配置
输出：任务状态（running/success/failed）

职责：
- 编排确认、卸载、写入、收尾
- 发出阶段性进度
- 在失败时返回标准错误结构

不要做：
- 不直接执行系统命令
- 不直接决定提权策略

### 4) 提权与命令执行
输入：命令与参数
输出：标准执行结果（退出码、stdout、stderr）

职责：
- 统一执行提权命令
- 支持超时、中断、错误透传
- 对上层隐藏命令细节

不要做：
- 不处理业务规则
- 不解析设备语义

## 建议数据模型（最小版）

```swift
struct BootDiskDevice {
    let id: String
    let path: String
    let name: String
    let sizeBytes: UInt64
    let isExternal: Bool
    let isSystemDisk: Bool
    let isMounted: Bool
}

struct BootImage {
    let path: String
    let format: String
    let sizeBytes: UInt64
}

enum P0Stage {
    case validating
    case unmounting
    case writing
    case finalizing
    case done
}

enum P0ErrorCode: String {
    case permissionDenied
    case deviceNotFound
    case deviceBusy
    case invalidImage
    case writeFailed
    case commandTimeout
    case unknown
}
```

## 接口草案（先统一形状）

```swift
protocol DeviceDiscovery {
    func listWritableDevices() throws -> [BootDiskDevice]
}

protocol ImageValidator {
    func validateImage(at path: String) throws -> BootImage
}

protocol PrivilegedExecutor {
    func run(_ command: String, args: [String], timeoutSeconds: Int) throws -> CommandResult
}

protocol WriteEngine {
    func write(image: BootImage,
               to device: BootDiskDevice,
               onStageChanged: (P0Stage) -> Void) throws
}
```

## 开发顺序（建议 5 天）

Day 1
- 完成设备识别与过滤
- 用日志打印可选设备列表

Day 2
- 完成镜像校验
- 接通容量检查（镜像大小 <= 设备容量）

Day 3
- 完成命令执行封装
- 支持超时、退出码、错误回传

Day 4
- 完成写入引擎基础流程
- 跑通一次完整写入

Day 5
- 补齐错误码与日志规范
- 形成一份可复现问题的测试记录

## 验收清单

- 能列出外置设备并屏蔽系统盘
- 非法镜像会被拦截
- 写入过程有阶段进度
- 失败日志可定位到具体阶段
- 至少完成 1 次成功写盘与 2 次失败场景验证

## 风险与规避

- 风险：误写系统盘
  - 规避：双重过滤 + 写入前最终确认
- 风险：权限流程不稳定
  - 规避：命令执行统一入口，细化错误码
- 风险：不同系统版本输出差异
  - 规避：解析层与业务层分离，先固定支持范围
