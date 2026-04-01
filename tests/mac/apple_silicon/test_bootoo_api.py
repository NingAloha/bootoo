"""
bootoo_api 单元测试
所有测试均通过 mock 隔离底层系统调用，不依赖真实磁盘设备。
"""
import os
import plistlib
import pytest
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from core.api.bootoo_api import (
    check_image_file,
    get_all_devices,
    get_available_devices,
    check_selected_device_writable,
    unmount_device,
    format_disk,
    get_disk_info,
    write_image,
    verify_result,
    verify_device_capacity,
    verify_device_partition,
    verify_boot_files,
    get_suggestions,
    remount_device,
    repartition_device,
)


# ─── 公共 fixtures ────────────────────────────────────────────────────────────

_FAKE_DEVICES = [
    {
        "id": "disk2", "device": "/dev/disk2", "size_bytes": 32 * 1024**3,
        "internal": False, "removable": True, "mounted": False,
        "volumes": ["USB"], "is_system_risk": False, "content": "",
    },
    {
        "id": "disk0", "device": "/dev/disk0", "size_bytes": 500 * 1024**3,
        "internal": True, "removable": False, "mounted": True,
        "volumes": ["Macintosh HD"], "is_system_risk": True,
        "content": "Apple_APFS_Container",
    },
]

def _fake_plist(**kwargs) -> bytes:
    return plistlib.dumps(kwargs)

def _mock_run_ok(stdout: bytes = b"", stderr: bytes = b"") -> MagicMock:
    return MagicMock(returncode=0, stdout=stdout, stderr=stderr)

def _mock_run_fail(stderr: bytes = b"error") -> MagicMock:
    return MagicMock(returncode=1, stdout=b"", stderr=stderr)


# ─── check_image_file ────────────────────────────────────────────────────────

class TestCheckImageFile:
    def test_file_not_found(self, tmp_path):
        result = check_image_file(str(tmp_path / "nonexistent.iso"))
        assert result["ok"] is False
        assert result["code"] == "IMAGE_NOT_FOUND"
        assert result["data"]["path"].endswith("nonexistent.iso")

    def test_iso_file(self, tmp_path):
        f = tmp_path / "test.iso"
        f.write_bytes(b"x" * 1024)
        result = check_image_file(str(f))
        assert result["ok"] is True
        assert result["code"] == "SUCCESS"
        assert result["data"]["format"] == "iso"
        assert result["data"]["size"] == 1024
        assert len(result["data"]["sha256"]) == 64

    def test_dmg_file(self, tmp_path):
        f = tmp_path / "test.dmg"
        f.write_bytes(b"y" * 512)
        result = check_image_file(str(f))
        assert result["ok"] is True
        assert result["data"]["format"] == "dmg"
        assert result["data"]["size"] == 512

    def test_img_file(self, tmp_path):
        f = tmp_path / "test.img"
        f.write_bytes(b"z" * 256)
        result = check_image_file(str(f))
        assert result["ok"] is True
        assert result["data"]["format"] == "img"

    def test_unknown_format(self, tmp_path):
        f = tmp_path / "test.bin"
        f.write_bytes(b"a" * 128)
        result = check_image_file(str(f))
        assert result["ok"] is True
        assert result["data"]["format"] == "unknown"

    def test_tilde_expansion(self, tmp_path, monkeypatch):
        f = tmp_path / "test.iso"
        f.write_bytes(b"data")
        monkeypatch.setenv("HOME", str(tmp_path))
        result = check_image_file("~/test.iso")
        assert result["ok"] is True


# ─── get_all_devices / get_available_devices ─────────────────────────────────

class TestGetDevices:
    @patch("core.mac.device_detection._scan_devices", return_value=_FAKE_DEVICES)
    def test_get_all_devices_returns_all(self, _mock):
        result = get_all_devices()
        assert len(result) == 2

    @patch("core.mac.device_detection._scan_devices", return_value=_FAKE_DEVICES)
    def test_get_available_devices_filters_system(self, _mock):
        result = get_available_devices()
        assert all(not d["is_system_risk"] for d in result)
        assert all(not d["internal"] for d in result)

    @patch("core.mac.device_detection._scan_devices", return_value=_FAKE_DEVICES)
    def test_get_available_devices_min_size(self, _mock):
        result = get_available_devices(min_size_bytes=64 * 1024**3)
        assert len(result) == 0

    @patch("core.mac.device_detection._scan_devices", return_value=[])
    def test_get_available_devices_empty(self, _mock):
        assert get_available_devices() == []


