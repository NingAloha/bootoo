import os
import re
import signal
import subprocess
import logging
from typing import Callable, Optional, Dict, Any

logger = logging.getLogger(__name__)

def _is_dmg(path: str) -> bool:
    # 扩展名检查仅作初步判断，后续可扩展为 magic byte 检测
    return path.lower().endswith('.dmg')

def _get_image_size(src: str) -> Optional[int]:
    """
    获取镜像文件大小（字节），文件不存在或无法读取时返回 None。
    """
    try:
        return os.path.getsize(src)
    except Exception:
        return None

def _dd_write(
    src: str,
    dst: str,
    block_size: int = 1024 * 1024,
    progress_callback: Optional[Callable[[float], None]] = None
) -> Dict[str, Any]:
    """
    使用 dd 写入镜像到目标设备，支持进度回调。
    macOS 原生 dd（BSD）不支持 status=progress，改用 SIGINFO 轮询获取进度。
    """
    total_size = _get_image_size(src)
    if total_size is None:
        return {"ok": False, "code": "SRC_ERROR", "message": "无法获取镜像大小", "data": None}

    # 原有代码使用 status=progress，macOS BSD dd 不支持此参数，进度回调永远不会触发。
    # 已移除 status=progress，改为定期发送 SIGINFO 信号获取 dd 进度输出。
    # cmd = ["dd", f"if={src}", f"of={dst}", f"bs={block_size}", "status=progress"]  ← 已移除
    cmd = ["dd", f"if={src}", f"of={dst}", f"bs={block_size}"]
    try:
        stderr_lines = []
        with subprocess.Popen(cmd, stderr=subprocess.PIPE, bufsize=1, universal_newlines=True) as proc:
            import threading, time

            def _siginfo_sender():
                # 每秒发送一次 SIGINFO，触发 dd 输出当前进度到 stderr
                while proc.poll() is None:
                    try:
                        proc.send_signal(signal.SIGINFO)
                    except Exception:
                        break
                    time.sleep(1)

            if progress_callback:
                t = threading.Thread(target=_siginfo_sender, daemon=True)
                t.start()

            for line in proc.stderr:
                stderr_lines.append(line)
                # macOS dd SIGINFO 输出格式："{N} bytes transferred in {T} secs ({R} bytes/sec)"
                m = re.search(r'^(\d+)\s+bytes', line)
                if m and progress_callback and total_size > 0:
                    try:
                        copied = int(m.group(1))
                        progress_callback(min(100.0, copied / total_size * 100))
                    except Exception:
                        pass
            proc.wait()

        ok = proc.returncode == 0
        err_msg = "\n".join(stderr_lines).strip()
        return {
            "ok": ok,
            "code": "SUCCESS" if ok else "DD_FAILED",
            "message": "写入完成" if ok else "dd 写入失败",
            # 原有代码在 message 中拼接 err_msg（含路径），已移至 data 字段避免路径泄露
            "data": {"src": src, "dst": dst, "image_size": total_size, "stderr": err_msg if not ok else None},
        }
    except Exception as e:
        logger.error("_dd_write 异常: %s", e)
        return {"ok": False, "code": "DD_FAILED", "message": "dd 写入异常", "data": None}

def _asr_restore(
    src: str,
    dst: str,
    progress_callback: Optional[Callable[[float], None]] = None
) -> Dict[str, Any]:
    """
    使用 asr 恢复镜像到目标设备，支持进度回调。
    """
    image_size = _get_image_size(src)

    # --noverify 跳过写后校验，静默接受损坏写入，已移除。
    # "--noverify",  ← 已移除，默认开启写后校验
    cmd = [
        "asr", "restore",
        "--source", src,
        "--target", dst,
        "--erase",
        "--noprompt",
    ]
    try:
        output_lines = []
        # 原有代码使用 proc.stdout 迭代 + proc.wait()，在 stdout/stderr 混合时可能死锁。
        # 已改用 proc.communicate() 一次性读取全部输出，避免管道阻塞。
        # with subprocess.Popen(...) as proc:
        #     for line in proc.stdout: ...
        #     proc.wait()  ← 已替换
        with subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        ) as proc:
            stdout, _ = proc.communicate()
        output_lines = stdout.splitlines()
        for line in output_lines:
            if "Progress:" in line and progress_callback:
                # 原有解析：line.split("Progress:")[1].split("%")[-2].strip() — 依赖尾部格式，易出错
                # 已改为 regex 解析
                # percent = float(line.split("Progress:")[1].split("%")[-2].strip())  ← 已替换
                m = re.search(r'(\d+(?:\.\d+)?)\s*%', line)
                if m:
                    try:
                        progress_callback(float(m.group(1)))
                    except Exception:
                        pass
        ok = proc.returncode == 0
        out_msg = "\n".join(output_lines).strip()
        return {
            "ok": ok,
            "code": "SUCCESS" if ok else "ASR_FAILED",
            "message": "写入完成" if ok else "asr 写入失败",
            # 原有代码在 message 中拼接 out_msg（含路径），已移至 data 字段
            "data": {"src": src, "dst": dst, "image_size": image_size, "output": out_msg if not ok else None},
        }
    except Exception as e:
        logger.error("_asr_restore 异常: %s", e)
        return {"ok": False, "code": "ASR_FAILED", "message": "asr 写入异常", "data": None}


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
    :return: 结构化结果字典，data 字段包含 image_size（字节）供调用方做空间预检
    """
    # 输入校验
    if not src or not os.path.isfile(src):
        return {"ok": False, "code": "SRC_ERROR", "message": "镜像文件不存在", "data": None}
    if not dst or not dst.startswith("/dev/"):
        return {"ok": False, "code": "DST_ERROR", "message": "无效的目标设备路径", "data": None}

    if _is_dmg(src):
        return _asr_restore(src, dst, progress_callback)
    else:
        return _dd_write(src, dst, progress_callback=progress_callback)