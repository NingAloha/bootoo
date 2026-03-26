from typing import List, Dict, Any, Tuple
import os

def _check_device_write_access(devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    for d in devices:
        dev_path = d.get("device")
        if not dev_path:
            results.append({"id": d.get("id"), "device": dev_path, "writable": False, "info": "无设备路径"})
            continue
        writable, reason = _check_writable(dev_path)
        info = "可写" if writable else f"不可写（{reason}）"
        results.append({"id": d.get("id"), "device": dev_path, "writable": writable, "info": info})
    return results

def _check_writable(dev_path: str) -> Tuple[bool, str]:
    if not os.access(dev_path, os.W_OK):
        return False, "权限不足或未授权"
    try:
        fd = os.open(dev_path, os.O_WRONLY)
        os.close(fd)
        return True, ""
    except PermissionError:
        return False, "权限不足"
    except OSError as e:
        if e.errno == 16:  
            return False, "设备被占用（可能已挂载或被其他进程占用）"
        elif e.errno == 30:  
            return False, "只读文件系统"
        else:
            return False, f"系统错误: {e.strerror}"
    except Exception as e:
        return False, f"未知错误: {e}"
    
def check_device_write_access(devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return _check_device_write_access(devices)

if __name__ == "__main__":
    try:
        from device_detection import list_available_devices
        devices = list_available_devices()
        results = check_device_write_access(devices)
        if not results:
            print("未检测到可用的外置磁盘设备。请插入U盘或移动硬盘后重试。")
        elif all(not item["writable"] for item in results):
            print("未发现任何可写入的设备，请检查U盘是否已卸载所有分区、权限是否足够。")
        else:
            for device in results:
                print(f"设备ID: {device['id']}, 路径: {device['device']}, 可写: {device['writable']}, 详情: {device['info']}")
    except ImportError:
        print("请确保 device_detection.py 可用，或单独作为模块导入。")