# ─── check_selected_device_writable ──────────────────────────────────────────

class TestCheckSelectedDeviceWritable:
    def test_missing_device_path(self):
        writable, detail = check_selected_device_writable({"id": "disk2"})
        assert writable is False
        assert "无设备路径" in detail["info"]

    @patch("core.mac.permission_guard._check_writable", return_value=(True, ""))
    def test_writable_device(self, _mock):
        writable, detail = check_selected_device_writable({"id": "disk2", "device": "/dev/disk2"})
        assert writable is True
        assert detail["writable"] is True

    @patch("core.mac.permission_guard._check_writable", return_value=(False, "设备被占用（可能已挂载或被其他进程占用）"))
    def test_busy_device(self, _mock):
        writable, detail = check_selected_device_writable({"id": "disk2", "device": "/dev/disk2"})
        assert writable is False
        assert "占用" in detail["info"]


# ─── unmount_device ───────────────────────────────────────────────────────────

class TestUnmountDevice:
    def test_invalid_path(self):
        result = unmount_device("not_a_dev_path")
        assert result["ok"] is False
        assert result["code"] == "UNMOUNT_FAILED"

    def test_empty_path(self):
        result = unmount_device("")
        assert result["ok"] is False

    @patch("subprocess.run", return_value=_mock_run_ok())
    def test_success(self, _mock):
        result = unmount_device("/dev/disk2")
        assert result["ok"] is True
        assert result["code"] == "SUCCESS"
        assert result["data"]["device_path"] == "/dev/disk2"

    @patch("subprocess.run", return_value=_mock_run_fail(b"disk not found"))
    def test_failure(self, _mock):
        result = unmount_device("/dev/disk2")
        assert result["ok"] is False
        assert result["code"] == "UNMOUNT_FAILED"


# ─── format_disk ─────────────────────────────────────────────────────────────

class TestFormatDisk:
    def test_invalid_path(self):
        result = format_disk("disk2s1")
        assert result["ok"] is False
        assert result["code"] == "FORMAT_FAILED"

    def test_invalid_fs_type(self):
        result = format_disk("/dev/disk2s1", fs_type="NTFS")
        assert result["ok"] is False
        assert "NTFS" in result["message"]

    @patch("core.mac.disk_ops.unmount_device", return_value={"ok": True, "message": "卸载成功"})
    @patch("subprocess.run", return_value=_mock_run_ok())
    def test_success(self, _mock_run, _mock_unmount):
        result = format_disk("/dev/disk2s1", fs_type="exFAT", name="TestVol")
        assert result["ok"] is True
        assert result["data"]["fs_type"] == "exFAT"
        assert result["data"]["unmount_ok"] is True

    @patch("core.mac.disk_ops.unmount_device", return_value={"ok": True, "message": ""})
    @patch("subprocess.run", return_value=_mock_run_ok())
    def test_name_truncation_exfat(self, _mock_run, _mock_unmount):
        result = format_disk("/dev/disk2s1", fs_type="exFAT", name="A" * 20)
        assert result["ok"] is True
        assert len(result["data"]["name"]) <= 11

    @patch("core.mac.disk_ops.unmount_device", return_value={"ok": True, "message": ""})
    @patch("subprocess.run", return_value=_mock_run_ok())
    def test_name_non_ascii_stripped(self, _mock_run, _mock_unmount):
        result = format_disk("/dev/disk2s1", fs_type="exFAT", name="测试盘")
        assert result["ok"] is True
        assert result["data"]["name"] == "Untitled"

    @patch("core.mac.disk_ops.unmount_device", return_value={"ok": True, "message": ""})
    @patch("subprocess.run", return_value=_mock_run_ok())
    def test_name_truncation_apfs(self, _mock_run, _mock_unmount):
        result = format_disk("/dev/disk2s1", fs_type="APFS", name="B" * 30)
        assert result["ok"] is True
        assert len(result["data"]["name"]) <= 27


