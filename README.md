# bootoo

## 项目想法

我常常需要帮朋友或同事在 Windows、Linux 等电脑上重装系统，但发现 Mac 平台上缺乏一个真正简单易用的启动盘制作工具。像 Rufus 这样的软件在 Windows 下很方便，但在 Mac 下，制作 Windows 或其他系统的启动盘往往要用命令行、复杂分区操作，很多普通用户完全不懂怎么做，甚至容易失败。

Mac 上现有的工具（如 Etcher）对 Windows/Mac/Linux 系统盘的支持不够完善，有时写入后的U盘无法引导安装。Boot Camp 早已不支持M系列芯片的Mac，官方方案也无法满足新老设备混用需求。

我由此产生了做一个适用于 Mac 的「多系统启动盘制作小工具」的想法。希望能弥补这个实际缺口，让大家用 Mac 更轻松地制作装机盘，不管是 Windows、Linux、macOS 恢复盘还是其它操作系统，都能一键完成。

---

## 项目结构规划

本项目采用高度清晰分层的目录结构，方便未来多平台兼容与专业开发。初始结构如下图所示：

```
bootoo/
│
├── README.md
├── LICENSE
│
├── core/                   # 项目的核心逻辑，平台相关的启动盘制作等
│   ├── platform/           # 按平台再细分
│   │   ├── mac/
│   │   │   ├── apple_silicon/   # M系列芯片Mac专用代码
│   │   │   │   ├── device_detection.swift
│   │   │   │   ├── diskutil_m.swift
│   │   │   │   └── ...
│   │   │   ├── intel/     # Intel芯片Mac专用代码
│   │   │   │   ├── device_detection.swift
│   │   │   │   └── ...
│   │   │   └── common/    # Mac通用（M和Intel共用）的代码，如镜像处理、日志等
│   │   │       ├── image_utils.swift
│   │   │       ├── log.swift
│   │   │       └── ...
│   │   ├── windows/
│   │   │   ├── device_detection.py
│   │   │   └── ...
│   │   ├── linux/
│   │   │   └── ...
│   │   └── utils/         # 平台无关的工具模块
│   ├── api/               # 对外接口、核心操作说明（可做给UI或脚本调用的入口）
│   │   ├── bootoo_api.swift
│   │   └── ...
│   └── config/            # 配置文件，平台检测、写盘参数、默认镜像路径等
│       ├── mac_m1_config.yaml
│       └── ...
│
├── ui/                    # 用户界面 (GUI)，按平台/技术再分
│   ├── mac/
│   │   ├── apple_silicon/
│   │   │   ├── MainView.swift
│   │   │   └── ...
│   │   ├── intel/
│   │   │   └── ...
│   │   └── shared/        # mac共用UI组件
│   ├── windows/
│   │   └── ...
│   ├── linux/
│   │   └── ...
│   └── components/        # 可复用的UI组件
│
├── scripts/               # 辅助脚本（shell, python...）
│   ├── mac/
│   │   ├── make_boot_disk.sh
│   │   ├── diskutil_helper.sh
│   │   └── ...
│   ├── windows/
│   ├── linux/
│   └── utils/
│
├── docs/                  # 文档, 按分类详细组织
│   ├── architecture.md    # 项目整体架构说明
│   ├── install.md         # 安装与使用说明
│   ├── m_chip_guide.md    # M系列Mac的专用说明
│   ├── dev_guide.md       # 开发协作指引、接口说明
│   ├── platform_compat.md # 多平台兼容性说明
│   └── troubleshooting.md # 常见问题及解决
│
├── resources/             # 资源, 测试镜像、界面图片、图标等
│   ├── images/
│   ├── icon/
│   ├── test_iso/
│   └── ...
│
├── tests/                 # 测试用例，单测、集成测试
│   ├── mac/
│   │   ├── apple_silicon/
│   │   ├── intel/
│   │   └── shared/
│   ├── windows/
│   ├── linux/
│   └── common/
│
├── .github/               # GitHub Actions, Issue/PR模板等
│   └── workflows/
│
├── .gitignore
└── pyproject.toml / Package.swift / ... （依据开发语言自动生成的工程文件）
```

### 分层说明
- core/platform：核心按平台与芯片分层，便于扩展与维护
- ui：各平台/芯片的界面模块独立，支持未来多平台
- scripts/resources/tests/docs：辅助脚本、资源、文档、测试分门别类组织

---

> 有疑问或需要生成空目录脚本，请随时提出。