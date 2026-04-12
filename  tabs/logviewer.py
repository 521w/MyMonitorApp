"""标签页：日志查看"""

from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
import os
import time
import traceback

from utils import esc, tail_read, format_size, log_crash

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