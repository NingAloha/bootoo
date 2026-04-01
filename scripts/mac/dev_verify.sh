#!/usr/bin/env python3
"""
dev_verify.sh — 写后校验目标设备（容量、分区、引导文件）。
用法：./scripts/mac/dev_verify.sh <device_path> <image_size_bytes> [mount_point] [os_type]
示例：./scripts/mac/dev_verify.sh /dev/disk2 3276800000
      ./scripts/mac/dev_verify.sh /dev/disk2 3276800000 /Volumes/USB windows
os_type 支持：windows / linux / macos（默认 windows）
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.api.bootoo_api import (
    verify_device_capacity,
    verify_device_partition,
    verify_boot_files,
    get_suggestions,
)

# ── 参数检查 ──────────────────────────────────────────────────────────────────

if len(sys.argv) < 3:
    print("用法：./scripts/mac/dev_verify.sh <device_path> <image_size_bytes> [mount_point] [os_type]")
    sys.exit(1)

device_path     = sys.argv[1]
image_size      = int(sys.argv[2])
mount_point     = sys.argv[3] if len(sys.argv) > 3 else None
os_type         = sys.argv[4] if len(sys.argv) > 4 else "windows"

print(f"\n{'─' * 48}")
print(f"  写后校验：{device_path}")
print(f"{'─' * 48}")

failed = False

# ── 1. 容量校验 ───────────────────────────────────────────────────────────────

cap = verify_device_capacity(device_path, image_size)
status = "✓" if cap["ok"] else "✗"
print(f"\n[1/3] 容量校验          {status}")
if cap["ok"]:
    d = cap["data"]
    print(f"      设备: {d['device_size'] / 1024**3:.1f} GB   镜像: {d['image_size'] / 1024**3:.2f} GB")
else:
    print(f"      {cap['message']}")
    for s in get_suggestions(cap["code"])["data"]["suggestions"]:
        print(f"      • {s}")
    failed = True

# ── 2. 分区存在性校验 ─────────────────────────────────────────────────────────

part = verify_device_partition(device_path)
status = "✓" if part["ok"] else "✗"
print(f"\n[2/3] 分区存在性校验    {status}")
if part["ok"]:
    print(f"      检测到 {part['data']['partition_count']} 个分区：{part['data']['partitions']}")
else:
    print(f"      {part['message']}")
    for s in get_suggestions(part["code"])["data"]["suggestions"]:
        print(f"      • {s}")
    failed = True

# ── 3. 引导文件校验（可选）───────────────────────────────────────────────────

if mount_point:
    files = verify_boot_files(mount_point, os_type)
    status = "✓" if files["ok"] else "✗"
    print(f"\n[3/3] 引导文件校验      {status}  ({os_type})")
    if files["ok"]:
        print(f"      必要文件均存在。")
    else:
        print(f"      缺少文件：{files['data']['missing_files']}")
        for s in get_suggestions(files["code"])["data"]["suggestions"]:
            print(f"      • {s}")
        failed = True
else:
    print(f"\n[3/3] 引导文件校验      跳过（未提供挂载点）")

# ── 结果 ──────────────────────────────────────────────────────────────────────

print(f"\n{'─' * 48}")
if failed:
    print("  校验未通过，请参考上方修复建议。")
    print(f"{'─' * 48}\n")
    sys.exit(1)
else:
    print("  所有校验通过。")
    print(f"{'─' * 48}\n")
