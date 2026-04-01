"""
bootoo_api 单元测试
所有测试均通过 mock 隔离底层系统调用，不依赖真实磁盘设备。
"""
import os
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
)


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

_FAKE_DEVICES = [
    {
        "id": "disk2", "device": "/dev/disk2", "size_bytes": 32 * 1024**3,
        "internal": False, "removable": True, "mounted": False,
        "volumes": ["USB"], "is_system_risk": False, "content": "",
    },
    {
        "id": "disk0", "device": "/dev/disk0", "size_bytes": 500 * 1024**3,
        "internal": True, "removable": False, "mounted": True,
        "volumes": ["Macintosh HD"], "is_system_risk": True, "content": "Apple_APFS_Container",
    },
]

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
        # 设置最小容量为 64GB，disk2（32GB）应被过滤
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
        device = {"id": "disk2", "device": "/dev/disk2"}
        writable, detail = check_selected_device_writable(device)
        assert writable is True
        assert detail["writable"] is True

    @patch("core.mac.permission_guard._check_writable", return_value=(False, "设备被占用（可能已挂载或被其他进程占用）"))
    def test_busy_device(self, _mock):
        device = {"id": "disk2", "device": "/dev/disk2"}
        writable, detail = check_selected_device_writable(device)
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

    @patch("subprocess.run")
    def test_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr=b"")
        result = unmount_device("/dev/disk2")
        assert result["ok"] is True
        assert result["code"] == "SUCCESS"
        assert result["data"]["device_path"] == "/dev/disk2"

    @patch("subprocess.run")
    def test_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr=b"disk not found")
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
    @patch("subprocess.run")
    def test_success(self, mock_run, _mock_unmount):
        mock_run.return_value = MagicMock(returncode=0, stderr=b"")
        result = format_disk("/dev/disk2s1", fs_type="exFAT", name="TestVol")
        assert result["ok"] is True
        assert result["data"]["fs_type"] == "exFAT"
        assert result["data"]["unmount_ok"] is True

    def test_name_truncation_exfat(self):
        # exFAT 卷标最长 11 字符
        with patch("core.mac.disk_ops.unmount_device", return_value={"ok": True, "message": ""}), \
             patch("subprocess.run", return_value=MagicMock(returncode=0, stderr=b"")):
            result = format_disk("/dev/disk2s1", fs_type="exFAT", name="A" * 20)
        assert result["ok"] is True
        assert len(result["data"]["name"]) <= 11

    def test_name_non_ascii_stripped(self):
        with patch("core.mac.disk_ops.unmount_device", return_value={"ok": True, "message": ""}), \
             patch("subprocess.run", return_value=MagicMock(returncode=0, stderr=b"")):
            result = format_disk("/dev/disk2s1", fs_type="exFAT", name="测试盘")
        # 非 ASCII 字符全部被过滤，回退为 "Untitled"
        assert result["ok"] is True
        assert result["data"]["name"] == "Untitled"


# ─── get_disk_info ────────────────────────────────────────────────────────────

class TestGetDiskInfo:
    def test_invalid_path(self):
        result = get_disk_info("disk2")
        assert result["ok"] is False
        assert result["code"] == "INFO_FAILED"

    @patch("subprocess.run")
    def test_success(self, mock_run):
        import plistlib
        fake_plist = plistlib.dumps({"DeviceNode": "/dev/disk2", "VolumeName": "USB"})
        mock_run.return_value = MagicMock(returncode=0, stdout=fake_plist, stderr=b"")
        result = get_disk_info("/dev/disk2")
        assert result["ok"] is True
        assert result["data"]["VolumeName"] == "USB"

    @patch("subprocess.run")
    def test_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout=b"", stderr=b"No disk found")
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

    @patch("core.mac.write_engine._dd_write")
    def test_iso_uses_dd(self, mock_dd, tmp_path):
        f = tmp_path / "test.iso"
        f.write_bytes(b"data")
        mock_dd.return_value = {"ok": True, "code": "SUCCESS", "message": "写入完成", "data": {"image_size": 4}}
        result = write_image(str(f), "/dev/disk2")
        mock_dd.assert_called_once()
        assert result["ok"] is True

    @patch("core.mac.write_engine._asr_restore")
    def test_dmg_uses_asr(self, mock_asr, tmp_path):
        f = tmp_path / "test.dmg"
        f.write_bytes(b"data")
        mock_asr.return_value = {"ok": True, "code": "SUCCESS", "message": "写入完成", "data": {"image_size": 4}}
        result = write_image(str(f), "/dev/disk2")
        mock_asr.assert_called_once()
        assert result["ok"] is True

    @patch("core.mac.write_engine._dd_write")
    def test_progress_callback_passed(self, mock_dd, tmp_path):
        f = tmp_path / "test.iso"
        f.write_bytes(b"data")
        mock_dd.return_value = {"ok": True, "code": "SUCCESS", "message": "写入完成", "data": {}}
        cb = MagicMock()
        write_image(str(f), "/dev/disk2", progress_callback=cb)
        _, kwargs = mock_dd.call_args
        assert kwargs.get("progress_callback") is cb
