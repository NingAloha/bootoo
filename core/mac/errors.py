"""
统一错误类型和错误码。
所有磁盘操作异常、权限不足、卸载失败等都在此集中定义，便于维护和上层统一处理。
"""

# ── 错误码常量 ──────────────────────────────────────────────────────────────────

# 通用
CODE_SUCCESS          = "SUCCESS"
CODE_UNKNOWN_ERROR    = "UNKNOWN_ERROR"

# 设备检测
CODE_DEVICE_SCAN_FAILED    = "DEVICE_SCAN_FAILED"
CODE_NO_DEVICES_FOUND      = "NO_DEVICES_FOUND"
CODE_DEVICE_INVALID        = "DEVICE_INVALID"

# 权限
CODE_PERMISSION_DENIED     = "PERMISSION_DENIED"
CODE_DEVICE_BUSY           = "DEVICE_BUSY"
CODE_DEVICE_READ_ONLY      = "DEVICE_READ_ONLY"

# 镜像
CODE_IMAGE_NOT_FOUND       = "IMAGE_NOT_FOUND"
CODE_IMAGE_FORMAT_INVALID  = "IMAGE_FORMAT_INVALID"
CODE_IMAGE_TOO_SMALL       = "IMAGE_TOO_SMALL"
CODE_IMAGE_HASH_FAILED     = "IMAGE_HASH_FAILED"

# 磁盘操作
CODE_UNMOUNT_FAILED        = "UNMOUNT_FAILED"
CODE_FORMAT_FAILED         = "FORMAT_FAILED"
CODE_INFO_FAILED           = "INFO_FAILED"

# 写入
CODE_SRC_ERROR             = "SRC_ERROR"
CODE_DST_ERROR             = "DST_ERROR"
CODE_DD_FAILED             = "DD_FAILED"
CODE_ASR_FAILED            = "ASR_FAILED"

# 写后校验
CODE_VERIFY_CAPACITY_FAIL  = "VERIFY_CAPACITY_FAIL"
CODE_VERIFY_PARTITION_FAIL = "VERIFY_PARTITION_FAIL"
CODE_VERIFY_FILES_FAIL     = "VERIFY_FILES_FAIL"
CODE_VERIFY_FAILED         = "VERIFY_FAILED"

# 恢复
CODE_RECOVERY_FAILED       = "RECOVERY_FAILED"


# ── 异常基类 ────────────────────────────────────────────────────────────────────

class BootooError(Exception):
    """bootoo 所有自定义异常的基类。"""
    code: str = CODE_UNKNOWN_ERROR

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        if code is not None:
            self.code = code
        self.message = message

    def to_dict(self):
        return {"ok": False, "code": self.code, "message": self.message, "data": None}


# ── 设备相关异常 ────────────────────────────────────────────────────────────────

class DeviceScanError(BootooError):
    """设备扫描失败。"""
    code = CODE_DEVICE_SCAN_FAILED


class DeviceInvalidError(BootooError):
    """设备路径无效或不符合写入条件。"""
    code = CODE_DEVICE_INVALID


# ── 权限相关异常 ────────────────────────────────────────────────────────────────

class PermissionDeniedError(BootooError):
    """权限不足，无法执行磁盘操作。"""
    code = CODE_PERMISSION_DENIED


class DeviceBusyError(BootooError):
    """设备正忙，无法写入。"""
    code = CODE_DEVICE_BUSY


class DeviceReadOnlyError(BootooError):
    """设备为只读，无法写入。"""
    code = CODE_DEVICE_READ_ONLY


# ── 镜像相关异常 ────────────────────────────────────────────────────────────────

class ImageNotFoundError(BootooError):
    """镜像文件不存在。"""
    code = CODE_IMAGE_NOT_FOUND


class ImageFormatError(BootooError):
    """镜像格式不支持或无法识别。"""
    code = CODE_IMAGE_FORMAT_INVALID


class ImageHashError(BootooError):
    """镜像 SHA256 校验失败。"""
    code = CODE_IMAGE_HASH_FAILED


# ── 磁盘操作异常 ────────────────────────────────────────────────────────────────

class UnmountError(BootooError):
    """卸载设备失败。"""
    code = CODE_UNMOUNT_FAILED


class FormatError(BootooError):
    """格式化分区失败。"""
    code = CODE_FORMAT_FAILED


# ── 写入异常 ────────────────────────────────────────────────────────────────────

class WriteError(BootooError):
    """写入操作失败（dd 或 asr）。"""
    code = CODE_DD_FAILED


# ── 校验异常 ────────────────────────────────────────────────────────────────────

class VerifyError(BootooError):
    """写后校验失败。"""
    code = CODE_VERIFY_FAILED


# ── 恢复异常 ────────────────────────────────────────────────────────────────────

class RecoveryError(BootooError):
    """恢复操作失败。"""
    code = CODE_RECOVERY_FAILED
