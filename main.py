"""
Python Monitor v3.1 - Root 增强版（全中文界面）
5个标签页：系统监控 / 进程管理 / 终端 / 日志查看 / 系统日志
"""

from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.core.window import Window
import subprocess
import os
import time
import re
import traceback

# ============================================================
# Android 权限（防崩溃）
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
# 崩溃日志 - 闪退时写到文件方便排查
# ============================================================
CRASH_LOG = "/sdcard/pm_crash.log"


def log_crash(msg):
    try:
        with open(CRASH_LOG, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")
    except Exception:
        pass


# ============================================================
# 工具函数
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


def esc(text):
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
    pct = max(0, min(100, pct))
    f = int(pct / 100 * w)
    return '=' * f + '-' * (w - f)


# ============================================================
# 标签页 1：系统监控
# ============================================================

class SystemMonitorTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=8, spacing=6, **kwargs)
        self.prev_cpu = None

        scroll = ScrollView(size_hint=(1, 1))
        self.info = Label(
            text="正在加载...", size_hint_y=None,
            halign="left", valign="top",
            markup=True, font_size="14sp",
        )
        self.info.bind(
            texture_size=lambda *a: setattr(
                self.info, 'height', self.info.texture_size[1] + 40
            )
        )
        scroll.bind(
            width=lambda inst, w: setattr(
                self.info, 'text_size', (w - 16, None)
            )
        )
        scroll.add_widget(self.info)
        self.add_widget(scroll)

        btn = Button(
            text="手动刷新", size_hint_y=None, height=48,
            font_size="14sp", background_color=(0.2, 0.5, 0.8, 1),
        )
        btn.bind(on_press=lambda x: self.update(0))
        self.add_widget(btn)

        Clock.schedule_interval(self.update, 3)

    def _cpu_sample(self):
        line = read_file_safe('/proc/stat')
        if not line:
            return None
        first = line.split('\n')[0].split()
        if len(first) < 5:
            return None
        vals = list(map(int, first[1:8] if len(first) >= 8 else first[1:]))
        return sum(vals), vals[3]

    def update(self, dt):
        try:
            # CPU
            s = self._cpu_sample()
            cpu = 0
            if s and self.prev_cpu:
                td = s[0] - self.prev_cpu[0]
                idd = s[1] - self.prev_cpu[1]
                cpu = round((1 - idd / td) * 100, 1) if td > 0 else 0
            self.prev_cpu = s
            cc = "44ff44" if cpu < 50 else ("ffaa00" if cpu < 80 else "ff4444")

            # 内存
            mi = {}
            for line in read_file_safe('/proc/meminfo').split('\n'):
                p = line.split()
                if len(p) >= 2:
                    mi[p[0].rstrip(':')] = int(p[1])
            mt = mi.get('MemTotal', 1)
            ma = mi.get('MemAvailable', mi.get('MemFree', 0))
            mu = mt - ma
            mp = round(mu / mt * 100, 1) if mt > 0 else 0
            mc = "44ff44" if mp < 60 else ("ffaa00" if mp < 85 else "ff4444")

            # 电池
            bb = '/sys/class/power_supply/battery'
            bl = read_file_safe(f'{bb}/capacity') or '?'
            bs = read_file_safe(f'{bb}/status') or '?'
            bt_raw = read_file_safe(f'{bb}/temp')
            bt = f"{int(bt_raw) / 10:.1f}" if bt_raw.isdigit() else '?'
            bs_cn = {'Charging': '充电中', 'Discharging': '放电中',
                     'Full': '已充满', 'Not charging': '未充电'}.get(bs, bs)

            # CPU 温度
            ct = '?'
            for p in ['/sys/class/thermal/thermal_zone0/temp']:
                v = read_file_safe(p)
                if v and v.isdigit():
                    t = int(v)
                    ct = f"{t / 1000:.1f}" if t > 1000 else str(t)
                    break

            # 运行时间
            ur = read_file_safe('/proc/uptime')
            if ur:
                secs = int(float(ur.split()[0]))
                uptime = f"{secs // 3600}小时 {(secs % 3600) // 60}分钟"
            else:
                uptime = '?'

            # 内核
            kv = read_file_safe('/proc/version')
            kernel = kv.split()[2] if kv and len(kv.split()) > 2 else '?'

            # 磁盘
            disk = run_cmd("df -h /data /sdcard 2>/dev/null | tail -2")

            # 网络
            net = run_cmd(
                "cat /proc/net/dev | awk 'NR>2{printf \"%s 接收:%s 发送:%s\\n\",$1,$2,$10}'"
            )

            self.info.text = (
                f"[b][color=88ccff]━━━ 系统监控仪表盘 ━━━[/color][/b]\n\n"
                f"[b]处理器[/b]\n"
                f"[color={cc}]  |{bar(cpu)}| {cpu}%[/color]\n\n"
                f"[b]内存[/b]\n"
                f"[color={mc}]  |{bar(mp)}| {mp}%[/color]\n"
                f"  已用 {mu // 1024}MB / 共 {mt // 1024}MB\n\n"
                f"[b]电池[/b]\n"
                f"  电量 {esc(bl)}% | {esc(bs_cn)} | 温度 {esc(bt)}°C\n\n"
                f"[b]处理器温度[/b]  {esc(ct)}°C\n"
                f"[b]运行时间[/b]    {esc(uptime)}\n"
                f"[b]内核版本[/b]    {esc(kernel)}\n\n"
                f"[b]磁盘空间[/b]\n  {esc(disk)}\n\n"
                f"[b]网络流量[/b]\n  {esc(net)}\n"
            )
        except Exception as e:
            log_crash(f"系统监控: {traceback.format_exc()}")
            self.info.text = f"[color=ff4444]读取出错: {esc(str(e))}[/color]"


