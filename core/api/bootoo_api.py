from typing import List, Dict, Any, Tuple
from core.mac.device_detection import list_available_devices
from core.mac.permission_guard import check_device_writable

def get_available_devices() -> List[Dict[str, Any]]:
    return list_available_devices()

def check_selected_device_writable(device: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    return check_device_writable(device)