import subprocess
from core.mac.device_detection import list_available_devices
from typing import Dict, Any

# 对外接口：unmount_device、format_disk、get_disk_info
# 参数全部统一为 partition_path 或 device_path，直接传递即可，无需额外拼接或处理

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
    try:
        result = subprocess.run(
            ["diskutil", "unmountDisk", device_path],
            capture_output=True,
            check=True
        )
        return {
            "ok": result.returncode == 0,
            "code": "SUCCESS" if result.returncode == 0 else "UNMOUNT_FAILED",
            "message": "卸载成功" if result.returncode == 0 else result.stderr.decode(),
            "data": {"device_path": device_path} if result.returncode == 0 else None
        }
    except Exception as e:
        return {
            "ok": False,
            "code": "UNMOUNT_FAILED",
            "message": f"卸载设备 {device_path} 失败: {e}",
            "data": None
        }


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
    try:
        result = subprocess.run(
            ["diskutil", "eraseVolume", fs_type, name, partition_path],
            capture_output=True,
            check=True
        )
        return {
            "ok": result.returncode == 0,
            "code": "SUCCESS" if result.returncode == 0 else "FORMAT_FAILED",
            "message": "格式化成功" if result.returncode == 0 else result.stderr.decode(),
            "data": {"partition_path": partition_path, "fs_type": fs_type, "name": name} if result.returncode == 0 else None
        }
    except Exception as e:
        return {
            "ok": False,
            "code": "FORMAT_FAILED",
            "message": f"格式化分区 {partition_path} 失败: {e}",
            "data": None
        }


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
    try:
        result = subprocess.run(
            ["diskutil", "info", "-plist", path],
            capture_output=True,
            check=True
        )
        import plistlib
        info = plistlib.loads(result.stdout)
        return {
            "ok": True,
            "code": "SUCCESS",
            "message": "查询成功",
            "data": info
        }
    except Exception as e:
        return {
            "ok": False,
            "code": "INFO_FAILED",
            "message": f"查询信息 {path} 失败: {e}",
            "data": None
        }


def format_gb(size_bytes: int) -> str:
    gb = size_bytes / (1024 ** 3)
    return f"{gb:.2f} GB"


def print_disk_summary(info: dict):
    """
    实用磁盘信息摘要输出。
    """
    if not info:
        print("无磁盘信息")
        return
    # 兼容不同key
    fs_type = info.get("FilesystemName") or info.get("Content") or "-"
    device = info.get("DeviceNode") or info.get("DeviceIdentifier") or "-"
    size = info.get("TotalSize") or info.get("Size") or 0
    size_gb = f"{int(size) / (1024 ** 3):.2f} GB" if size else "-"
    vol_name = info.get("VolumeName") or "-"
    mount_point = info.get("MountPoint") or "-"
    is_system = info.get("Internal") or info.get("OSInternalMedia") or False
    print(f"设备路径: {device}")
    print(f"卷标名: {vol_name}")
    print(f"文件系统类型: {fs_type}")
    print(f"总容量: {size_gb}")
    print(f"挂载点: {mount_point}")
    print(f"是否内置/系统盘: {is_system}")


def ask_volume_name(default_name="Untitled") -> str:
    name = input(f"请输入卷标名（默认{default_name}）: ")
    return name.strip() or default_name

def list_partitions(device_info: dict) -> list:
    """
    返回磁盘所有分区的设备路径和卷标名列表。
    """
    partitions = []
    for part_key in ("Partitions", "APFSVolumes"):
        for part in device_info.get(part_key, []):
            dev = part.get("DeviceIdentifier")
            if dev:
                path = f"/dev/{dev}"
                name = part.get("VolumeName") or "-"
                partitions.append((path, name))
    return partitions

if __name__ == "__main__":
    # 获取可用设备列表
    devices = list_available_devices()
    if not devices:
        print("未检测到可用磁盘设备！")
        exit(1)
    print("可用磁盘设备：")
    for idx, d in enumerate(devices):
        print(f"{idx}: {d['device']}  容量: {format_gb(d['size_bytes'])}  卷: {d['volumes']}")
    choice = input("请选择设备编号: ")
    try:
        idx = int(choice)
        selected = devices[idx]
    except (ValueError, IndexError):
        print("无效选择")
        exit(1)
    test_disk = selected['device']
    print(f"你选择的设备: {test_disk}")
    # 获取分区列表
    disk_info = get_disk_info(test_disk)
    partitions = list_partitions(disk_info)
    if not partitions:
        # 兼容单分区老U盘
        partitions = [(test_disk + "s1", "-")]
    print("可用分区：")
    for idx, (p, n) in enumerate(partitions):
        print(f"{idx}: {p}  卷标: {n}")
    part_choice = input("请选择要操作的分区编号: ")
    try:
        part_idx = int(part_choice)
        test_partition = partitions[part_idx][0]
    except (ValueError, IndexError):
        print("无效选择")
        exit(1)

    # 只保留 macOS 原生支持的文件系统类型
    fs_types = [
        ("exFAT", "exFAT (Win/Linux/U盘通用)"),
        ("MS-DOS FAT32", "FAT32 (Win/Linux/兼容性好)"),
        ("APFS", "APFS (Mac系统盘)"),
        ("JHFS+", "Mac OS 扩展（日志式）")
    ]

    print("\n请选择要执行的操作：")
    print("1: 卸载磁盘")
    print("2: 格式化分区")
    print("3: 查询磁盘信息")
    op = input("请输入操作编号: ")

    if op == "1":
        print("--- 卸载磁盘 ---")
        result = unmount_device(test_disk)
        print(f"ok: {result['ok']}")
        print(f"code: {result['code']}")
        print(f"message: {result['message']}")
        if result["data"]:
            print(f"data: {result['data']}")
    elif op == "2":
        print("--- 格式化分区 ---")
        print("可选文件系统类型：")
        for i, (fs, desc) in enumerate(fs_types):
            print(f"{i}: {fs} - {desc}")
        fs_choice = input("请选择文件系统类型编号（默认0/exFAT）: ")
        try:
            fs_idx = int(fs_choice) if fs_choice else 0
            fs_type = fs_types[fs_idx][0]
        except (ValueError, IndexError):
            print("无效选择，使用默认exFAT")
            fs_type = "exFAT"
        vol_name = ask_volume_name()
        result = format_disk(test_partition, fs_type=fs_type, name=vol_name)
        print(f"ok: {result['ok']}")
        print(f"code: {result['code']}")
        print(f"message: {result['message']}")
        if result["data"]:
            print(f"data: {result['data']}")
    elif op == "3":
        print("--- 查询磁盘信息 ---")
        result = get_disk_info(test_partition)
        print(f"ok: {result['ok']}")
        print(f"code: {result['code']}")
        print(f"message: {result['message']}")
        if result["data"]:
            print_disk_summary(result["data"])
    else:
        print("无效操作编号")