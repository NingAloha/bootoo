import os
import subprocess
from typing import Callable, Optional, Dict, Any

def _is_dmg(path: str) -> bool:
    return path.lower().endswith('.dmg')

def _dd_write(
    src: str,
    dst: str,
    block_size: int = 1024 * 1024,
    progress_callback: Optional[Callable[[float], None]] = None
) -> Dict[str, Any]:
    """
    使用 dd 写入镜像到目标设备，支持进度回调。
    """
    try:
        total_size = os.path.getsize(src)
    except Exception as e:
        return {"ok": False, "code": "SRC_ERROR", "message": f"无法获取镜像大小: {e}", "data": None}
    copied = 0
    cmd = [
        "dd",
        f"if={src}",
        f"of={dst}",
        f"bs={block_size}",
        "status=progress"
    ]
    try:
        stderr_lines = []
        with subprocess.Popen(cmd, stderr=subprocess.PIPE, bufsize=1, universal_newlines=True) as proc:
            for line in proc.stderr:
                stderr_lines.append(line)
                if "bytes" in line and "copied" in line:
                    try:
                        copied = int(line.split()[0])
                        if progress_callback and total_size > 0:
                            percent = min(100.0, copied / total_size * 100)
                            progress_callback(percent)
                    except Exception:
                        pass
            proc.wait()
        ok = proc.returncode == 0
        err_msg = "\n".join(stderr_lines).strip()
        return {
            "ok": ok,
            "code": "SUCCESS" if ok else "DD_FAILED",
            "message": "写入完成" if ok else f"dd 写入失败: {err_msg}",
            "data": {"src": src, "dst": dst, "stderr": err_msg if not ok else None}
        }
    except Exception as e:
        return {
            "ok": False,
            "code": "DD_FAILED",
            "message": f"dd 写入异常: {e}",
            "data": None
        }

def _asr_restore(
    src: str,
    dst: str,
    progress_callback: Optional[Callable[[float], None]] = None
) -> Dict[str, Any]:
    """
    使用 asr 恢复镜像到目标设备，支持进度回调。
    """
    cmd = [
        "asr", "restore",
        "--source", src,
        "--target", dst,
        "--erase",
        "--noverify",
        "--noprompt"
    ]
    try:
        output_lines = []
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True) as proc:
            for line in proc.stdout:
                output_lines.append(line)
                if "Progress:" in line:
                    try:
                        percent = float(line.split("Progress:")[1].split("%")[-2].strip())
                        if progress_callback:
                            progress_callback(percent)
                    except Exception:
                        pass
            proc.wait()
        ok = proc.returncode == 0
        out_msg = "\n".join(output_lines).strip()
        return {
            "ok": ok,
            "code": "SUCCESS" if ok else "ASR_FAILED",
            "message": "写入完成" if ok else f"asr 写入失败: {out_msg}",
            "data": {"src": src, "dst": dst, "output": out_msg if not ok else None}
        }
    except Exception as e:
        return {
            "ok": False,
            "code": "ASR_FAILED",
            "message": f"asr 写入异常: {e}",
            "data": None
        }

def write_image_auto(
    src: str,
    dst: str,
    progress_callback: Optional[Callable[[float], None]] = None
) -> Dict[str, Any]:
    """
    自动判断镜像类型，dmg 用 asr，其余用 dd。
    :param src: 源镜像路径
    :param dst: 目标设备路径
    :param progress_callback: 进度回调
    :return: 结构化结果字典
    """
    if _is_dmg(src):
        return _asr_restore(src, dst, progress_callback)
    else:
        return _dd_write(src, dst, progress_callback=progress_callback)


