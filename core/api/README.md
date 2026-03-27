# /core/api 文件夹结构说明
```
/core/api/
├── bootoo_api.py
├── contracts.py
├── models.py
├── __pycache__/            # Python 缓存目录
└── README.md               # 说明文档
```
---
## 功能简介

- bootoo_api.py (API主入口)
    - 公共接口：
        - get_available_devices() -> List[Dict[str, Any]]
            - 描述：获取所有可用（可写入/非系统盘）磁盘设备信息列表。
            - 输入参数：无
            - 返回值：List[Dict[str, Any]]，每个字典包含如下字段：
                - id: 设备标识符（str），如 "disk2"
                - device: 设备路径（str），如 "/dev/disk2"
                - size_bytes: 设备容量（int，字节数）
                - internal: 是否为内置设备（bool）
                - removable: 是否为可移动设备（bool）
                - mounted: 是否已挂载（bool）
                - volumes: 设备上的卷名列表（List[str]）
                - is_system_risk: 是否为系统盘或高风险设备（bool）
        - check_selected_device_writable(device: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]
            - 描述：检查指定设备是否可写，并返回详细结果。
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
        - unmount_device(device_path: str) -> bool
            - 描述：卸载指定的磁盘设备。
            - 输入参数：
                - device_path: 设备路径（str），如"/dev/disk2"
            - 返回值：
                - bool: True 表示卸载成功，False 表示卸载失败
    - 依赖：
        - core.mac.device_detection.list_available_devices
        - core.mac.permission_guard.check_device_writable
        - core.mac.disk_ops.unmount_device

- contracts.py (接口约定)
    - 预留，暂未实现

- models.py (数据模型)
    - 预留，暂未实现
