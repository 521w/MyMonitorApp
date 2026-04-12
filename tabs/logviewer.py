"""标签页：日志查看 - 美化版"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
import os
import time
import traceback

import theme as T
from utils import esc, tail_read, format_size, log_crash
from widgets import IconButton, ScrollLabel

LOG_PATH = "/sdcard/py_monitor.log"
MAX_LINES = 500


def colorize(line):
    upper = line.upper()
    if "ERROR" in upper or "FATAL" in upper or "EXCEPTION" in upper:
        return f"[color={T.RED_HEX}]{line}[/color]"
    elif "WARN" in upper:
        return f"[color={T.YELLOW_HEX}]{line}[/color]"
    elif "SUCCESS" in upper or "DONE" in upper:
        return f"[color={T.GREEN_HEX}]{line}[/color]"
    elif "DEBUG" in upper:
        return f"[color=888888]{line}[/color]"
    return line


class LogViewerTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=6, spacing=4, **kwargs)

        self.status = Label(
            text=f"[color={T.ACCENT_HEX}]◇ 等待日志文件...[/color]",
            markup=True, size_hint_y=None, height=30,
            halign="left", font_size=T.FONT_SM,
        )
        self.status.bind(
            size=lambda *a: setattr(
                self.status, 'text_size', (self.status.width, None)
            )
        )
        self.add_widget(self.status)

        sb = BoxLayout(size_hint_y=None, height=42, spacing=4)
        self.search = TextInput(
            hint_text="输入关键词过滤...", size_hint_x=0.7,
            multiline=False, font_size=T.FONT_MD,
            background_color=T.BG_INPUT,
            foreground_color=T.TEXT_PRIMARY,
            hint_text_color=T.TEXT_DIM,
        )
        sb.add_widget(self.search)
        self.fbtn = IconButton(
            icon="◯", text="过滤:关",
            size_hint_x=0.3, background_color=T.BTN_NEUTRAL,
        )
        self.fbtn.bind(on_press=self.toggle_filter)
        sb.add_widget(self.fbtn)
        self.add_widget(sb)

        self.scroll = ScrollLabel(font_size=T.FONT_MD)
        self.add_widget(self.scroll)

        bb = BoxLayout(size_hint_y=None, height=46, spacing=6)
        self.pbtn = IconButton(
            icon="⏸", text="暂停",
            size_hint_x=0.5, background_color=T.BTN_PRIMARY,
        )
        self.pbtn.bind(on_press=self.toggle_pause)
        bb.add_widget(self.pbtn)
        sb2 = IconButton(
            icon="↓", text="回到底部",
            size_hint_x=0.5, background_color=T.BTN_SUCCESS,
        )
        sb2.bind(on_press=lambda x: self.scroll.scroll_to_bottom())
        bb.add_widget(sb2)
        self.add_widget(bb)

        self.paused = False
        self.filter_on = False
        self.last_mt = 0
        Clock.schedule_interval(self.update, 0.5)

    def toggle_pause(self, *args):
        self.paused = not self.paused
        if self.paused:
            self.pbtn.text = "▶ 继续"
            self.pbtn.background_color = T.BTN_WARN
        else:
            self.pbtn.text = "⏸ 暂停"
            self.pbtn.background_color = T.BTN_PRIMARY

    def toggle_filter(self, *args):
        self.filter_on = not self.filter_on
        if self.filter_on:
            self.fbtn.text = "● 过滤:开"
            self.fbtn.background_color = T.BTN_SUCCESS
        else:
            self.fbtn.text = "◯ 过滤:关"
            self.fbtn.background_color = T.BTN_NEUTRAL
        self.last_mt = 0

    def update(self, dt):
        if self.paused:
            return
        try:
            if not os.path.exists(LOG_PATH):
                self.scroll.text = (
                    f"[color={T.YELLOW_HEX}]日志文件不存在[/color]\n"
                    f"路径：{esc(LOG_PATH)}"
                )
                self.status.text = f"[color={T.YELLOW_HEX}]◇ 文件未找到[/color]"
                return

            st = os.stat(LOG_PATH)
            if st.st_mtime == self.last_mt:
                return
            self.last_mt = st.st_mtime

            lines = tail_read(LOG_PATH, MAX_LINES)
            if not lines:
                self.scroll.text = "[color=888888]日志文件为空[/color]"
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
                    colored = f"[color=00ffff]▸[/color] {colored}"
                display.append(colored)

            self.scroll.text = '\n'.join(display)

            t = time.strftime("%H:%M:%S", time.localtime(st.st_mtime))
            sz = format_size(st.st_size)
            fi = f" | 过滤后 {len(display)} 行" if (self.filter_on and kw) else ""
            self.status.text = (
                f"[color={T.ACCENT_HEX}]◇ {sz} | "
                f"{len(lines)} 行{fi} | {t}[/color]"
            )
            self.scroll.scroll_to_bottom()
        except PermissionError:
            self.scroll.text = (
                f"[color={T.RED_HEX}]权限不足，请授权文件访问[/color]"
            )
        except Exception as e:
            log_crash(f"日志查看: {traceback.format_exc()}")
            self.scroll.text = (
                f"[color={T.RED_HEX}]出错: {esc(str(e))}[/color]"
            )