# ========== 测试主函数（交互式，风格参考disk_ops） ===========
if __name__ == "__main__":
    import sys
    from core.mac.device_detection import list_available_devices
    from core.mac.disk_ops import unmount_device, format_disk, get_disk_info
    from core.mac.permission_guard import check_device_writable

    def format_gb(size_bytes):
        return f"{size_bytes / (1024 ** 3):.2f} GB"

    def ask_volume_name():
        name = input("请输入卷标名（默认Untitled）: ").strip()
        return name if name else "Untitled"

    # 1. 设备选择
    devices = list_available_devices()
    if not devices:
        print("未检测到可用磁盘设备！")
        sys.exit(1)
    print("可用磁盘设备：")
    for idx, d in enumerate(devices):
        print(f"{idx}: {d['device']}  容量: {format_gb(d['size_bytes'])}  卷: {d['volumes']}")
    choice = input("请选择设备编号: ")
    try:
        idx = int(choice)
        selected = devices[idx]
    except (ValueError, IndexError):
        print("无效选择")
        sys.exit(1)
    test_disk = selected['device']
    print(f"你选择的设备: {test_disk}")

    # 2. 获取分区列表
    info_res = get_disk_info(test_disk)
    if not info_res['ok']:
        print("获取磁盘信息失败！")
        sys.exit(1)
    info = info_res['data']
    # 简单分区提取逻辑
    partitions = []
    if 'Partitions' in info:
        for part in info['Partitions']:
            part_dev = part.get('DeviceIdentifier')
            part_name = part.get('VolumeName', '-')
            if part_dev:
                partitions.append((f"/dev/{part_dev}", part_name))
    if not partitions:
        # 兼容单分区老U盘
        partitions = [(test_disk + "s1", "-")]
    print("可用分区：")
    for idx, (p, n) in enumerate(partitions):
        print(f"{idx}: {p}  卷标: {n}")
    part_choice = input("请选择要操作的分区编号: ")
    try:
        part_idx = int(part_choice)
        test_partition = partitions[part_idx][0]
    except (ValueError, IndexError):
        print("无效选择")
        sys.exit(1)

    # 3. 操作选择
    print("\n请选择要执行的操作：")
    print("1: 卸载磁盘")
    print("2: 格式化分区")
    print("3: 检查可写性")
    print("4: 写入镜像（自动卸载+可写性检查）")
    op = input("请输入操作编号: ")

    if op == "1":
        print("--- 卸载磁盘 ---")
        result = unmount_device(test_disk)
        print(f"ok: {result['ok']}")
        print(f"code: {result['code']}")
        print(f"message: {result['message']}")
        if result["data"]:
            print(f"data: {result['data']}")
    elif op == "2":
        print("--- 格式化分区 ---")
        fs_types = [
            ("exFAT", "exFAT (Win/Linux/U盘通用)"),
            ("MS-DOS FAT32", "FAT32 (Win/Linux/兼容性好)"),
            ("APFS", "APFS (Mac系统盘)"),
            ("JHFS+", "Mac OS 扩展（日志式）")
        ]
        print("可选文件系统类型：")
        for i, (fs, desc) in enumerate(fs_types):
            print(f"{i}: {fs} - {desc}")
        fs_choice = input("请选择文件系统类型编号（默认0/exFAT）: ")
        try:
            fs_idx = int(fs_choice) if fs_choice else 0
            fs_type = fs_types[fs_idx][0]
        except (ValueError, IndexError):
            print("无效选择，使用默认exFAT")
            fs_type = "exFAT"
        vol_name = ask_volume_name()
        result = format_disk(test_partition, fs_type=fs_type, name=vol_name)
        print(f"ok: {result['ok']}")
        print(f"code: {result['code']}")
        print(f"message: {result['message']}")
        if result["data"]:
            print(f"data: {result['data']}")
    elif op == "3":
        print("--- 检查可写性 ---")
        writable, detail = check_device_writable(selected)
        print(f"可写: {writable}")
        print(f"详情: {detail['info']}")
    elif op == "4":
        print("--- 自动卸载分区 ---")
        result = unmount_device(test_partition)
        print(f"卸载: {result['message']}")
        print("--- 检查可写性 ---")
        writable, detail = check_device_writable(selected)
        print(f"可写: {writable}")
        print(f"详情: {detail['info']}")
        if not writable:
            print("分区不可写，终止写入！")
            sys.exit(1)
        print("--- 写入镜像 ---")
        import os
        while True:
            img_path = input("请输入要写入的镜像文件路径: ").strip()
            if not os.path.isfile(img_path):
                print("镜像文件不存在，请重新输入。")
                continue
            if os.path.getsize(img_path) == 0:
                print("镜像文件大小为0，请重新输入。")
                continue
            break
        def progress(percent):
            print(f"写入进度: {percent:.2f}%", end='\r')
        print("开始写入镜像...")
        write_res = write_image_auto(img_path, test_partition, progress_callback=progress)
        print("\n写入结果:", write_res['message'])
        if not write_res['ok']:
            sys.exit(1)
        print("全部流程完成！")
    else:
        print("无效操作编号")
