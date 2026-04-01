#!/usr/bin/env python3
"""
dev_write.sh — 将镜像写入目标设备。
用法：./scripts/mac/dev_write.sh <image_path> <device_path>
示例：./scripts/mac/dev_write.sh ~/Downloads/ubuntu.iso /dev/disk2

注意：此操作会清除目标设备上的所有数据，请确认设备路径正确。
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.api.bootoo_api import (
    check_image_file,
    get_available_devices,
    check_selected_device_writable,
    unmount_device,
    write_image,
    get_suggestions,
)

# ── 参数检查 ──────────────────────────────────────────────────────────────────

if len(sys.argv) < 3:
    print("用法：./scripts/mac/dev_write.sh <image_path> <device_path>")
    sys.exit(1)

src = os.path.expanduser(sys.argv[1])
dst = sys.argv[2]

# ── 镜像校验（不含 SHA256）────────────────────────────────────────────────────

print(f"\n[1/4] 检查镜像文件：{src}")
img_result = check_image_file(src)
if not img_result["ok"]:
    print(f"  ✗ {img_result['message']}  (code: {img_result['code']})")
    sys.exit(1)

img_data = img_result["data"]
size_gb = img_data["size"] / 1024**3
print(f"  格式: {img_data['format']}   大小: {size_gb:.2f} GB")

# ── 设备校验 ──────────────────────────────────────────────────────────────────

print(f"\n[2/4] 检查目标设备：{dst}")
available = get_available_devices()
target = next((d for d in available if d["device"] == dst), None)

if target is None:
    print(f"  ✗ {dst} 不在可用设备列表中，请用 dev_scan.sh 确认设备路径。")
    sys.exit(1)

writable, detail = check_selected_device_writable(target)
if not writable:
    print(f"  ✗ 设备不可写：{detail['info']}")
    sys.exit(1)

size_gb_dev = target["size_bytes"] / 1024**3
print(f"  设备容量: {size_gb_dev:.1f} GB   可写: 是")

# ── 用户确认 ──────────────────────────────────────────────────────────────────

print(f"\n  即将把 {os.path.basename(src)} 写入 {dst}，目标设备数据将被清除。")
confirm = input("  确认继续？(yes/N): ").strip().lower()
if confirm != "yes":
    print("  已取消。")
    sys.exit(0)

# ── 卸载设备 ──────────────────────────────────────────────────────────────────

print(f"\n[3/4] 卸载设备：{dst}")
unmount_result = unmount_device(dst)
if not unmount_result["ok"]:
    print(f"  ⚠ 卸载失败（{unmount_result['message']}），继续尝试写入...")
else:
    print("  卸载成功。")

# ── 写入 ──────────────────────────────────────────────────────────────────────

print(f"\n[4/4] 写入中...")

def _progress(p: float):
    filled = int(p / 5)
    bar = "█" * filled + "░" * (20 - filled)
    print(f"\r  [{bar}] {p:5.1f}%", end="", flush=True)

write_result = write_image(src, dst, progress_callback=_progress)
print()  # 换行

if write_result["ok"]:
    print(f"\n  写入完成。")
else:
    print(f"\n  ✗ 写入失败：{write_result['message']}  (code: {write_result['code']})")
    suggestions = get_suggestions(write_result["code"])["data"]["suggestions"]
    print("\n  修复建议：")
    for s in suggestions:
        print(f"    • {s}")
    sys.exit(1)
