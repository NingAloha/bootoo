from typing import List, Dict, Any, Tuple
from core.mac.device_detection import list_available_devices
from core.mac.permission_guard import check_device_writable
import core.mac.disk_ops as disk_ops
from core.mac.image_utils import check_image

def check_image_file(path: str) -> Dict[str, Any]:
    """
    检查镜像文件的存在性、格式和 SHA256。
    输入参数：
        - path: 镜像文件路径（str）
    返回值：
        - Dict[str, Any]:
            - ok: 是否检查通过（bool）
            - code: 状态码（str），如 'SUCCESS'、'IMAGE_NOT_FOUND'
            - message: 说明信息（str）
            - data: 详细信息（dict，包含 path/format/sha256，失败时为 None）
    """
    return check_image(path)

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

# === 磁盘操作相关接口（直接转发 disk_ops） ===
def unmount_device(device_path: str) -> Dict[str, Any]:
    """
    卸载指定的磁盘或分区。
    输入参数：
        - device_path: 设备或分区路径（str），如"/dev/disk2" 或 "/dev/disk2s1"
    返回值：
        - Dict[str, Any]:
            - ok: 是否卸载成功（bool）
            - code: 状态码（str），如 'SUCCESS'、'UNMOUNT_FAILED'
            - message: 说明信息（str）
            - data: 详细信息（dict，包含 device_path，失败时为 None）
    """
    return disk_ops.unmount_device(device_path)

def format_disk(partition_path: str, fs_type: str = "exFAT", name: str = "Untitled") -> Dict[str, Any]:
    """
    格式化指定分区。
    输入参数：
        - partition_path: 分区路径（str），如"/dev/disk2s1"
        - fs_type: 文件系统类型（str），如"exFAT"、"APFS"，默认"exFAT"
        - name: 卷标名（str），默认"Untitled"
    返回值：
        - Dict[str, Any]:
            - ok: 是否格式化成功（bool）
            - code: 状态码（str），如 'SUCCESS'、'FORMAT_FAILED'
            - message: 说明信息（str）
            - data: 详细信息（dict，包含 partition_path, fs_type, name，失败时为 None）
    """
    return disk_ops.format_disk(partition_path, fs_type, name)

def get_disk_info(path: str) -> Dict[str, Any]:
    """
    查询磁盘或分区信息。
    输入参数：
        - path: 设备或分区路径（str），如"/dev/disk2" 或 "/dev/disk2s1"
    返回值：
        - Dict[str, Any]:
            - ok: 是否查询成功（bool）
            - code: 状态码（str），如 'SUCCESS'、'INFO_FAILED'
            - message: 说明信息（str）
            - data: 详细信息（dict，查询到的信息，失败时为 None）
    """
    return disk_ops.get_disk_info(path)

if __name__ == "__main__":
    # 获取所有可用设备
    devices = get_available_devices()
    print("可用设备:")
    for idx, device in enumerate(devices):
        print(f"  [{idx}] 设备: {device.get('device', '-')}, 容量: {device.get('size_bytes', 0) // (1024**3)}GB, 卷: {device.get('volumes', [])}")

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
        print("\n--- 卸载磁盘 ---")
        unmount_result = unmount_device(device_path)
        print(f"  状态: {'成功' if unmount_result['ok'] else '失败'}")
        print(f"  信息: {unmount_result['message']}")

        # 检查设备可写性
        print("\n--- 检查设备可写性 ---")
        writable, info = check_selected_device_writable(selected_device)
        print(f"  可写: {'是' if writable else '否'}")
        if not writable:
            print(f"  原因: {info.get('info', 'Unknown')}")

        # 选择分区进行后续测试
        print("\n--- get_disk_info 测试 ---")
        test_partition = device_path + 's1'
        info_result = get_disk_info(test_partition)
        print(f"  状态: {'成功' if info_result['ok'] else '失败'}")
        print(f"  信息: {info_result['message']}")
        if info_result["data"]:
            # 只展示部分关键信息
            d = info_result["data"]
            print(f"  设备: {d.get('DeviceNode', '-')}  卷标: {d.get('VolumeName', '-')}  文件系统: {d.get('FilesystemName', d.get('Content', '-'))}  容量: {d.get('TotalSize', d.get('Size', 0)) // (1024**3)}GB  挂载点: {d.get('MountPoint', '-')}  内置: {d.get('Internal', d.get('OSInternalMedia', '-') )}")

        # 格式化分区（仅演示，不建议在真实设备上运行！）
        do_format = input(f"是否对 {test_partition} 执行格式化操作？(y/N): ").strip().lower()
        if do_format == "y":
            fs_type = "exFAT"
            vol_name = "TestVol"
            print("\n--- format_disk 测试 ---")
            format_result = format_disk(test_partition, fs_type=fs_type, name=vol_name)
            print(f"  状态: {'成功' if format_result['ok'] else '失败'}")
            print(f"  信息: {format_result['message']}")
            if format_result["data"]:
                d = format_result["data"]
                print(f"  分区: {d.get('partition_path', '-')}  文件系统: {d.get('fs_type', '-')}  卷标: {d.get('name', '-')}")
        else:
            print("跳过格式化操作。")

    # 镜像检查测试
    print("\n--- 镜像检查测试 ---")
    test_images = [
        "resources/test_iso/blank_1mb.iso",
        "resources/test_iso/blank_10mb.dmg",
        "resources/test_iso/blank_10mb.img"
    ]
    for img_path in test_images:
        result = check_image_file(img_path)
        print(f"  镜像: {img_path}")
        print(f"    状态: {'通过' if result['ok'] else '失败'}")
        print(f"    信息: {result['message']}")
        if result["data"]:
            d = result["data"]
            print(f"    格式: {d.get('format', '-')}  SHA256: {d.get('sha256', '-')}")
        print("  ---")