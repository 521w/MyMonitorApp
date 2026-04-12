"""
Python Monitor v1.0
实时日志查看器 - 增强版
功能：自动滚底、暂停/继续、关键词过滤、日志着色、状态栏、高效读取
"""

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.core.window import Window
import os
import time

# Android 权限
try:
    from android.permissions import request_permissions, Permission
    ANDROID = True
except ImportError:
    ANDROID = False

LOG_PATH = "/sdcard/py_monitor.log"
MAX_LINES = 500          # 最大显示行数
REFRESH_INTERVAL = 0.5   # 刷新间隔（秒）


def colorize_line(line):
    """根据日志级别给单行文本上色（Kivy markup）"""
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


def format_size(size_bytes):
    """文件大小格式化"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def tail_read(filepath, max_lines=500):
    """高效读取文件尾部，大文件不会卡"""
    try:
        file_size = os.path.getsize(filepath)
        # 预估每行 200 字节，多读一些确保够
        read_size = min(file_size, max_lines * 200)

        with open(filepath, "rb") as f:
            if read_size < file_size:
                f.seek(-read_size, 2)  # 从文件末尾往前 seek
            raw = f.read()

        text = raw.decode("utf-8", errors="replace")
        lines = text.splitlines(keepends=True)

        # 如果是 seek 过来的，第一行可能不完整，丢掉
        if read_size < file_size and len(lines) > 1:
            lines = lines[1:]

        return lines[-max_lines:]
    except Exception:
        return []


class LogView(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=2, padding=4, **kwargs)

        # ===== 状态栏 =====
        self.status_label = Label(
            text="等待日志文件...",
            size_hint_y=None,
            height=36,
            halign="left",
            valign="middle",
            color=(0.6, 0.8, 1, 1),
            font_size="13sp",
        )
        self.status_label.bind(size=lambda *a: setattr(
            self.status_label, "text_size", (self.status_label.width, None)
        ))
        self.add_widget(self.status_label)

        # ===== 搜索栏 =====
        search_bar = BoxLayout(size_hint_y=None, height=44, spacing=4)

        self.search_input = TextInput(
            hint_text="输入关键词过滤...",
            size_hint_x=0.7,
            multiline=False,
            font_size="14sp",
            background_color=(0.15, 0.15, 0.2, 1),
            foreground_color=(1, 1, 1, 1),
            hint_text_color=(0.5, 0.5, 0.5, 1),
        )
        search_bar.add_widget(self.search_input)

        self.filter_btn = Button(
            text="过滤:关",
            size_hint_x=0.3,
            font_size="13sp",
            background_color=(0.3, 0.3, 0.4, 1),
        )
        self.filter_btn.bind(on_press=self.toggle_filter)
        search_bar.add_widget(self.filter_btn)

        self.add_widget(search_bar)

        # ===== 日志显示区 =====
        self.scroll = ScrollView(size_hint=(1, 1))
        self.label = Label(
            size_hint_y=None,
            text="",
            halign="left",
            valign="top",
            markup=True,
            font_size="13sp",
        )
        self.label.bind(texture_size=self._update_label_height)
        self.scroll.bind(width=self._update_text_width)
        self.scroll.add_widget(self.label)
        self.add_widget(self.scroll)

        # ===== 底部工具栏 =====
        bottom_bar = BoxLayout(size_hint_y=None, height=48, spacing=4)

        self.pause_btn = Button(
            text="⏸ 暂停",
            size_hint_x=0.5,
            font_size="14sp",
            background_color=(0.2, 0.5, 0.8, 1),
        )
        self.pause_btn.bind(on_press=self.toggle_pause)
        bottom_bar.add_widget(self.pause_btn)

        self.scroll_btn = Button(
            text="↓ 滚到底部",
            size_hint_x=0.5,
            font_size="14sp",
            background_color=(0.3, 0.6, 0.3, 1),
        )
        self.scroll_btn.bind(on_press=self.scroll_to_bottom)
        bottom_bar.add_widget(self.scroll_btn)

        self.add_widget(bottom_bar)

        # ===== 状态变量 =====
        self.paused = False
        self.filter_on = False
        self.last_mtime = 0       # 上次文件修改时间（避免无变化时重复读取）
        self.auto_scroll = True   # 是否自动滚到底部

        # 监听用户手动滚动
        self.scroll.bind(scroll_y=self._on_user_scroll)

        # 请求权限后启动轮询
        if ANDROID:
            request_permissions(
                [Permission.MANAGE_EXTERNAL_STORAGE],
                callback=self._perm_callback,
            )
        else:
            self._start_polling()

    # ---------- 权限与启动 ----------

    def _perm_callback(self, permissions, grant_results):
        Clock.schedule_once(lambda dt: self._start_polling(), 0.5)

    def _start_polling(self):
        Clock.schedule_interval(self.update_log, REFRESH_INTERVAL)

    # ---------- 布局 ----------

    def _update_label_height(self, *args):
        self.label.height = self.label.texture_size[1] + 20

    def _update_text_width(self, instance, width):
        self.label.text_size = (width - 8, None)

    # ---------- 自动滚底 ----------

    def _on_user_scroll(self, instance, value):
        # scroll_y ≈ 0 表示在底部，用户手动上滑就关闭自动滚底
        self.auto_scroll = (value <= 0.02)

    def scroll_to_bottom(self, *args):
        self.scroll.scroll_y = 0
        self.auto_scroll = True

    # ---------- 暂停/继续 ----------

    def toggle_pause(self, *args):
        self.paused = not self.paused
        if self.paused:
            self.pause_btn.text = "▶ 继续"
            self.pause_btn.background_color = (0.8, 0.4, 0.2, 1)
        else:
            self.pause_btn.text = "⏸ 暂停"
            self.pause_btn.background_color = (0.2, 0.5, 0.8, 1)

    # ---------- 过滤开关 ----------

    def toggle_filter(self, *args):
        self.filter_on = not self.filter_on
        if self.filter_on:
            self.filter_btn.text = "过滤:开"
            self.filter_btn.background_color = (0.2, 0.7, 0.3, 1)
        else:
            self.filter_btn.text = "过滤:关"
            self.filter_btn.background_color = (0.3, 0.3, 0.4, 1)
        self.last_mtime = 0  # 强制刷新

    # ---------- 核心：读取和显示日志 ----------

    def update_log(self, dt):
        if self.paused:
            return

        try:
            if not os.path.exists(LOG_PATH):
                self.label.text = (
                    f"[color=ffaa00]日志文件不存在[/color]\n\n"
                    f"路径：{LOG_PATH}\n\n"
                    f"请确认监控脚本已运行并输出到该路径。"
                )
                self.status_label.text = "⚠ 文件未找到"
                return

            # 检查文件是否有变化（没变就不重新读取，省资源）
            stat = os.stat(LOG_PATH)
            if stat.st_mtime == self.last_mtime:
                return
            self.last_mtime = stat.st_mtime

            # 高效读取尾部
            lines = tail_read(LOG_PATH, MAX_LINES)

            if not lines:
                self.label.text = "[color=888888]日志文件为空[/color]"
                self.status_label.text = "文件为空"
                return

            # 关键词过滤
            keyword = self.search_input.text.strip()
            if self.filter_on and keyword:
                lines = [l for l in lines if keyword.lower() in l.lower()]

            # 关键词高亮 + 日志级别着色
            display_lines = []
            for line in lines:
                line = line.rstrip("\n\r")
                # 转义 markup 特殊字符
                safe = line.replace("&", "&amp;").replace("[", "&bl;").replace("]", "&br;")
                # 还原后着色
                safe = safe.replace("&bl;", "[").replace("&br;", "]")
                colored = colorize_line(safe)

                # 搜索关键词高亮（黄底）
                if keyword and keyword.lower() in line.lower():
                    # 在着色后的文本里再包一层高亮标记不好做，简单处理：行首加标记
                    colored = f"[color=00ffff]▸[/color] {colored}"

                display_lines.append(colored)

            self.label.text = "\n".join(display_lines)

            # 更新状态栏
            total_lines = len(lines)
            update_time = time.strftime("%H:%M:%S", time.localtime(stat.st_mtime))
            size_str = format_size(stat.st_size)
            filter_info = f" | 过滤后 {len(display_lines)} 行" if (self.filter_on and keyword) else ""
            self.status_label.text = (
                f"📄 {size_str} | {total_lines} 行{filter_info} | 更新 {update_time}"
            )

            # 自动滚到底部
            if self.auto_scroll:
                Clock.schedule_once(lambda dt: self.scroll_to_bottom(), 0.1)

        except PermissionError:
            self.label.text = (
                "[color=ff4444]⛔ 权限不足[/color]\n\n"
                "请到 系统设置 → 应用 → Python Monitor → 权限\n"
                "→ 开启「所有文件访问」权限。"
            )
            self.status_label.text = "⛔ 权限不足"
        except Exception as e:
            self.label.text = f"[color=ff4444]读取出错[/color]\n{type(e).__name__}: {e}"
            self.status_label.text = "❌ 读取出错"


class MonitorApp(App):
    def build(self):
        Window.clearcolor = (0.08, 0.08, 0.12, 1)  # 深色背景
        self.title = "Python Monitor"
        return LogView()


if __name__ == "__main__":
    MonitorApp().run()