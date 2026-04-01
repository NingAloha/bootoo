#!/usr/bin/env python3
"""
dev_scan.sh — 扫描并列出所有可用外置设备。
用法：./scripts/mac/dev_scan.sh [--all]
  --all  同时显示系统盘和内置盘
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.api.bootoo_api import get_all_devices, get_available_devices

all_mode = "--all" in sys.argv

devices = get_all_devices() if all_mode else get_available_devices()

if not devices:
    print("未找到可用设备。" if not all_mode else "未找到任何设备。")
    sys.exit(0)

label = "所有设备" if all_mode else "可用外置设备"
print(f"\n{'─' * 48}")
print(f"  {label}（共 {len(devices)} 个）")
print(f"{'─' * 48}")
for d in devices:
    size_gb = d.get("size_bytes", 0) / 1024**3
    vols = ", ".join(d.get("volumes") or []) or "-"
    flags = []
    if d.get("internal"):
        flags.append("内置")
    if d.get("is_system_risk"):
        flags.append("系统盘")
    if d.get("removable"):
        flags.append("可移动")
    flag_str = f"  [{', '.join(flags)}]" if flags else ""
    print(f"  {d['device']:<16} {size_gb:>7.1f} GB   卷: {vols}{flag_str}")
print(f"{'─' * 48}\n")
