"""系统日志（Logcat）"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.metrics import dp
import re
import theme as T
from utils import run_cmd, esc
from widgets import StyledCard, StyledLabel, StyledButton, StyledTextInput


class LogcatTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(6), spacing=dp(4), **kwargs)

        # 级别筛选
        fb = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(3))
        self.log_level = "I"
        self.lvbtns = []
        for lv in ["V", "D", "I", "W", "E"]:
            btn = StyledButton(
                text=lv,
                bg_color=T.BTN_PRIMARY if lv == "I" else T.BTN_NEUTRAL,
            )
            btn.lv = lv
            btn.bind(on_release=self.set_lv)
            fb.add_widget(btn)
            self.lvbtns.append(btn)
        self.add_widget(fb)

        # TAG 过滤
        tb = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(4))
        self.tag_input = StyledTextInput(
            hint_text="过滤标签（留空 = 全部）", size_hint_x=1,
        )
        tb.add_widget(self.tag_input)
        self.add_widget(tb)

        # 日志输出区
        scroll = ScrollView()
        self.log_output = StyledLabel(
            text=f"[color={T.ACCENT_HEX}]点击「捕获日志」开始...[/color]",
            size_hint_y=None, halign="left", valign="top",
            font_size=T.FONT_XS,
        )
        self.log_output.bind(texture_size=self._auto_h)
        scroll.add_widget(self.log_output)
        self.add_widget(scroll)
        self._scroll = scroll

        # 控制按钮
        ctrl = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(4))
        cb = StyledButton(text="● 捕获日志", size_hint_x=0.3, bg_color=T.BTN_SUCCESS)
        cb.bind(on_release=self.capture)
        ctrl.add_widget(cb)

        clb = StyledButton(text="✕ 清空", size_hint_x=0.2, bg_color=T.BTN_DANGER)
        clb.bind(on_release=lambda x: setattr(self.log_output, "text", ""))
        ctrl.add_widget(clb)

        svb = StyledButton(text="↓ 保存", size_hint_x=0.2, bg_color=T.BTN_NEUTRAL)
        svb.bind(on_release=self.save)
        ctrl.add_widget(svb)

        self.live_btn = StyledButton(text="◉ 实时", size_hint_x=0.3, bg_color=T.BTN_WARN)
        self.live_btn.bind(on_release=self.toggle_live)
        ctrl.add_widget(self.live_btn)

        self.add_widget(ctrl)
        self.live_ev = None

    def _auto_h(self, *args):
        self.log_output.height = max(self.log_output.texture_size[1] + dp(20), dp(100))
        self.log_output.text_size = (self.log_output.width, None)

    def set_lv(self, btn):
        self.log_level = btn.lv
        for b in self.lvbtns:
            b._bg = T.BTN_PRIMARY if b.lv == self.log_level else T.BTN_NEUTRAL
            # 更新canvas颜色
            b.canvas.before.clear()
            from kivy.graphics import Color, RoundedRectangle
            with b.canvas.before:
                Color(*b._bg)
                b._rect = RoundedRectangle(pos=b.pos, size=b.size, radius=T.RADIUS_SM)
            b.bind(pos=b._upd, size=b._upd)

    def color_lc(self, line):
        if " E " in line or "/E " in line:
            return f"[color={T.RED_HEX}]{line}[/color]"
        elif " W " in line or "/W " in line:
            return f"[color={T.YELLOW_HEX}]{line}[/color]"
        elif " I " in line or "/I " in line:
            return f"[color={T.GREEN_HEX}]{line}[/color]"
        elif " D " in line or "/D " in line:
            return f"[color=888888]{line}[/color]"
        return line

    def capture(self, *args):
        try:
            self.log_output.text = "[color=888888]正在捕获...[/color]\n"
            tag = self.tag_input.text.strip()
            if tag:
                cmd = f"logcat -d -v brief -s {tag}:{self.log_level} | tail -200"
            else:
                cmd = f"logcat -d -v brief *:{self.log_level} | tail -200"
            output = run_cmd(cmd, root=True, timeout=10)
            if output and not output.startswith("["):
                lines = output.split("\n")
                colored = [self.color_lc(esc(l)) for l in lines]
                self.log_output.text = "\n".join(colored)
            else:
                self.log_output.text = (
                    f"[color={T.YELLOW_HEX}]"
                    f"无输出（级别={esc(self.log_level)}）[/color]"
                )
            self._scroll_bottom()
        except Exception as e:
            self.log_output.text = (
                f"[color={T.RED_HEX}]出错: {esc(str(e))}[/color]"
            )

    def _scroll_bottom(self):
        Clock.schedule_once(lambda dt: setattr(self._scroll, "scroll_y", 0), 0.1)

    def toggle_live(self, *args):
        if self.live_ev:
            self.live_ev.cancel()
            self.live_ev = None
            self.log_output.text += (
                f"\n[color={T.YELLOW_HEX}]◉ 实时模式已关闭[/color]"
            )
        else:
            self.live_ev = Clock.schedule_interval(lambda dt: self.capture(), 2)
            self.log_output.text = (
                f"[color={T.GREEN_HEX}]◉ 实时模式已开启（每2秒刷新）[/color]\n"
            )

    def save(self, *args):
        try:
            path = "/sdcard/logcat_dump.txt"
            clean = re.sub(r"\[/?color[^\]]*\]", "", self.log_output.text)
            clean = clean.replace("&amp;", "&")
            clean = clean.replace("&bl;", "[").replace("&br;", "]")
            with open(path, "w", encoding="utf-8") as f:
                f.write(clean)
            self.log_output.text += (
                f"\n[color={T.GREEN_HEX}]✓ 已保存到 {esc(path)}[/color]"
            )
        except Exception as e:
            self.log_output.text += (
                f"\n[color={T.RED_HEX}]保存失败: {esc(str(e))}[/color]"
            )