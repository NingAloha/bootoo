#!/usr/bin/env python3
"""
bootoo — Apple Silicon Mac 启动盘制作工具（终端版）
用法：
  bootoo scan [--all] [--json]
  bootoo write <image_path> <device_path> [--json]
  bootoo verify <device_path> <image_size_bytes> [mount_point] [os_type] [--json]
  bootoo help
"""
import sys
import os
import json as _json

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from core.api.bootoo_api import (
    check_image_file,
    get_all_devices,
    get_available_devices,
    check_selected_device_writable,
    unmount_device,
    write_image,
    verify_device_capacity,
    verify_device_partition,
    verify_boot_files,
    get_suggestions,
)

_SEP = "─" * 50


def _json_out(data: dict):
    print(_json.dumps(data, ensure_ascii=False, indent=2))


def cmd_scan(args):
    json_mode = "--json" in args
    all_mode  = "--all"  in args
    devices   = get_all_devices() if all_mode else get_available_devices()

    if json_mode:
        _json_out({"ok": True, "devices": devices})
        return

    label = "所有设备" if all_mode else "可用外置设备"
    if not devices:
        print(f"未找到{label}。")
        return

    print(f"\n{_SEP}")
    print(f"  {label}（共 {len(devices)} 个）")
    print(_SEP)
    for d in devices:
        size_gb  = d.get("size_bytes", 0) / 1024 ** 3
        vols     = ", ".join(d.get("volumes") or []) or "-"
        flags    = []
        if d.get("internal"):       flags.append("内置")
        if d.get("is_system_risk"): flags.append("系统盘")
        if d.get("removable"):      flags.append("可移动")
        flag_str = f"  [{', '.join(flags)}]" if flags else ""
        print(f"  {d['device']:<16} {size_gb:>7.1f} GB   卷: {vols}{flag_str}")
    print(f"{_SEP}\n")


def cmd_write(args):
    json_mode = "--json" in args
    args      = [a for a in args if a != "--json"]

    if len(args) < 2:
        if json_mode:
            _json_out({"ok": False, "code": "USAGE_ERROR", "message": "缺少参数"})
        else:
            print("用法：bootoo write <image_path> <device_path>")
        sys.exit(1)

    src = os.path.expanduser(args[0])
    dst = args[1]

    # 1. 镜像校验
    if not json_mode:
        print(f"\n[1/4] 检查镜像文件：{src}")
    img = check_image_file(src)
    if not img["ok"]:
        if json_mode:
            _json_out(img)
        else:
            print(f"  ✗ {img['message']}  (code: {img['code']})")
        sys.exit(1)
    if not json_mode:
        d = img["data"]
        print(f"  格式: {d['format']}   大小: {d['size'] / 1024**3:.2f} GB")

    # 2. 设备校验
    if not json_mode:
        print(f"\n[2/4] 检查目标设备：{dst}")
    available = get_available_devices()
    target    = next((x for x in available if x["device"] == dst), None)
    if target is None:
        msg = f"{dst} 不在可用设备列表中"
        if json_mode:
            _json_out({"ok": False, "code": "DEVICE_INVALID", "message": msg})
        else:
            print(f"  ✗ {msg}，请用 bootoo scan 确认设备路径。")
        sys.exit(1)
    writable, detail = check_selected_device_writable(target)
    if not writable:
        if json_mode:
            _json_out({"ok": False, "code": "PERMISSION_DENIED", "message": detail["info"]})
        else:
            print(f"  ✗ 设备不可写：{detail['info']}")
        sys.exit(1)
    if not json_mode:
        print(f"  设备容量: {target['size_bytes'] / 1024**3:.1f} GB   可写: 是")

    # 3. 用户确认（JSON 模式跳过，由调用方负责确认）
    if not json_mode:
        print(f"\n  即将把 {os.path.basename(src)} 写入 {dst}，目标设备数据将被清除。")
        confirm = input("  确认继续？(yes/N): ").strip().lower()
        if confirm != "yes":
            print("  已取消。")
            sys.exit(0)

    # 4. 卸载
    if not json_mode:
        print(f"\n[3/4] 卸载设备：{dst}")
    u = unmount_device(dst)
    if not json_mode:
        if u["ok"]:
            print("  卸载成功。")
        else:
            print(f"  ⚠ 卸载失败（{u['message']}），继续尝试写入...")

    # 5. 写入
    if not json_mode:
        print(f"\n[4/4] 写入中...")

    def _progress(p: float):
        if json_mode:
            return
        filled = int(p / 5)
        bar    = "█" * filled + "░" * (20 - filled)
        print(f"\r  [{bar}] {p:5.1f}%", end="", flush=True)

    result = write_image(src, dst, progress_callback=_progress)
    if not json_mode:
        print()

    if json_mode:
        _json_out(result)
        sys.exit(0 if result["ok"] else 1)

    if result["ok"]:
        print("\n  写入完成。")
    else:
        print(f"\n  ✗ 写入失败：{result['message']}  (code: {result['code']})")
        for s in get_suggestions(result["code"])["data"]["suggestions"]:
            print(f"    • {s}")
        sys.exit(1)