# ============================================================
# 标签页 2：进程管理
# ============================================================

class ProcessTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=8, spacing=4, **kwargs)

        ctrl = BoxLayout(size_hint_y=None, height=44, spacing=4)
        rb = Button(
            text="刷新进程", size_hint_x=0.5,
            font_size="13sp", background_color=(0.2, 0.5, 0.8, 1),
        )
        rb.bind(on_press=self.refresh)
        ctrl.add_widget(rb)

        self.sort_btn = Button(
            text="排序:CPU", size_hint_x=0.5,
            font_size="13sp", background_color=(0.3, 0.3, 0.4, 1),
        )
        self.sort_btn.bind(on_press=self.toggle_sort)
        ctrl.add_widget(self.sort_btn)
        self.add_widget(ctrl)

        self.scroll = ScrollView(size_hint=(1, 1))
        self.label = Label(
            size_hint_y=None, text="点击「刷新进程」查看...",
            halign="left", valign="top",
            markup=True, font_size="12sp",
        )
        self.label.bind(
            texture_size=lambda *a: setattr(
                self.label, 'height', self.label.texture_size[1] + 20
            )
        )
        self.scroll.bind(
            width=lambda inst, w: setattr(
                self.label, 'text_size', (w - 8, None)
            )
        )
        self.scroll.add_widget(self.label)
        self.add_widget(self.scroll)

        kill_bar = BoxLayout(size_hint_y=None, height=44, spacing=4)
        self.pid_input = TextInput(
            hint_text="输入 PID 杀进程",
            size_hint_x=0.6, multiline=False, font_size="13sp",
            background_color=(0.15, 0.15, 0.2, 1),
            foreground_color=(1, 1, 1, 1),
        )
        kill_bar.add_widget(self.pid_input)
        kb = Button(
            text="强制结束", size_hint_x=0.4,
            font_size="13sp", background_color=(0.8, 0.2, 0.2, 1),
        )
        kb.bind(on_press=self.kill_proc)
        kill_bar.add_widget(kb)
        self.add_widget(kill_bar)

        self.sort_cpu = True

    def toggle_sort(self, *args):
        self.sort_cpu = not self.sort_cpu
        self.sort_btn.text = "排序:CPU" if self.sort_cpu else "排序:内存"
        self.refresh()

    def refresh(self, *args):
        try:
            output = run_cmd("top -b -n 1 | head -35", root=True)
            if not output or output.startswith("["):
                output = run_cmd("ps -A | head -30", root=True)
            if not output:
                self.label.text = "[color=ffaa00]需要 Root 权限[/color]"
                return

            lines = output.split('\n')
            colored = []
            for i, line in enumerate(lines):
                safe = esc(line)
                if i == 0 or line.startswith(' ') and 'PID' in line.upper():
                    colored.append(f"[color=88ccff][b]{safe}[/b][/color]")
                elif '%' in line:
                    nums = re.findall(r'(\d+)%', line)
                    high = any(int(n) > 50 for n in nums) if nums else False
                    med = any(int(n) > 10 for n in nums) if nums else False
                    if high:
                        colored.append(f"[color=ff4444]{safe}[/color]")
                    elif med:
                        colored.append(f"[color=ffaa00]{safe}[/color]")
                    else:
                        colored.append(safe)
                else:
                    colored.append(safe)
            self.label.text = '\n'.join(colored)
        except Exception as e:
            log_crash(f"进程管理: {traceback.format_exc()}")
            self.label.text = f"[color=ff4444]出错: {esc(str(e))}[/color]"

    def kill_proc(self, *args):
        pid = self.pid_input.text.strip()
        if not pid or not pid.isdigit():
            self.label.text = "[color=ff4444]请输入有效的 PID 数字[/color]"
            return
        result = run_cmd(f"kill -9 {pid}", root=True)
        if "error" in result.lower() or "denied" in result.lower():
            self.label.text = f"[color=ff4444]结束失败: {esc(result)}[/color]"
        else:
            self.label.text = f"[color=44ff44]已强制结束进程 PID {esc(pid)}[/color]"
        self.pid_input.text = ""
        Clock.schedule_once(lambda dt: self.refresh(), 0.5)


