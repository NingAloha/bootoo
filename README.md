
# bootoo (amd64_win 分支)

## 项目简介

bootoo 致力于为 Windows (amd64) 平台用户提供一站式、简单高效的启动盘制作体验。参考 Rufus、Ventoy 等工具，结合自身创新，支持多种系统镜像写入、U盘/移动硬盘识别、分区与格式化、引导修复等功能。

本分支专注于 Windows (amd64) 版本，由 **Edison0825** 全权负责。后续如有其他平台（如 Mac/ARM、Linux）需求，将以独立分支维护。

---

## 项目结构规划

本分支采用面向 Windows 平台的分层结构，兼顾易用性、可维护性与扩展性：

```
bootoo/
│
├── README.md
├── LICENSE
│
├── core/                   # 核心逻辑（仅 Windows amd64）
│   ├── win/                # Windows 平台核心实现
│   │   ├── device_detection.cpp   # 设备与系统环境检测（C++/WinAPI）
│   │   ├── diskutil_win.cpp       # 磁盘识别、分区、格式化与写入
│   │   ├── image_utils.cpp        # 镜像校验、挂载、转换等
│   │   ├── boot_prep.cpp          # 引导文件准备与兼容处理
│   │   └── log.cpp                # 日志与错误追踪
│   ├── api/               # 对外接口（C++/Python/C#等，供 UI 或脚本调用）
│   │   ├── bootoo_api.cpp
│   │   └── ...
│   └── config/            # 配置文件：写盘参数、默认镜像路径、重试策略等
│       ├── win_config.yaml
│       └── ...
│
├── ui/                    # 用户界面 (GUI)，仅面向 Windows
│   ├── winforms/          # C# WinForms/WPF 实现
│   ├── qt/                # Qt/C++ 实现（可选）
│   └── components/        # 可复用 UI 组件
│
├── scripts/               # 辅助脚本（bat, powershell, python...）
│   ├── win/
│   │   ├── make_boot_disk.bat
│   │   ├── diskutil_helper.ps1
│   │   └── ...
│   └── utils/
│
├── docs/                  # 文档, 按分类详细组织
│   ├── architecture.md    # 项目整体架构说明
│   ├── install.md         # 安装与使用说明
│   ├── win_guide.md       # Windows 平台专用说明
│   ├── dev_guide.md       # 开发协作指引、接口说明
│   ├── platform_compat.md # 机型与系统版本兼容性说明
│   └── troubleshooting.md # 常见问题及解决
│
├── resources/             # 资源, 测试镜像、界面图片、图标等
│   ├── images/
│   ├── icon/
│   ├── test_iso/
│   └── ...
│
├── tests/                 # 测试用例（单测、集成测试）
│   ├── win/
│   │   └── shared/
│   └── common/
│
├── .github/               # GitHub Actions, Issue/PR模板等
│   └── workflows/
│
├── .gitignore
└── CMakeLists.txt / win_bootoo.sln / ... （依据开发语言自动生成的工程文件）
```

### 分层说明
- core/win：聚焦 Windows 平台核心流程，优先保证兼容性与稳定性
- ui/winforms/qt：多种 Windows GUI 技术可选，提升用户体验
- scripts/resources/tests/docs：辅助脚本、资源、文档、测试分门别类组织

### 当前范围（Scope）
- 仅支持 Windows 10/11 (amd64) 及主流 UEFI 机型
- 不包含 ARM/ARM64、Mac、Linux 支持

---

## 多语言集成与分支说明

本项目支持多语言协作，核心以 C++ 实现，部分功能可用 Python/C# 扩展，通过统一 API 层（如 C++/CLI、Python ctypes、C# P/Invoke 等）集成。各语言模块需保证接口清晰、调用安全，便于后续扩展和跨语言复用。

本分支（Windows amd64 版）由 **Edison0825** 全权负责，专注于 Windows 平台的启动盘制作与相关功能。

如需协作、贡献新平台支持或有多语言集成相关建议，欢迎通过 Issue 或 PR 交流。