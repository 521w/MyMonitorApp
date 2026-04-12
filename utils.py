"""公共工具函数"""

import subprocess
import os
import time

# ============================================================
# Android 权限
# ============================================================
ANDROID = False
try:
    from android.permissions import request_permissions, Permission
    ANDROID = True
except Exception:
    pass


def request_android_perms():
    if not ANDROID:
        return
    try:
        perms = []
        for p in ['READ_EXTERNAL_STORAGE', 'WRITE_EXTERNAL_STORAGE']:
            try:
                perms.append(getattr(Permission, p))
            except AttributeError:
                perms.append(f"android.permission.{p}")
        if perms:
            request_permissions(perms)
    except Exception:
        pass


# ============================================================
# 崩溃日志
# ============================================================
CRASH_LOG = "/sdcard/pm_crash.log"


def log_crash(msg):
    try:
        with open(CRASH_LOG, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")
    except Exception:
        pass


# ============================================================
# 命令执行
# ============================================================

def run_cmd(cmd, root=False, timeout=5):
    try:
        if root:
            full_cmd = ['su', '-c', cmd]
        else:
            full_cmd = ['sh', '-c', cmd]
        r = subprocess.run(
            full_cmd, capture_output=True, text=True, timeout=timeout
        )
        out = r.stdout.strip()
        err = r.stderr.strip()
        return out if out else err if err else ""
    except subprocess.TimeoutExpired:
        return "[命令超时]"
    except FileNotFoundError:
        return "[未找到 su - 需要 Root 权限]"
    except Exception as e:
        return f"[错误: {e}]"


# ============================================================
# 文件读取
# ============================================================

def read_file_safe(path):
    try:
        with open(path, 'r') as f:
            return f.read().strip()
    except Exception:
        return ""


def tail_read(filepath, max_lines=500):
    try:
        file_size = os.path.getsize(filepath)
        read_size = min(file_size, max_lines * 200)
        with open(filepath, "rb") as f:
            if read_size < file_size:
                f.seek(-read_size, 2)
            raw = f.read()
        text = raw.decode("utf-8", errors="replace")
        lines = text.splitlines(keepends=True)
        if read_size < file_size and len(lines) > 1:
            lines = lines[1:]
        return lines[-max_lines:]
    except Exception:
        return []


# ============================================================
# 文本处理
# ============================================================

def esc(text):
    """转义 Kivy markup 特殊字符"""
    if not text:
        return ""
    return text.replace('&', '&amp;').replace('[', '&bl;').replace(']', '&br;')


def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def bar(pct, w=20):
    """生成美化文本进度条"""
    pct = max(0, min(100, pct))
    filled = int(pct / 100 * w)
    return '█' * filled + '░' * (w - filled)


def color_val(val, low=50, high=80):
    """根据数值返回颜色 hex（绿/黄/红）"""
    from theme import GREEN_HEX, YELLOW_HEX, RED_HEX
    if val < low:
        return GREEN_HEX
    elif val < high:
        return YELLOW_HEX
    return RED_HEX