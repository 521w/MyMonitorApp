"""标签页：系统日志（Logcat）"""

from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
import re

from utils import run_cmd, esc


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
                self.label.text = (
                    f"[color=ffaa00]无输出（级别={esc(self.log_level)}）[/color]"
                )
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