# ============================================================
# 标签页 3：Root 终端
# ============================================================

class TerminalTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=8, spacing=4, **kwargs)

        self.scroll = ScrollView(size_hint=(1, 1))
        self.output = Label(
            size_hint_y=None,
            text=(
                "[color=44ff44]Root 终端[/color]\n"
                "[color=888888]所有命令通过 su -c 以 Root 身份执行[/color]\n"
                "[color=888888]==============================[/color]\n"
            ),
            halign="left", valign="top",
            markup=True, font_size="13sp",
        )
        self.output.bind(
            texture_size=lambda *a: setattr(
                self.output, 'height', self.output.texture_size[1] + 20
            )
        )
        self.scroll.bind(
            width=lambda inst, w: setattr(
                self.output, 'text_size', (w - 8, None)
            )
        )
        self.scroll.add_widget(self.output)
        self.add_widget(self.scroll)

        input_bar = BoxLayout(size_hint_y=None, height=48, spacing=4)
        self.cmd_input = TextInput(
            hint_text="# 输入命令...",
            size_hint_x=0.7, multiline=False, font_size="14sp",
            background_color=(0.1, 0.1, 0.15, 1),
            foreground_color=(0.3, 1, 0.3, 1),
        )
        self.cmd_input.bind(on_text_validate=self.exec_cmd)
        input_bar.add_widget(self.cmd_input)

        run_btn = Button(
            text="执行", size_hint_x=0.3, font_size="14sp",
            background_color=(0.2, 0.7, 0.3, 1),
        )
        run_btn.bind(on_press=self.exec_cmd)
        input_bar.add_widget(run_btn)
        self.add_widget(input_bar)

        # 快捷命令 - 全部兼容 Android
        quick_bar = BoxLayout(size_hint_y=None, height=40, spacing=2)
        quick_cmds = [
            ("身份", "id"),
            ("磁盘", "df -h"),
            ("网络", "ip addr show"),
            ("系统", "getprop ro.build.display.id"),
            ("进程", "top -b -n 1 | head -15"),
            ("清屏", "__clear__"),
        ]
        for label, cmd in quick_cmds:
            btn = Button(
                text=label, font_size="11sp",
                background_color=(0.25, 0.25, 0.35, 1),
            )
            btn.cmd_text = cmd
            btn.bind(on_press=self.quick_cmd)
            quick_bar.add_widget(btn)
        self.add_widget(quick_bar)

        self.cwd = "/sdcard"

    def quick_cmd(self, btn):
        if btn.cmd_text == "__clear__":
            self.output.text = "[color=44ff44]已清屏[/color]\n"
            return
        self.cmd_input.text = btn.cmd_text
        self.exec_cmd()

    def exec_cmd(self, *args):
        cmd = self.cmd_input.text.strip()
        if not cmd:
            return
        self.cmd_input.text = ""
        self.output.text += f"\n[color=44ff44]# {esc(cmd)}[/color]\n"

        try:
            if cmd.startswith("cd "):
                target = cmd[3:].strip()
                result = run_cmd(f"cd {target} && pwd", root=True)
                if result and not result.startswith("["):
                    self.cwd = result
                    self.output.text += f"当前目录: {esc(self.cwd)}\n"
                else:
                    self.output.text += f"[color=ff4444]{esc(result)}[/color]\n"
            else:
                full = f"cd {self.cwd} 2>/dev/null; {cmd}"
                result = run_cmd(full, root=True, timeout=15)
                if result:
                    self.output.text += f"{esc(result)}\n"
                else:
                    self.output.text += "[color=888888]（无输出）[/color]\n"
        except Exception as e:
            self.output.text += f"[color=ff4444]{esc(str(e))}[/color]\n"

        Clock.schedule_once(
            lambda dt: setattr(self.scroll, 'scroll_y', 0), 0.1
        )


