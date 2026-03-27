import subprocess

def unmount_device(device_path: str) -> bool:
    """
    卸载指定的磁盘设备。
    输入参数：
        - device_path: 设备路径（str），如"/dev/disk2"
    返回值：
        - bool: True 表示卸载成功，False 表示卸载失败
    """
    try:
        result = subprocess.run(
            ["diskutil", "unmountDisk", device_path],
            capture_output=True,
            check=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"卸载设备 {device_path} 失败: {e}")
        return False