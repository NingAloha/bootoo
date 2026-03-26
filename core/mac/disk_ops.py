import subprocess

def unmount_device(device_path: str) -> bool:
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