# ─── get_disk_info ────────────────────────────────────────────────────────────

class TestGetDiskInfo:
    def test_invalid_path(self):
        result = get_disk_info("disk2")
        assert result["ok"] is False
        assert result["code"] == "INFO_FAILED"

    @patch("subprocess.run")
    def test_success(self, mock_run):
        mock_run.return_value = _mock_run_ok(
            stdout=_fake_plist(DeviceNode="/dev/disk2", VolumeName="USB")
        )
        result = get_disk_info("/dev/disk2")
        assert result["ok"] is True
        assert result["data"]["VolumeName"] == "USB"

    @patch("subprocess.run", return_value=_mock_run_fail(b"No disk found"))
    def test_failure(self, _mock):
        result = get_disk_info("/dev/disk99")
        assert result["ok"] is False
        assert result["code"] == "INFO_FAILED"


# ─── write_image ──────────────────────────────────────────────────────────────

class TestWriteImage:
    def test_src_not_found(self, tmp_path):
        result = write_image(str(tmp_path / "missing.iso"), "/dev/disk2")
        assert result["ok"] is False
        assert result["code"] == "SRC_ERROR"

    def test_invalid_dst(self, tmp_path):
        f = tmp_path / "test.iso"
        f.write_bytes(b"data")
        result = write_image(str(f), "disk2")
        assert result["ok"] is False
        assert result["code"] == "DST_ERROR"

    @patch("core.mac.write_engine._dd_write",
           return_value={"ok": True, "code": "SUCCESS", "message": "写入完成", "data": {"image_size": 4}})
    def test_iso_uses_dd(self, mock_dd, tmp_path):
        f = tmp_path / "test.iso"
        f.write_bytes(b"data")
        result = write_image(str(f), "/dev/disk2")
        mock_dd.assert_called_once()
        assert result["ok"] is True

    @patch("core.mac.write_engine._asr_restore",
           return_value={"ok": True, "code": "SUCCESS", "message": "写入完成", "data": {"image_size": 4}})
    def test_dmg_uses_asr(self, mock_asr, tmp_path):
        f = tmp_path / "test.dmg"
        f.write_bytes(b"data")
        result = write_image(str(f), "/dev/disk2")
        mock_asr.assert_called_once()
        assert result["ok"] is True

    @patch("core.mac.write_engine._dd_write",
           return_value={"ok": True, "code": "SUCCESS", "message": "写入完成", "data": {}})
    def test_progress_callback_passed(self, mock_dd, tmp_path):
        f = tmp_path / "test.iso"
        f.write_bytes(b"data")
        cb = MagicMock()
        write_image(str(f), "/dev/disk2", progress_callback=cb)
        _, kwargs = mock_dd.call_args
        assert kwargs.get("progress_callback") is cb

    @patch("core.mac.write_engine._dd_write",
           return_value={"ok": False, "code": "DD_FAILED", "message": "dd 写入失败", "data": None})
    def test_dd_failure_propagated(self, _mock, tmp_path):
        f = tmp_path / "test.img"
        f.write_bytes(b"data")
        result = write_image(str(f), "/dev/disk2")
        assert result["ok"] is False
        assert result["code"] == "DD_FAILED"


# ─── verify_result / verify_device_capacity / verify_device_partition ─────────

