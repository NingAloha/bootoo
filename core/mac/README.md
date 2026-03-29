## mac 文件夹结构说明
```
/core/mac/
├── device_detection.py
├── disk_ops.py
├── errors.py
├── image_utils.py
├── log.py
├── permission_guard.py
├── recovery.py
├── verify.py
├── write_engine.py
├── commands/               # 预留的命令相关子目录（当前为空）
├── __pycache__/            # Python 缓存目录
└── README.md               # 说明文档
```
---
## 功能简介

- device_detection.py (设备检测)
    - 私有函数：
        - _scan_devices() -> List[Dict[str, Any]]
            - 描述：扫描本机所有磁盘设备，返回设备信息列表。
            - 输入参数：无
            - 返回值：List[Dict[str, Any]]，每个字典包含如下字段：
                - id: 设备标识符（str）
                - device: 设备路径（str，如"/dev/disk2"）
                - size_bytes: 设备容量（int，字节数）
                - internal: 是否为内置设备（bool）
                - removable: 是否为可移动设备（bool）
                - mounted: 是否已挂载（bool）
                - volumes: 设备上的卷名列表（List[str]）
                - is_system_risk: 是否为系统盘或高风险设备（bool）
        - _validate_target(device: Dict[str, Any]) -> bool
            - 描述：校验设备是否为可用目标盘。
            - 输入参数：device，单个设备信息字典（同上）
            - 返回值：bool，True 表示可用，False 表示不可用
    - 公共接口：
        - list_all_devices() -> List[Dict[str, Any]]
            - 描述：获取所有磁盘设备信息列表。
            - 输入参数：无
            - 返回值：List[Dict[str, Any]]，结构同 _scan_devices
        - list_available_devices() -> List[Dict[str, Any]]
            - 描述：获取所有可用（可写入/非系统盘）磁盘设备信息列表。
            - 输入参数：无
            - 返回值：List[Dict[str, Any]]，结构同 _scan_devices
    
- disk_ops.py (磁盘操作)
     - 公共接口：
         - unmount_device(device_path: str) -> bool
             - 描述：卸载指定的磁盘设备。
             - 输入参数：
                 - device_path: 设备路径（str），如"/dev/disk2"
             - 返回值：
                 - bool: True 表示卸载成功，False 表示卸载失败 
- errors.py(错误定义与处理)
    - 预留，暂未实现
- image_utils.py (镜像处理)
    - 私有函数：
        - _check_image_exists(path: str) -> bool
            - 描述：检查镜像文件是否存在。
            - 输入参数：
                - path: 镜像文件路径（str）
            - 返回值：
                - bool: True 表示存在，False 表示不存在
        - _get_image_format(path: str) -> str
            - 描述：识别镜像文件格式（基于扩展名）。
            - 输入参数：
                - path: 镜像文件路径（str）
            - 返回值：
                - str: 格式字符串，如 'dmg', 'iso', 'img'，未知返回 'unknown'
        - _calc_sha256(path: str) -> Optional[str]
            - 描述：计算镜像文件的 SHA256 值。
            - 输入参数：
                - path: 镜像文件路径（str）
            - 返回值：
                - str: sha256 字符串，文件不存在时返回 None
    - 公共接口：
        - check_image(path: str) -> Dict[str, Any]
            - 描述：检查镜像文件的存在性、格式和 SHA256，返回统一结构。
            - 输入参数：
                - path: 镜像文件路径（str）
            - 返回值：
                - Dict[str, Any]:
                    - ok: 是否检查通过（bool）
                    - code: 状态码（str），如 'SUCCESS'、'IMAGE_NOT_FOUND'
                    - message: 说明信息（str）
                    - data: 详细信息（dict，包含 path/format/sha256，失败时为 None）
- log.py(日志)
    - 预留，暂未实现
- permission_guard.py (权限校验)
    - 私有函数：
        - _check_writable(dev_path: str) -> Tuple[bool, str]
            - 描述：检查指定设备路径是否可写。
            - 输入参数：
                - dev_path: 设备路径（str），如"/dev/disk2"
            - 返回值：
                - Tuple[bool, str]
                    - bool: True 表示可写，False 表示不可写
                    - str: 不可写时的原因说明（如权限不足、设备被占用等）
    - 公共接口：
        - check_device_writable(device: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]
            - 描述：检查设备是否可写，并返回详细结果。
            - 输入参数：
                - device: 设备信息字典，需包含至少 device（路径）和 id 字段
            - 返回值：
                - Tuple[bool, Dict[str, Any]]
                    - bool: True 表示可写，False 表示不可写
                    - Dict[str, Any]: 结果详情，字段包括：
                        - id: 设备标识符（str）
                        - device: 设备路径（str）
                        - writable: 是否可写（bool）
                        - info: 说明信息（str）
- recovery.py(恢复相关)
    - 预留，暂未实现
- verify.py(校验相关)
    - 预留，暂未实现
- write_engine.py(写入引擎)
    - 预留，暂未实现