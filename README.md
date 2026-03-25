# bootoo

## 项目想法

我常常需要帮朋友或同事在 Windows、Linux 等电脑上重装系统，但发现 Mac 平台上缺乏一个真正简单易用的启动盘制作工具。像 Rufus 这样的软件在 Windows 下很方便，但在 Mac 下，制作 Windows 或其他系统的启动盘往往要用命令行、复杂分区操作，很多普通用户完全不懂怎么做，甚至容易失败。

Mac 上现有的工具（如 Etcher）对 Windows/Mac/Linux 系统盘的支持不够完善，有时写入后的U盘无法引导安装。Boot Camp 早已不支持M系列芯片的Mac，官方方案也无法满足新老设备混用需求。

我由此产生了做一个适用于 M 芯片 Mac 的「启动盘制作小工具」的想法。项目将专注在 Apple Silicon 设备上，把检测、写盘流程、引导兼容、错误恢复都做到更稳定、更易用，不再分散到其它平台。

---

## 项目结构规划

本项目采用清晰的单平台分层结构，专注 M 芯片 Mac 的开发与迭代。初始结构如下图所示：

```
bootoo/
│
├── README.md
├── LICENSE
│
├── core/                   # 项目的核心逻辑（仅 M 芯片 Mac）
│   ├── mac/                # Apple Silicon 平台核心实现
│   │   ├── device_detection.swift   # 设备与系统环境检测
│   │   ├── diskutil_m.swift         # 磁盘识别、分区、格式化与写入
│   │   ├── image_utils.swift        # 镜像校验、挂载、转换等
│   │   ├── boot_prep.swift          # 引导文件准备与兼容处理
│   │   └── log.swift                # 日志与错误追踪
│   ├── api/               # 对外接口、核心操作说明（可做给 UI 或脚本调用的入口）
│   │   ├── bootoo_api.swift
│   │   └── ...
│   └── config/            # 配置文件：写盘参数、默认镜像路径、重试策略等
│       ├── mac_m1_config.yaml
│       └── ...
│
├── ui/                    # 用户界面 (GUI)，仅面向 Apple Silicon Mac
│   ├── mac/
│   │   ├── MainView.swift
│   │   ├── WriteFlowView.swift
│   │   └── ...
│   └── components/        # 可复用 UI 组件
│
├── scripts/               # 辅助脚本（shell, python...）
│   ├── mac/
│   │   ├── make_boot_disk.sh
│   │   ├── diskutil_helper.sh
│   │   └── ...
│   └── utils/
│
├── docs/                  # 文档, 按分类详细组织
│   ├── architecture.md    # 项目整体架构说明
│   ├── install.md         # 安装与使用说明
│   ├── m_chip_guide.md    # M 系列 Mac 专用说明
│   ├── dev_guide.md       # 开发协作指引、接口说明
│   ├── platform_compat.md # M 系列机型与系统版本兼容性说明
│   └── troubleshooting.md # 常见问题及解决
│
├── resources/             # 资源, 测试镜像、界面图片、图标等
│   ├── images/
│   ├── icon/
│   ├── test_iso/
│   └── ...
│
├── tests/                 # 测试用例（单测、集成测试）
│   ├── mac/
│   │   ├── apple_silicon/
│   │   └── shared/
│   └── common/
│
├── .github/               # GitHub Actions, Issue/PR模板等
│   └── workflows/
│
├── .gitignore
└── pyproject.toml / Package.swift / ... （依据开发语言自动生成的工程文件）
```

### 分层说明
- core/mac：聚焦 M 芯片 Mac 的核心流程，优先保证稳定性与可维护性
- ui/mac：围绕单平台使用场景设计，减少多平台分支复杂度
- scripts/resources/tests/docs：辅助脚本、资源、文档、测试分门别类组织

### 当前范围（Scope）
- 仅支持 M 系列芯片（Apple Silicon）Mac
- 不包含 Intel Mac 支持
- 不包含 Windows/Linux 本地运行版本

---

> 有疑问或需要生成空目录脚本，请随时提出。

---

## 多语言集成与分支说明

本项目采用多语言协作架构，核心功能以 Python 为主，底层性能或系统相关模块可用 C/C++/Swift 实现，并通过统一的 API 层（如 Python CFFI、ctypes、Swift-Python bridge 等）进行集成。各语言模块需保证接口清晰、调用安全，便于后续扩展和跨语言复用。

当前分支（Apple Silicon Mac 版）由 **NingAloha** 全权负责，专注于 M 系列芯片 Mac 的启动盘制作与相关功能。

后续可能会有其他平台（如 amd64 Windows 版）分支，由其他开发者主导，届时会在项目主页和文档中明确标注负责人及适用平台。

如需协作、贡献新平台支持或有多语言集成相关建议，欢迎通过 Issue 或 PR 交流。