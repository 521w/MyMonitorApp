"""
Python Monitor v3.0 - Root Enhanced Edition
5 Tabs: System Monitor / Process Manager / Root Terminal / Log Viewer / Logcat
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

try:
    from android.permissions import request_permissions, Permission
    ANDROID = True
except ImportError:
    ANDROID = False


# ============================================================
# Utility Functions
# ============================================================

def run_cmd(cmd, root=False, timeout=5):
    """Run a shell command, optionally as root via su"""
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
        return out if out else err
    except subprocess.TimeoutExpired:
        return "[命令超时]"
    except Exception as e:
        return f"[错误] {e}"


def read_file_safe(path):
    """Safely read a file, return empty string on failure"""
    try:
        with open(path, 'r') as f:
            return f.read().strip()
    except Exception:
        return ""


def tail_read(filepath, max_lines=500):
    """Efficiently read last N lines by seeking from end"""
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


def escape_markup(text):
    """Escape Kivy markup special characters"""
    return text.replace('&', '&amp;').replace('[', '&bl;').replace(']', '&br;')


def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


# ============================================================
# Tab 1: System Monitor
# ============================================================

class SystemMonitorTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=8, spacing=6, **kwargs)

        scroll = ScrollView(size_hint=(1, 1))
        self.info_label = Label(
            text="正在读取系统信息...",
            size_hint_y=None, height=500,
            halign="left", valign="top",
            markup=True, font_size="14sp",
        )
        self.info_label.bind(
            texture_size=lambda *a: setattr(
                self.info_label, 'height', self.info_label.texture_size[1] + 40
            )
        )
        scroll.bind(
            width=lambda inst, w: setattr(
                self.info_label, 'text_size', (w - 16, None)
            )
        )
        scroll.add_widget(self.info_label)
        self.add_widget(scroll)

        btn_bar = BoxLayout(size_hint_y=None, height=48, spacing=4)
        refresh_btn = Button(
            text="手动刷新", font_size="14sp",
            background_color=(0.2, 0.5, 0.8, 1),
        )
        refresh_btn.bind(on_press=lambda x: self.update_info(0))
        btn_bar.add_widget(refresh_btn)
        self.add_widget(btn_bar)

        # Store previous CPU reading for delta calculation
        self.prev_cpu = None
        Clock.schedule_interval(self.update_info, 3)

    def _read_cpu_sample(self):
        line = read_file_safe('/proc/stat')
        if not line:
            return None
        first = line.split('\n')[0].split()
        if len(first) < 5:
            return None
        vals = list(map(int, first[1:8] if len(first) >= 8 else first[1:]))
        return sum(vals), vals[3]  # total, idle

    def update_info(self, dt):
        try:
            # --- CPU ---
            s1 = self._read_cpu_sample()
            if s1 and self.prev_cpu:
                total_d = s1[0] - self.prev_cpu[0]
                idle_d = s1[1] - self.prev_cpu[1]
                cpu = round((1 - idle_d / total_d) * 100, 1) if total_d > 0 else 0
            else:
                cpu = 0
            self.prev_cpu = s1
            cpu_color = "44ff44" if cpu < 50 else ("ffaa00" if cpu < 80 else "ff4444")

            # --- Memory ---
            meminfo = {}
            for line in read_file_safe('/proc/meminfo').split('\n'):
                parts = line.split()
                if len(parts) >= 2:
                    meminfo[parts[0].rstrip(':')] = int(parts[1])
            mem_total = meminfo.get('MemTotal', 1)
            mem_avail = meminfo.get('MemAvailable', meminfo.get('MemFree', 0))
            mem_used = mem_total - mem_avail
            mem_pct = round(mem_used / mem_total * 100, 1) if mem_total > 0 else 0
            mem_color = "44ff44" if mem_pct < 60 else ("ffaa00" if mem_pct < 85 else "ff4444")

            # --- Battery ---
            bat_base = '/sys/class/power_supply/battery'
            bat_level = read_file_safe(f'{bat_base}/capacity') or '?'
            bat_status = read_file_safe(f'{bat_base}/status') or '?'
            bat_temp_raw = read_file_safe(f'{bat_base}/temp')
            bat_temp = f"{int(bat_temp_raw) / 10:.1f}" if bat_temp_raw.isdigit() else '?'
            status_cn = {
                'Charging': '充电中', 'Discharging': '放电中',
                'Full': '已充满', 'Not charging': '未充电',
            }.get(bat_status, bat_status)

            # --- CPU Temp ---
            cpu_temp = '?'
            for p in ['/sys/class/thermal/thermal_zone0/temp',
                       '/sys/devices/virtual/thermal/thermal_zone0/temp']:
                val = read_file_safe(p)
                if val and val.isdigit():
                    t = int(val)
                    cpu_temp = f"{t / 1000:.1f}" if t > 1000 else f"{t:.1f}"
                    break

            # --- Uptime ---
            up_raw = read_file_safe('/proc/uptime')
            if up_raw:
                secs = int(float(up_raw.split()[0]))
                uptime = f"{secs // 3600}h {(secs % 3600) // 60}m"
            else:
                uptime = '?'

            # --- Kernel ---
            kver = read_file_safe('/proc/version')
            kernel = kver.split()[2] if kver and len(kver.split()) > 2 else '?'

            # --- Disk ---
            disk_out = run_cmd("df -h /data /sdcard 2>/dev/null | tail -2")

            # --- Network ---
            net_out = run_cmd(
                "cat /proc/net/dev | awk 'NR>2{print $1, $2, $10}'",
            )

            def bar(pct, w=20):
                f = int(pct / 100 * w)
                return '█' * f + '░' * (w - f)

            self.info_label.text = (
                f"[b][color=88ccff]━━━ 系统监控仪表盘 ━━━[/color][/b]\n\n"

                f"[b]CPU[/b]\n"
                f"[color={cpu_color}]  {bar(cpu)} {cpu}%[/color]\n\n"

                f"[b]内存[/b]\n"
                f"[color={mem_color}]  {bar(mem_pct)} {mem_pct}%[/color]\n"
                f"  {mem_used // 1024}MB / {mem_total // 1024}MB"
                f" (可用 {mem_avail // 1024}MB)\n\n"

                f"[b]电池[/b]\n"
                f"  电量 {bat_level}% | {status_cn} | 温度 {bat_temp}°C\n\n"

                f"[b]温度[/b]\n"
                f"  CPU: {cpu_temp}°C\n\n"

                f"[b]运行时间[/b]  {uptime}\n"
                f"[b]内核[/b]  {kernel}\n\n"

                f"[b]磁盘[/b]\n  {disk_out}\n\n"

                f"[b]网络流量[/b] (接口 接收 发送)\n  {net_out}\n"
            )

        except Exception as e:
            self.info_label.text = f"[color=ff4444]读取出错: {e}[/color]"


# ============================================================
# Tab 2: Process Manager
# ============================================================

class ProcessTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=8, spacing=4, **kwargs)

        ctrl = BoxLayout(size_hint_y=None, height=44, spacing=4)
        refresh_btn = Button(
            text="刷新进程", size_hint_x=0.5,
            font_size="13sp", background_color=(0.2, 0.5, 0.8, 1),
        )
        refresh_btn.bind(on_press=self.refresh_processes)
        ctrl.add_widget(refresh_btn)

        self.sort_btn = Button(
            text="排序:CPU", size_hint_x=0.5,
            font_size="13sp", background_color=(0.3, 0.3, 0.4, 1),
        )
        self.sort_btn.bind(on_press=self.toggle_sort)
        ctrl.add_widget(self.sort_btn)
        self.add_widget(ctrl)

        self.scroll = ScrollView(size_hint=(1, 1))
        self.proc_label = Label(
            size_hint_y=None, text="点击「刷新进程」查看...",
            halign="left", valign="top",
            markup=True, font_size="12sp",
        )
        self.proc_label.bind(
            texture_size=lambda *a: setattr(
                self.proc_label, 'height', self.proc_label.texture_size[1] + 20
            )
        )
        self.scroll.bind(
            width=lambda inst, w: setattr(
                self.proc_label, 'text_size', (w - 8, None)
            )
        )
        self.scroll.add_widget(self.proc_label)
        self.add_widget(self.scroll)

        kill_bar = BoxLayout(size_hint_y=None, height=44, spacing=4)
        self.pid_input = TextInput(
            hint_text="输入 PID 杀进程",
            size_hint_x=0.6, multiline=False, font_size="13sp",
            background_color=(0.15, 0.15, 0.2, 1),
            foreground_color=(1, 1, 1, 1),
        )
        kill_bar.add_widget(self.pid_input)
        kill_btn = Button(
            text="Kill -9", size_hint_x=0.4,
            font_size="13sp", background_color=(0.8, 0.2, 0.2, 1),
        )
        kill_btn.bind(on_press=self.kill_process)
        kill_bar.add_widget(kill_btn)
        self.add_widget(kill_bar)

        self.sort_by_cpu = True

    def toggle_sort(self, *args):
        self.sort_by_cpu = not self.sort_by_cpu
        self.sort_btn.text = "排序:CPU" if self.sort_by_cpu else "排序:MEM"
        self.refresh_processes()

    def refresh_processes(self, *args):
        key = "pcpu" if self.sort_by_cpu else "pmem"
        output = run_cmd(
            f"ps -eo pid,user,%cpu,%mem,comm --sort=-{key} | head -30",
            root=True,
        )
        if not output:
            self.proc_label.text = "[color=ffaa00]需要 Root 权限[/color]"
            return

        lines = output.split('\n')
        colored = []
        for i, line in enumerate(lines):
            if i == 0:
                colored.append(f"[color=88ccff][b]{line}[/b][/color]")
            else:
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        v = float(parts[2])
                        if v > 50:
                            colored.append(f"[color=ff4444]{line}[/color]")
                        elif v > 10:
                            colored.append(f"[color=ffaa00]{line}[/color]")
                        else:
                            colored.append(line)
                    except ValueError:
                        colored.append(line)
                else:
                    colored.append(line)
        self.proc_label.text = '\n'.join(colored)

    def kill_process(self, *args):
        pid = self.pid_input.text.strip()
        if not pid or not pid.isdigit():
            self.proc_label.text = "[color=ff4444]请输入有效的 PID 数字[/color]"
            return
        result = run_cmd(f"kill -9 {pid}", root=True)
        msg = f"[color=44ff44]已发送 kill -9 到 PID {pid}[/color]"
        if "error" in result.lower() or "denied" in result.lower():
            msg = f"[color=ff4444]Kill 失败: {result}[/color]"
        self.proc_label.text = msg + "\n\n"
        self.pid_input.text = ""
        Clock.schedule_once(lambda dt: self.refresh_processes(), 0.5)


# ============================================================
# Tab 3: Root Terminal
# ============================================================

class TerminalTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=8, spacing=4, **kwargs)

        self.scroll = ScrollView(size_hint=(1, 1))
        self.output = Label(
            size_hint_y=None,
            text=(
                "[color=44ff44]Root Terminal[/color]\n"
                "[color=888888]所有命令通过 su -c 以 root 执行[/color]\n"
                "[color=888888]━━━━━━━━━━━━━━━━━━━━━━━━━━[/color]\n"
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
        self.cmd_input.bind(on_text_validate=self.execute_cmd)
        input_bar.add_widget(self.cmd_input)

        run_btn = Button(
            text="执行", size_hint_x=0.3, font_size="14sp",
            background_color=(0.2, 0.7, 0.3, 1),
        )
        run_btn.bind(on_press=self.execute_cmd)
        input_bar.add_widget(run_btn)
        self.add_widget(input_bar)

        # Quick command buttons
        quick_bar = BoxLayout(size_hint_y=None, height=40, spacing=2)
        quick_cmds = [
            ("id", "id"),
            ("磁盘", "df -h"),
            ("网络", "ip addr show"),
            ("连接", "netstat -tlnp"),
            ("进程树", "pstree -p | head -30"),
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
        self.execute_cmd()

    def execute_cmd(self, *args):
        cmd = self.cmd_input.text.strip()
        if not cmd:
            return
        self.cmd_input.text = ""

        self.output.text += f"\n[color=44ff44]# {escape_markup(cmd)}[/color]\n"

        if cmd.startswith("cd "):
            target = cmd[3:].strip()
            result = run_cmd(f"cd {target} && pwd", root=True)
            if result and not result.startswith("["):
                self.cwd = result
                self.output.text += f"目录: {self.cwd}\n"
            else:
                self.output.text += f"[color=ff4444]{result}[/color]\n"
        else:
            full_cmd = f"cd {self.cwd} 2>/dev/null; {cmd}"
            result = run_cmd(full_cmd, root=True, timeout=15)
            if result:
                safe = escape_markup(result)
                self.output.text += f"{safe}\n"
            else:
                self.output.text += "[color=888888](无输出)[/color]\n"

        Clock.schedule_once(
            lambda dt: setattr(self.scroll, 'scroll_y', 0), 0.1
        )


# ============================================================
# Tab 4: Log Viewer (Enhanced)
# ============================================================

LOG_PATH = "/sdcard/py_monitor.log"
MAX_LINES = 500


def colorize_line(line):
    upper = line.upper()
    if "ERROR" in upper or "FATAL" in upper or "EXCEPTION" in upper:
        return f"[color=ff4444]{line}[/color]"
    elif "WARN" in upper:
        return f"[color=ffaa00]{line}[/color]"
    elif "SUCCESS" in upper or " OK " in upper or "DONE" in upper:
        return f"[color=44ff44]{line}[/color]"
    elif "DEBUG" in upper:
        return f"[color=888888]{line}[/color]"
    return line


class LogViewerTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=8, spacing=4, **kwargs)

        self.status = Label(
            text="等待日志...", size_hint_y=None, height=32,
            halign="left", font_size="12sp", color=(0.6, 0.8, 1, 1),
        )
        self.status.bind(
            size=lambda *a: setattr(
                self.status, 'text_size', (self.status.width, None)
            )
        )
        self.add_widget(self.status)

        search_bar = BoxLayout(size_hint_y=None, height=40, spacing=4)
        self.search_input = TextInput(
            hint_text="过滤关键词...", size_hint_x=0.7,
            multiline=False, font_size="13sp",
            background_color=(0.15, 0.15, 0.2, 1),
            foreground_color=(1, 1, 1, 1),
        )
        search_bar.add_widget(self.search_input)
        self.filter_btn = Button(
            text="过滤:关", size_hint_x=0.3,
            font_size="13sp", background_color=(0.3, 0.3, 0.4, 1),
        )
        self.filter_btn.bind(on_press=self.toggle_filter)
        search_bar.add_widget(self.filter_btn)
        self.add_widget(search_bar)

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

        bottom = BoxLayout(size_hint_y=None, height=44, spacing=4)
        self.pause_btn = Button(
            text="暂停", size_hint_x=0.5,
            font_size="14sp", background_color=(0.2, 0.5, 0.8, 1),
        )
        self.pause_btn.bind(on_press=self.toggle_pause)
        bottom.add_widget(self.pause_btn)
        scroll_btn = Button(
            text="底部", size_hint_x=0.5,
            font_size="14sp", background_color=(0.3, 0.6, 0.3, 1),
        )
        scroll_btn.bind(
            on_press=lambda x: setattr(self.scroll, 'scroll_y', 0)
        )
        bottom.add_widget(scroll_btn)
        self.add_widget(bottom)

        self.paused = False
        self.filter_on = False
        self.last_mtime = 0
        Clock.schedule_interval(self.update_log, 0.5)

    def toggle_pause(self, *args):
        self.paused = not self.paused
        self.pause_btn.text = "继续" if self.paused else "暂停"
        self.pause_btn.background_color = (
            (0.8, 0.4, 0.2, 1) if self.paused else (0.2, 0.5, 0.8, 1)
        )

    def toggle_filter(self, *args):
        self.filter_on = not self.filter_on
        self.filter_btn.text = "过滤:开" if self.filter_on else "过滤:关"
        self.filter_btn.background_color = (
            (0.2, 0.7, 0.3, 1) if self.filter_on else (0.3, 0.3, 0.4, 1)
        )
        self.last_mtime = 0

    def update_log(self, dt):
        if self.paused:
            return
        try:
            if not os.path.exists(LOG_PATH):
                self.label.text = (
                    f"[color=ffaa00]日志文件不存在[/color]\n{LOG_PATH}"
                )
                self.status.text = "文件未找到"
                return

            stat = os.stat(LOG_PATH)
            if stat.st_mtime == self.last_mtime:
                return
            self.last_mtime = stat.st_mtime

            lines = tail_read(LOG_PATH, MAX_LINES)
            if not lines:
                self.label.text = "[color=888888]日志为空[/color]"
                return

            keyword = self.search_input.text.strip()
            if self.filter_on and keyword:
                lines = [l for l in lines if keyword.lower() in l.lower()]

            display = []
            for line in lines:
                line = line.rstrip('\n\r')
                colored = colorize_line(line)
                if keyword and keyword.lower() in line.lower():
                    colored = f"[color=00ffff]>[/color] {colored}"
                display.append(colored)

            self.label.text = '\n'.join(display)

            t = time.strftime("%H:%M:%S", time.localtime(stat.st_mtime))
            sz = format_size(stat.st_size)
            fi = f" | 过滤后{len(display)}行" if (self.filter_on and keyword) else ""
            self.status.text = f"{sz} | {len(lines)}行{fi} | {t}"

            Clock.schedule_once(
                lambda dt: setattr(self.scroll, 'scroll_y', 0), 0.1
            )
        except PermissionError:
            self.label.text = "[color=ff4444]权限不足，请授权文件访问[/color]"
        except Exception as e:
            self.label.text = f"[color=ff4444]出错: {e}[/color]"


# ============================================================
# Tab 5: Logcat Viewer
# ============================================================

class LogcatTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=8, spacing=4, **kwargs)

        filter_bar = BoxLayout(size_hint_y=None, height=40, spacing=4)
        self.log_level = "I"
        self.level_btns = []
        for lv in ["V", "D", "I", "W", "E"]:
            btn = Button(
                text=lv, font_size="13sp",
                background_color=(
                    (0.2, 0.5, 0.8, 1) if lv == "I"
                    else (0.3, 0.3, 0.4, 1)
                ),
            )
            btn.lv = lv
            btn.bind(on_press=self.set_level)
            filter_bar.add_widget(btn)
            self.level_btns.append(btn)
        self.add_widget(filter_bar)

        # Tag filter
        tag_bar = BoxLayout(size_hint_y=None, height=40, spacing=4)
        self.tag_input = TextInput(
            hint_text="过滤 TAG（留空显示全部）",
            size_hint_x=1, multiline=False, font_size="13sp",
            background_color=(0.15, 0.15, 0.2, 1),
            foreground_color=(1, 1, 1, 1),
        )
        tag_bar.add_widget(self.tag_input)
        self.add_widget(tag_bar)

        self.scroll = ScrollView(size_hint=(1, 1))
        self.logcat_label = Label(
            size_hint_y=None,
            text="点击「捕获」按钮开始...",
            halign="left", valign="top",
            markup=True, font_size="11sp",
        )
        self.logcat_label.bind(
            texture_size=lambda *a: setattr(
                self.logcat_label, 'height',
                self.logcat_label.texture_size[1] + 20
            )
        )
        self.scroll.bind(
            width=lambda inst, w: setattr(
                self.logcat_label, 'text_size', (w - 8, None)
            )
        )
        self.scroll.add_widget(self.logcat_label)
        self.add_widget(self.scroll)

        ctrl = BoxLayout(size_hint_y=None, height=44, spacing=4)
        cap_btn = Button(
            text="捕获 Logcat", size_hint_x=0.4,
            font_size="13sp", background_color=(0.2, 0.7, 0.3, 1),
        )
        cap_btn.bind(on_press=self.capture_logcat)
        ctrl.add_widget(cap_btn)

        clear_btn = Button(
            text="清空", size_hint_x=0.2,
            font_size="13sp", background_color=(0.5, 0.3, 0.3, 1),
        )
        clear_btn.bind(
            on_press=lambda x: setattr(self.logcat_label, 'text', '')
        )
        ctrl.add_widget(clear_btn)

        save_btn = Button(
            text="保存", size_hint_x=0.2,
            font_size="13sp", background_color=(0.3, 0.3, 0.5, 1),
        )
        save_btn.bind(on_press=self.save_logcat)
        ctrl.add_widget(save_btn)

        live_btn = Button(
            text="实时", size_hint_x=0.2,
            font_size="13sp", background_color=(0.6, 0.4, 0.2, 1),
        )
        live_btn.bind(on_press=self.toggle_live)
        ctrl.add_widget(live_btn)
        self.add_widget(ctrl)

        self.live_event = None

    def set_level(self, btn):
        self.log_level = btn.lv
        for b in self.level_btns:
            b.background_color = (
                (0.2, 0.5, 0.8, 1) if b.lv == self.log_level
                else (0.3, 0.3, 0.4, 1)
            )

    def colorize_logcat(self, line):
        if ' E ' in line or ' E/' in line:
            return f"[color=ff4444]{line}[/color]"
        elif ' W ' in line or ' W/' in line:
            return f"[color=ffaa00]{line}[/color]"
        elif ' I ' in line or ' I/' in line:
            return f"[color=44ff44]{line}[/color]"
        elif ' D ' in line or ' D/' in line:
            return f"[color=888888]{line}[/color]"
        return line

    def capture_logcat(self, *args):
        self.logcat_label.text = "[color=888888]正在捕获...[/color]\n"

        tag = self.tag_input.text.strip()
        if tag:
            cmd = f"logcat -d -v brief -s {tag}:{self.log_level} | tail -200"
        else:
            cmd = f"logcat -d -v brief *:{self.log_level} | tail -200"

        output = run_cmd(cmd, root=True, timeout=10)

        if output and not output.startswith("["):
            lines = output.split('\n')
            safe_lines = [escape_markup(l) for l in lines]
            colored = [self.colorize_logcat(l) for l in safe_lines]
            self.logcat_label.text = '\n'.join(colored)
        else:
            self.logcat_label.text = (
                f"[color=ffaa00]无输出 (Level={self.log_level})[/color]"
            )
        Clock.schedule_once(
            lambda dt: setattr(self.scroll, 'scroll_y', 0), 0.1
        )

    def toggle_live(self, *args):
        if self.live_event:
            self.live_event.cancel()
            self.live_event = None
            self.logcat_label.text += (
                "\n[color=ffaa00]实时模式已关闭[/color]"
            )
        else:
            self.live_event = Clock.schedule_interval(
                lambda dt: self.capture_logcat(), 2
            )
            self.logcat_label.text = "[color=44ff44]实时模式已开启（每2秒刷新）[/color]\n"

    def save_logcat(self, *args):
        try:
            path = "/sdcard/logcat_dump.txt"
            clean = re.sub(r'\[/?color[^\]]*\]', '', self.logcat_label.text)
            clean = clean.replace('&amp;', '&').replace('&bl;', '[').replace('&br;', ']')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(clean)
            self.logcat_label.text += (
                f"\n[color=44ff44]已保存到 {path}[/color]"
            )
        except Exception as e:
            self.logcat_label.text += (
                f"\n[color=ff4444]保存失败: {e}[/color]"
            )


# ============================================================
# Main App
# ============================================================

class MonitorApp(App):
    def build(self):
        Window.clearcolor = (0.08, 0.08, 0.12, 1)
        self.title = "Python Monitor"

        if ANDROID:
            request_permissions([Permission.MANAGE_EXTERNAL_STORAGE])

        tp = TabbedPanel(
            do_default_tab=False,
            tab_width=Window.width / 5,
        )

        tabs = [
            ("监控", SystemMonitorTab()),
            ("进程", ProcessTab()),
            ("终端", TerminalTab()),
            ("日志", LogViewerTab()),
            ("Logcat", LogcatTab()),
        ]

        for title, content in tabs:
            tab = TabbedPanelItem(text=title, font_size="13sp")
            tab.add_widget(content)
            tp.add_widget(tab)

        return tp


if __name__ == "__main__":
    MonitorApp().run()