"""标签页：系统日志（Logcat）- 美化版"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
import re

import theme as T
from utils import run_cmd, esc
from widgets import IconButton, SmallButton, ScrollLabel


class LogcatTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=6, spacing=4, **kwargs)

        fb = BoxLayout(size_hint_y=None, height=40, spacing=3)
        self.log_level = "I"
        self.lvbtns = []
        for lv in ["V", "D", "I", "W", "E"]:
            btn = SmallButton(
                text=lv,
                background_color=(
                    T.BTN_PRIMARY if lv == "I" else T.BTN_NEUTRAL
                ),
            )
            btn.lv = lv
            btn.bind(on_press=self.set_lv)
            fb.add_widget(btn)
            self.lvbtns.append(btn)
        self.add_widget(fb)

        tb = BoxLayout(size_hint_y=None, height=42, spacing=4)
        self.tag_input = TextInput(
            hint_text="过滤标签（留空 = 全部）",
            size_hint_x=1, multiline=False, font_size=T.FONT_MD,
            background_color=T.BG_INPUT,
            foreground_color=T.TEXT_PRIMARY,
            hint_text_color=T.TEXT_DIM,
        )
        tb.add_widget(self.tag_input)
        self.add_widget(tb)

        self.scroll = ScrollLabel(font_size=T.FONT_XS)
        self.scroll.text = (
            f"[color={T.ACCENT_HEX}]点击「捕获日志」开始...[/color]"
        )
        self.add_widget(self.scroll)

        ctrl = BoxLayout(size_hint_y=None, height=46, spacing=4)
        cb = IconButton(
            icon="●", text="捕获日志",
            size_hint_x=0.3, background_color=T.BTN_SUCCESS,
        )
        cb.bind(on_press=self.capture)
        ctrl.add_widget(cb)

        clb = IconButton(
            icon="✕", text="清空",
            size_hint_x=0.2, background_color=T.BTN_DANGER,
        )
        clb.bind(on_press=lambda x: setattr(self.scroll, 'text', ''))
        ctrl.add_widget(clb)

        svb = IconButton(
            icon="↓", text="保存",
            size_hint_x=0.2, background_color=T.BTN_NEUTRAL,
        )
        svb.bind(on_press=self.save)
        ctrl.add_widget(svb)

        self.live_btn = IconButton(
            icon="◉", text="实时",
            size_hint_x=0.3, background_color=T.BTN_WARN,
        )
        self.live_btn.bind(on_press=self.toggle_live)
        ctrl.add_widget(self.live_btn)
        self.add_widget(ctrl)

        self.live_ev = None

    def set_lv(self, btn):
        self.log_level = btn.lv
        for b in self.lvbtns:
            b.background_color = (
                T.BTN_PRIMARY if b.lv == self.log_level else T.BTN_NEUTRAL
            )

    def color_lc(self, line):
        if ' E ' in line or '/E ' in line:
            return f"[color={T.RED_HEX}]{line}[/color]"
        elif ' W ' in line or '/W ' in line:
            return f"[color={T.YELLOW_HEX}]{line}[/color]"
        elif ' I ' in line or '/I ' in line:
            return f"[color={T.GREEN_HEX}]{line}[/color]"
        elif ' D ' in line or '/D ' in line:
            return f"[color=888888]{line}[/color]"
        return line

    def capture(self, *args):
        try:
            self.scroll.text = "[color=888888]正在捕获...[/color]\n"
            tag = self.tag_input.text.strip()
            if tag:
                cmd = f"logcat -d -v brief -s {tag}:{self.log_level} | tail -200"
            else:
                cmd = f"logcat -d -v brief *:{self.log_level} | tail -200"

            output = run_cmd(cmd, root=True, timeout=10)
            if output and not output.startswith("["):
                lines = output.split('\n')
                colored = [self.color_lc(esc(l)) for l in lines]
                self.scroll.text = '\n'.join(colored)
            else:
                self.scroll.text = (
                    f"[color={T.YELLOW_HEX}]"
                    f"无输出（级别={esc(self.log_level)}）[/color]"
                )
            self.scroll.scroll_to_bottom()
        except Exception as e:
            self.scroll.text = (
                f"[color={T.RED_HEX}]出错: {esc(str(e))}[/color]"
            )

    def toggle_live(self, *args):
        if self.live_ev:
            self.live_ev.cancel()
            self.live_ev = None
            self.scroll.text += (
                f"\n[color={T.YELLOW_HEX}]◉ 实时模式已关闭[/color]"
            )
            self.live_btn.background_color = T.BTN_WARN
        else:
            self.live_ev = Clock.schedule_interval(
                lambda dt: self.capture(), 2
            )
            self.scroll.text = (
                f"[color={T.GREEN_HEX}]◉ 实时模式已开启"
                f"（每2秒刷新）[/color]\n"
            )
            self.live_btn.background_color = T.BTN_SUCCESS

    def save(self, *args):
        try:
            path = "/sdcard/logcat_dump.txt"
            clean = re.sub(r'\[/?color[^\]]*\]', '', self.scroll.text)
            clean = clean.replace('&amp;', '&')
            clean = clean.replace('&bl;', '[').replace('&br;', ']')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(clean)
            self.scroll.text += (
                f"\n[color={T.GREEN_HEX}]✓ 已保存到 {esc(path)}[/color]"
            )
        except Exception as e:
            self.scroll.text += (
                f"\n[color={T.RED_HEX}]保存失败: {esc(str(e))}[/color]"
            )