class TestVerifyResult:
    def test_invalid_device_path(self):
        result = verify_result("disk2", 1024)
        assert result["ok"] is False
        assert result["code"] == "VERIFY_CAPACITY_FAIL"

    @patch("core.mac.verify._get_disk_info_plist", return_value={"TotalSize": 100})
    @patch("core.mac.verify._get_partition_list",
           return_value=[{"DeviceIdentifier": "disk2s1"}])
    def test_success_without_mount_point(self, _mock_part, _mock_info):
        result = verify_result("/dev/disk2", 50)
        assert result["ok"] is True
        assert result["code"] == "SUCCESS"
        assert "capacity" in result["data"]
        assert "partition" in result["data"]

    @patch("core.mac.verify._get_disk_info_plist", return_value={"TotalSize": 10})
    def test_capacity_fail_short_circuits(self, _mock_info):
        result = verify_result("/dev/disk2", 9999)
        assert result["ok"] is False
        assert result["code"] == "VERIFY_CAPACITY_FAIL"
        assert "partition" not in result["data"]

    @patch("core.mac.verify._get_disk_info_plist", return_value={"TotalSize": 9999})
    @patch("core.mac.verify._get_partition_list", return_value=[])
    def test_partition_fail_short_circuits(self, _mock_part, _mock_info):
        result = verify_result("/dev/disk2", 50)
        assert result["ok"] is False
        assert result["code"] == "VERIFY_PARTITION_FAIL"

    @patch("core.mac.verify._get_disk_info_plist", return_value={"TotalSize": 9999})
    @patch("core.mac.verify._get_partition_list",
           return_value=[{"DeviceIdentifier": "disk2s1"}])
    def test_files_checked_when_mount_point_given(self, _mock_part, _mock_info, tmp_path):
        # 挂载点存在但缺少引导文件 → VERIFY_FILES_FAIL
        result = verify_result("/dev/disk2", 50, mount_point=str(tmp_path), os_type="windows")
        assert result["ok"] is False
        assert result["code"] == "VERIFY_FILES_FAIL"

    @patch("core.mac.verify._get_disk_info_plist", return_value={"TotalSize": 9999})
    @patch("core.mac.verify._get_partition_list",
           return_value=[{"DeviceIdentifier": "disk2s1"}])
    def test_files_skipped_without_mount_point(self, _mock_part, _mock_info):
        result = verify_result("/dev/disk2", 50)
        assert result["ok"] is True
        assert "files" not in result["data"]


class TestVerifyDeviceCapacity:
    def test_invalid_path(self):
        result = verify_device_capacity("disk2", 1024)
        assert result["ok"] is False
        assert result["code"] == "VERIFY_CAPACITY_FAIL"

    @patch("core.mac.verify._get_disk_info_plist", return_value=None)
    def test_diskutil_failure(self, _mock):
        result = verify_device_capacity("/dev/disk2", 1024)
        assert result["ok"] is False
        assert result["code"] == "VERIFY_CAPACITY_FAIL"

    @patch("core.mac.verify._get_disk_info_plist", return_value={"TotalSize": 1000})
    def test_capacity_sufficient(self, _mock):
        result = verify_device_capacity("/dev/disk2", 500)
        assert result["ok"] is True
        assert result["data"]["device_size"] == 1000

    @patch("core.mac.verify._get_disk_info_plist", return_value={"TotalSize": 100})
    def test_capacity_insufficient(self, _mock):
        result = verify_device_capacity("/dev/disk2", 9999)
        assert result["ok"] is False
        assert result["code"] == "VERIFY_CAPACITY_FAIL"


class TestVerifyDevicePartition:
    def test_invalid_path(self):
        result = verify_device_partition("disk2")
        assert result["ok"] is False
        assert result["code"] == "VERIFY_PARTITION_FAIL"

    @patch("core.mac.verify._get_partition_list",
           return_value=[{"DeviceIdentifier": "disk2s1"}, {"DeviceIdentifier": "disk2s2"}])
    def test_partitions_found(self, _mock):
        result = verify_device_partition("/dev/disk2")
        assert result["ok"] is True
        assert result["data"]["partition_count"] == 2

    @patch("core.mac.verify._get_partition_list", return_value=[])
    def test_no_partitions(self, _mock):
        result = verify_device_partition("/dev/disk2")
        assert result["ok"] is False
        assert result["code"] == "VERIFY_PARTITION_FAIL"


# ─── verify_boot_files ────────────────────────────────────────────────────────

