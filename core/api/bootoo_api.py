from typing import List, Dict, Any, Tuple
from core.mac.device_detection import list_available_devices
from core.mac.permission_guard import check_device_writable
from core.mac.disk_ops import unmount_device

def get_available_devices() -> List[Dict[str, Any]]:
    """
    获取所有可用（可写入/非系统盘）磁盘设备信息列表。
    输入参数：无
    返回值：List[Dict[str, Any]]，每个字典结构见 device_detection.py
    """
    return list_available_devices()

def check_selected_device_writable(device: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    检查指定设备是否可写，并返回详细结果。
    输入参数：
        - device: 设备信息字典，需包含 device（路径）和 id 字段
    返回值：
        - Tuple[bool, Dict[str, Any]]
            - bool: True 表示可写，False 表示不可写
            - Dict[str, Any]: 结果详情，字段包括 id/device/writable/info
    """
    return check_device_writable(device)

if __name__ == "__main__":
    # 获取所有可用设备
    devices = get_available_devices()
    print("可用设备:")
    for idx, device in enumerate(devices):
        print(f"{idx}: {device}")

    if devices:
        # 用户选择设备编号
        choice = input("请选择设备编号: ")
        try:
            idx = int(choice)
            selected_device = devices[idx]
        except (ValueError, IndexError):
            print("无效选择")
            exit(1)

        # 获取设备路径
        device_path = selected_device.get('device')
        if not device_path:
            print("无法获取设备路径")
            exit(1)

        # 尝试解除挂载
        unmount_result = unmount_device(device_path)
        print(f"解除挂载结果: {unmount_result}")

        # 检查设备可写性
        writable, info = check_selected_device_writable(selected_device)
        print(f"设备可写: {writable}")
        if not writable:
            print(f"原因: {info.get('reason', 'Unknown')}")