# ============================================================
# 标签页 4：日志查看
# ============================================================

LOG_PATH = "/sdcard/py_monitor.log"
MAX_LINES = 500


def colorize(line):
    upper = line.upper()
    if "ERROR" in upper or "FATAL" in upper or "EXCEPTION" in upper:
        return f"[color=ff4444]{line}[/color]"
    elif "WARN" in upper:
        return f"[color=ffaa00]{line}[/color]"
    elif "SUCCESS" in upper or "DONE" in upper:
        return f"[color=44ff44]{line}[/color]"
    elif "DEBUG" in upper:
        return f"[color=888888]{line}[/color]"
    return line


class LogViewerTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=8, spacing=4, **kwargs)

        self.status = Label(
            text="等待日志文件...", size_hint_y=None, height=32,
            halign="left", font_size="12sp", color=(0.6, 0.8, 1, 1),
        )
        self.status.bind(
            size=lambda *a: setattr(
                self.status, 'text_size', (self.status.width, None)
            )
        )
        self.add_widget(self.status)

        sb = BoxLayout(size_hint_y=None, height=40, spacing=4)
        self.search = TextInput(
            hint_text="输入关键词过滤...", size_hint_x=0.7,
            multiline=False, font_size="13sp",
            background_color=(0.15, 0.15, 0.2, 1),
            foreground_color=(1, 1, 1, 1),
        )
        sb.add_widget(self.search)
        self.fbtn = Button(
            text="过滤:关", size_hint_x=0.3,
            font_size="13sp", background_color=(0.3, 0.3, 0.4, 1),
        )
        self.fbtn.bind(on_press=self.toggle_filter)
        sb.add_widget(self.fbtn)
        self.add_widget(sb)

        self.scroll = ScrollView(size_hint=(1, 1))
        self.label = Label(
            size_hint_y=None, text="", halign="left", valign="top",
            markup=True, font_size="13sp",
        )
        self.label.bind(
            texture_size=lambda *a: setattr(
                self.label, 'height', self.label.texture_size[1] + 20
            )
        )
        self.scroll.bind(
            width=lambda inst, w: setattr(
                self.label, 'text_size', (w - 8, None)
            )
        )
        self.scroll.add_widget(self.label)
        self.add_widget(self.scroll)

        bb = BoxLayout(size_hint_y=None, height=44, spacing=4)
        self.pbtn = Button(
            text="暂停", size_hint_x=0.5,
            font_size="14sp", background_color=(0.2, 0.5, 0.8, 1),
        )
        self.pbtn.bind(on_press=self.toggle_pause)
        bb.add_widget(self.pbtn)
        sb2 = Button(
            text="回到底部", size_hint_x=0.5,
            font_size="14sp", background_color=(0.3, 0.6, 0.3, 1),
        )
        sb2.bind(on_press=lambda x: setattr(self.scroll, 'scroll_y', 0))
        bb.add_widget(sb2)
        self.add_widget(bb)

        self.paused = False
        self.filter_on = False
        self.last_mt = 0
        Clock.schedule_interval(self.update, 0.5)

    def toggle_pause(self, *args):
        self.paused = not self.paused
        self.pbtn.text = "继续" if self.paused else "暂停"
        self.pbtn.background_color = (
            (0.8, 0.4, 0.2, 1) if self.paused else (0.2, 0.5, 0.8, 1)
        )

    def toggle_filter(self, *args):
        self.filter_on = not self.filter_on
        self.fbtn.text = "过滤:开" if self.filter_on else "过滤:关"
        self.fbtn.background_color = (
            (0.2, 0.7, 0.3, 1) if self.filter_on else (0.3, 0.3, 0.4, 1)
        )
        self.last_mt = 0

    def update(self, dt):
        if self.paused:
            return
        try:
            if not os.path.exists(LOG_PATH):
                self.label.text = (
                    f"[color=ffaa00]日志文件不存在[/color]\n"
                    f"路径：{esc(LOG_PATH)}"
                )
                self.status.text = "文件未找到"
                return

            st = os.stat(LOG_PATH)
            if st.st_mtime == self.last_mt:
                return
            self.last_mt = st.st_mtime

            lines = tail_read(LOG_PATH, MAX_LINES)
            if not lines:
                self.label.text = "[color=888888]日志文件为空[/color]"
                return

            kw = self.search.text.strip()
            if self.filter_on and kw:
                lines = [l for l in lines if kw.lower() in l.lower()]

            display = []
            for line in lines:
                line = line.rstrip('\n\r')
                safe = esc(line)
                colored = colorize(safe)
                if kw and kw.lower() in line.lower():
                    colored = f"[color=00ffff]>[/color] {colored}"
                display.append(colored)

            self.label.text = '\n'.join(display)

            t = time.strftime("%H:%M:%S", time.localtime(st.st_mtime))
            sz = format_size(st.st_size)
            fi = f" | 过滤后 {len(display)} 行" if (self.filter_on and kw) else ""
            self.status.text = f"{sz} | {len(lines)} 行{fi} | 更新于 {t}"

            Clock.schedule_once(
                lambda dt: setattr(self.scroll, 'scroll_y', 0), 0.1
            )
        except PermissionError:
            self.label.text = "[color=ff4444]权限不足，请授权文件访问[/color]"
        except Exception as e:
            log_crash(f"日志查看: {traceback.format_exc()}")
            self.label.text = f"[color=ff4444]出错: {esc(str(e))}[/color]"