class TestVerifyBootFiles:
    def test_empty_mount_point(self):
        result = verify_boot_files("")
        assert result["ok"] is False
        assert result["code"] == "VERIFY_FILES_FAIL"

    def test_unknown_os_type_skips(self, tmp_path):
        result = verify_boot_files(str(tmp_path), os_type="dos")
        assert result["ok"] is True
        assert result["data"]["checked"] is False

    def test_windows_files_missing(self, tmp_path):
        result = verify_boot_files(str(tmp_path), os_type="windows")
        assert result["ok"] is False
        assert result["code"] == "VERIFY_FILES_FAIL"
        assert "bootmgr" in result["data"]["missing_files"]

    def test_windows_files_present(self, tmp_path):
        (tmp_path / "bootmgr").write_bytes(b"")
        boot_dir = tmp_path / "boot"
        boot_dir.mkdir()
        (boot_dir / "bcd").write_bytes(b"")
        result = verify_boot_files(str(tmp_path), os_type="windows")
        assert result["ok"] is True
        assert result["data"]["missing_files"] == []

    def test_linux_files_missing(self, tmp_path):
        result = verify_boot_files(str(tmp_path), os_type="linux")
        assert result["ok"] is False
        assert len(result["data"]["missing_files"]) > 0

    def test_macos_files_missing(self, tmp_path):
        result = verify_boot_files(str(tmp_path), os_type="macos")
        assert result["ok"] is False


# ─── get_suggestions ─────────────────────────────────────────────────────────

class TestGetSuggestions:
    @pytest.mark.parametrize("code", [
        "DD_FAILED", "ASR_FAILED", "UNMOUNT_FAILED", "FORMAT_FAILED",
        "VERIFY_CAPACITY_FAIL", "VERIFY_PARTITION_FAIL", "VERIFY_FILES_FAIL",
        "PERMISSION_DENIED", "DEVICE_BUSY",
    ])
    def test_known_codes_return_suggestions(self, code):
        result = get_suggestions(code)
        assert result["ok"] is True
        assert result["code"] == "SUCCESS"
        assert isinstance(result["data"]["suggestions"], list)
        assert len(result["data"]["suggestions"]) > 0

    def test_unknown_code_returns_fallback(self):
        result = get_suggestions("TOTALLY_UNKNOWN")
        assert result["ok"] is True
        assert len(result["data"]["suggestions"]) > 0

    def test_data_contains_error_code(self):
        result = get_suggestions("DD_FAILED")
        assert result["data"]["error_code"] == "DD_FAILED"


# ─── remount_device ───────────────────────────────────────────────────────────

class TestRemountDevice:
    def test_invalid_path(self):
        result = remount_device("disk2")
        assert result["ok"] is False
        assert result["code"] == "RECOVERY_FAILED"

    def test_empty_path(self):
        result = remount_device("")
        assert result["ok"] is False

    @patch("subprocess.run", return_value=_mock_run_ok())
    def test_success(self, _mock):
        result = remount_device("/dev/disk2")
        assert result["ok"] is True
        assert result["code"] == "SUCCESS"
        assert result["data"]["device_path"] == "/dev/disk2"

    @patch("subprocess.run", return_value=_mock_run_fail(b"mount failed"))
    def test_failure(self, _mock):
        result = remount_device("/dev/disk2")
        assert result["ok"] is False
        assert result["code"] == "RECOVERY_FAILED"


# ─── repartition_device ───────────────────────────────────────────────────────

class TestRepartitionDevice:
    def test_invalid_path(self):
        result = repartition_device("disk2")
        assert result["ok"] is False
        assert result["code"] == "RECOVERY_FAILED"

    def test_empty_path(self):
        result = repartition_device("")
        assert result["ok"] is False

    @patch("subprocess.run", return_value=_mock_run_ok())
    def test_success(self, _mock):
        result = repartition_device("/dev/disk2", fs_type="exFAT", name="Recover")
        assert result["ok"] is True
        assert result["code"] == "SUCCESS"
        assert result["data"]["fs_type"] == "exFAT"
        assert result["data"]["name"] == "Recover"

    @patch("subprocess.run", return_value=_mock_run_fail(b"erase failed"))
    def test_failure(self, _mock):
        result = repartition_device("/dev/disk2")
        assert result["ok"] is False
        assert result["code"] == "RECOVERY_FAILED"
        assert result["data"] is None
