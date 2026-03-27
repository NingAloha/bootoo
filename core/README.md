# core 文件夹结构说明

```
core/
├── api/         # API 层，接口与数据模型
├── config/      # 配置文件目录
├── mac/         # macOS 相关核心功能实现
└── README.md    # 说明文档
```

各子目录简要说明：
- api/：包含 bootoo_api.py（主接口）、contracts.py（接口约定，预留）、models.py（数据模型，预留）及说明文档。
- config/：存放 default.yaml、device_rules.yaml、image_rules.yaml 等配置文件。
- mac/：实现设备检测、磁盘操作、权限校验等 macOS 相关核心功能，并含详细说明文档。
- README.md：core 目录结构与功能说明。