# ============================================================
# 标签页 5：系统日志（Logcat）
# ============================================================

class LogcatTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=8, spacing=4, **kwargs)

        fb = BoxLayout(size_hint_y=None, height=40, spacing=4)
        self.log_level = "I"
        self.lvbtns = []
        for lv in ["V", "D", "I", "W", "E"]:
            btn = Button(
                text=lv, font_size="13sp",
                background_color=(
                    (0.2, 0.5, 0.8, 1) if lv == "I"
                    else (0.3, 0.3, 0.4, 1)
                ),
            )
            btn.lv = lv
            btn.bind(on_press=self.set_lv)
            fb.add_widget(btn)
            self.lvbtns.append(btn)
        self.add_widget(fb)

        tb = BoxLayout(size_hint_y=None, height=40, spacing=4)
        self.tag_input = TextInput(
            hint_text="过滤标签（留空显示全部）",
            size_hint_x=1, multiline=False, font_size="13sp",
            background_color=(0.15, 0.15, 0.2, 1),
            foreground_color=(1, 1, 1, 1),
        )
        tb.add_widget(self.tag_input)
        self.add_widget(tb)

        self.scroll = ScrollView(size_hint=(1, 1))
        self.label = Label(
            size_hint_y=None, text="点击「捕获」按钮开始...",
            halign="left", valign="top",
            markup=True, font_size="11sp",
        )
        self.label.bind(
            texture_size=lambda *a: setattr(
                self.label, 'height', self.label.texture_size[1] + 20
            )
        )
        self.scroll.bind(
            width=lambda inst, w: setattr(
                self.label, 'text_size', (w - 8, None)
            )
        )
        self.scroll.add_widget(self.label)
        self.add_widget(self.scroll)

        ctrl = BoxLayout(size_hint_y=None, height=44, spacing=4)
        cb = Button(
            text="捕获日志", size_hint_x=0.3,
            font_size="13sp", background_color=(0.2, 0.7, 0.3, 1),
        )
        cb.bind(on_press=self.capture)
        ctrl.add_widget(cb)

        clb = Button(
            text="清空", size_hint_x=0.2,
            font_size="13sp", background_color=(0.5, 0.3, 0.3, 1),
        )
        clb.bind(on_press=lambda x: setattr(self.label, 'text', ''))
        ctrl.add_widget(clb)

        svb = Button(
            text="保存", size_hint_x=0.2,
            font_size="13sp", background_color=(0.3, 0.3, 0.5, 1),
        )
        svb.bind(on_press=self.save)
        ctrl.add_widget(svb)

        lb = Button(
            text="实时", size_hint_x=0.3,
            font_size="13sp", background_color=(0.6, 0.4, 0.2, 1),
        )
        lb.bind(on_press=self.toggle_live)
        ctrl.add_widget(lb)
        self.add_widget(ctrl)

        self.live_ev = None

    def set_lv(self, btn):
        self.log_level = btn.lv
        for b in self.lvbtns:
            b.background_color = (
                (0.2, 0.5, 0.8, 1) if b.lv == self.log_level
                else (0.3, 0.3, 0.4, 1)
            )

    def color_lc(self, line):
        if ' E ' in line or '/E ' in line:
            return f"[color=ff4444]{line}[/color]"
        elif ' W ' in line or '/W ' in line:
            return f"[color=ffaa00]{line}[/color]"
        elif ' I ' in line or '/I ' in line:
            return f"[color=44ff44]{line}[/color]"
        elif ' D ' in line or '/D ' in line:
            return f"[color=888888]{line}[/color]"
        return line

    def capture(self, *args):
        try:
            self.label.text = "[color=888888]正在捕获...[/color]\n"
            tag = self.tag_input.text.strip()
            if tag:
                cmd = f"logcat -d -v brief -s {tag}:{self.log_level} | tail -200"
            else:
                cmd = f"logcat -d -v brief *:{self.log_level} | tail -200"

            output = run_cmd(cmd, root=True, timeout=10)
            if output and not output.startswith("["):
                lines = output.split('\n')
                colored = [self.color_lc(esc(l)) for l in lines]
                self.label.text = '\n'.join(colored)
            else:
                self.label.text = f"[color=ffaa00]无输出（级别={esc(self.log_level)}）[/color]"
            Clock.schedule_once(
                lambda dt: setattr(self.scroll, 'scroll_y', 0), 0.1
            )
        except Exception as e:
            self.label.text = f"[color=ff4444]出错: {esc(str(e))}[/color]"

    def toggle_live(self, *args):
        if self.live_ev:
            self.live_ev.cancel()
            self.live_ev = None
            self.label.text += "\n[color=ffaa00]实时模式已关闭[/color]"
        else:
            self.live_ev = Clock.schedule_interval(
                lambda dt: self.capture(), 2
            )
            self.label.text = "[color=44ff44]实时模式已开启（每2秒刷新）[/color]\n"

    def save(self, *args):
        try:
            path = "/sdcard/logcat_dump.txt"
            clean = re.sub(r'\[/?color[^\]]*\]', '', self.label.text)
            clean = clean.replace('&amp;', '&').replace('&bl;', '[').replace('&br;', ']')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(clean)
            self.label.text += f"\n[color=44ff44]已保存到 {esc(path)}[/color]"
        except Exception as e:
            self.label.text += f"\n[color=ff4444]保存失败: {esc(str(e))}[/color]"


# ============================================================
# 主程序（防崩溃）
# ============================================================

class MonitorApp(App):
    def build(self):
        try:
            Window.clearcolor = (0.08, 0.08, 0.12, 1)
            self.title = "Python Monitor"

            request_android_perms()

            tp = TabbedPanel(do_default_tab=False)

            tabs = [
                ("监控", SystemMonitorTab()),
                ("进程", ProcessTab()),
                ("终端", TerminalTab()),
                ("日志", LogViewerTab()),
                ("系统", LogcatTab()),
            ]

            for title, content in tabs:
                tab = TabbedPanelItem(text=title, font_size="13sp")
                tab.add_widget(content)
                tp.add_widget(tab)

            return tp

        except Exception as e:
            log_crash(f"启动崩溃: {traceback.format_exc()}")
            return Label(
                text=f"启动出错：\n{e}\n\n请查看 {CRASH_LOG}",
                halign="center", valign="middle",
            )


if __name__ == "__main__":
    try:
        MonitorApp().run()
    except Exception as e:
        log_crash(f"致命错误: {traceback.format_exc()}")