def cmd_verify(args):
    json_mode = "--json" in args
    args      = [a for a in args if a != "--json"]

    if len(args) < 2:
        if json_mode:
            _json_out({"ok": False, "code": "USAGE_ERROR", "message": "缺少参数"})
        else:
            print("用法：bootoo verify <device_path> <image_size_bytes> [mount_point] [os_type]")
        sys.exit(1)

    device_path = args[0]
    image_size  = int(args[1])
    mount_point = args[2] if len(args) > 2 else None
    os_type     = args[3] if len(args) > 3 else "windows"

    cap  = verify_device_capacity(device_path, image_size)
    part = verify_device_partition(device_path)
    files_result = verify_boot_files(mount_point, os_type) if mount_point else None

    overall_ok = cap["ok"] and part["ok"] and (files_result["ok"] if files_result else True)

    if json_mode:
        _json_out({
            "ok":      overall_ok,
            "device":  device_path,
            "capacity": cap,
            "partition": part,
            "files":   files_result,
        })
        sys.exit(0 if overall_ok else 1)

    # human output
    failed = False
    print(f"\n{_SEP}")
    print(f"  写后校验：{device_path}")
    print(_SEP)

    print(f"\n[1/3] 容量校验          {'✓' if cap['ok'] else '✗'}")
    if cap["ok"]:
        d = cap["data"]
        print(f"      设备: {d['device_size'] / 1024**3:.1f} GB   镜像: {d['image_size'] / 1024**3:.2f} GB")
    else:
        print(f"      {cap['message']}")
        for s in get_suggestions(cap["code"])["data"]["suggestions"]:
            print(f"      • {s}")
        failed = True

    print(f"\n[2/3] 分区存在性校验    {'✓' if part['ok'] else '✗'}")
    if part["ok"]:
        print(f"      检测到 {part['data']['partition_count']} 个分区：{part['data']['partitions']}")
    else:
        print(f"      {part['message']}")
        for s in get_suggestions(part["code"])["data"]["suggestions"]:
            print(f"      • {s}")
        failed = True

    if files_result:
        print(f"\n[3/3] 引导文件校验      {'✓' if files_result['ok'] else '✗'}  ({os_type})")
        if files_result["ok"]:
            print("      必要文件均存在。")
        else:
            print(f"      缺少文件：{files_result['data']['missing_files']}")
            for s in get_suggestions(files_result["code"])["data"]["suggestions"]:
                print(f"      • {s}")
            failed = True
    else:
        print(f"\n[3/3] 引导文件校验      跳过（未提供挂载点）")

    print(f"\n{_SEP}")
    if failed:
        print("  校验未通过，请参考上方修复建议。")
        print(f"{_SEP}\n")
        sys.exit(1)
    else:
        print("  所有校验通过。")
        print(f"{_SEP}\n")


def cmd_help():
    print("""
bootoo — Apple Silicon Mac 启动盘制作工具

用法：
  bootoo scan [--all] [--json]
      列出可用外置设备。--all 同时显示系统盘和内置盘。

  bootoo write <image_path> <device_path> [--json]
      将镜像写入目标设备。
      --json 模式跳过确认提示，由调用方负责确认。
      示例：bootoo write ~/Downloads/ubuntu.iso /dev/disk2

  bootoo verify <device_path> <image_size_bytes> [mount_point] [os_type] [--json]
      写后校验目标设备（容量、分区、引导文件）。
      os_type 支持：windows / linux / macos（默认 windows）
      示例：bootoo verify /dev/disk2 3276800000
            bootoo verify /dev/disk2 3276800000 /Volumes/USB windows

  bootoo help
      显示此帮助信息。
""")


_COMMANDS = {
    "scan":   cmd_scan,
    "write":  cmd_write,
    "verify": cmd_verify,
    "help":   lambda _: cmd_help(),
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in _COMMANDS:
        cmd_help()
        sys.exit(0)
    _COMMANDS[sys.argv[1]](sys.argv[2:])
