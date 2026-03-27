from typing import List, Dict, Any, Tuple
from core.mac.device_detection import list_available_devices
from core.mac.permission_guard import check_device_writable
from core.mac.disk_ops import unmount_device

def get_available_devices() -> List[Dict[str, Any]]:
    return list_available_devices()

def check_selected_device_writable(device: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    return check_device_writable(device)

if __name__ == "__main__":
    devices = get_available_devices()
    print("可用设备:")
    for idx, device in enumerate(devices):
        print(f"{idx}: {device}")

    if devices:
        choice = input("请选择设备编号: ")
        try:
            idx = int(choice)
            selected_device = devices[idx]
        except (ValueError, IndexError):
            print("无效选择")
            exit(1)


        device_path = selected_device.get('device')
        if not device_path:
            print("无法获取设备路径")
            exit(1)

        unmount_result = unmount_device(device_path)
        print(f"解除挂载结果: {unmount_result}")

        writable, info = check_selected_device_writable(selected_device)
        print(f"设备可写: {writable}")
        if not writable:
            print(f"原因: {info.get('reason', 'Unknown')}")