"""日志文件查看器"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.metrics import dp
import os
import theme as T
from widgets import StyledCard, StyledLabel, StyledButton, StyledTextInput


class LogViewerTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(8), spacing=dp(6), **kwargs)

        # 文件路径输入
        path_bar = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        self.path_input = StyledTextInput(
            text="/sdcard/pm_log.txt", hint_text="日志文件路径...", size_hint_x=0.65
        )
        btn_load = StyledButton(text="加载", size_hint_x=0.2)
        btn_load.bind(on_release=lambda x: self._load())
        btn_tail = StyledButton(text="尾部", size_hint_x=0.15, bg_color=T.BTN_NEUTRAL)
        btn_tail.bind(on_release=lambda x: self._load(tail=True))
        path_bar.add_widget(self.path_input)
        path_bar.add_widget(btn_load)
        path_bar.add_widget(btn_tail)
        self.add_widget(path_bar)

        # 搜索栏
        search_bar = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        self.filter_input = StyledTextInput(hint_text="过滤关键字...", size_hint_x=0.5)
        btn_filter = StyledButton(text="过滤", size_hint_x=0.15)
        btn_filter.bind(on_release=lambda x: self._filter())
        btn_err = StyledButton(text="仅ERROR", size_hint_x=0.2, bg_color=T.BTN_WARN)
        btn_err.bind(on_release=lambda x: self._filter(keyword="error"))
        btn_clr = StyledButton(text="清除", size_hint_x=0.15, bg_color=T.BTN_NEUTRAL)
        btn_clr.bind(on_release=lambda x: self._show_raw())
        search_bar.add_widget(self.filter_input)
        search_bar.add_widget(btn_filter)
        search_bar.add_widget(btn_err)
        search_bar.add_widget(btn_clr)
        self.add_widget(search_bar)

        # 状态
        self.status = StyledLabel(
            text=f"[color={T.ACCENT_HEX}]请输入日志路径并点击加载[/color]",
            size_hint_y=None, height=dp(24), font_size=T.FONT_SM,
        )
        self.add_widget(self.status)

        # 内容区
        scroll = ScrollView()
        self.log_label = StyledLabel(
            text="", size_hint_y=None, halign="left", valign="top",
            font_size=T.FONT_SM,
        )
        self.log_label.bind(texture_size=self._auto_h)
        scroll.add_widget(self.log_label)
        self.add_widget(scroll)
        self._scroll = scroll

        self._raw_lines = []

        # 快捷路径
        quick = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(4))
        paths = [
            ("dmesg", "/proc/kmsg"),
            ("syslog", "/var/log/syslog"),
            ("pm_log", "/sdcard/pm_log.txt"),
        ]
        for name, path in paths:
            b = StyledButton(text=name, bg_color=T.BTN_NEUTRAL)
            b._path = path
            b.bind(on_release=lambda x: self._quick_path(x))
            quick.add_widget(b)
        self.add_widget(quick)

    def _auto_h(self, *args):
        self.log_label.height = max(self.log_label.texture_size[1] + dp(20), dp(100))
        self.log_label.text_size = (self.log_label.width, None)

    def _quick_path(self, btn):
        self.path_input.text = btn._path
        self._load()

    def _load(self, tail=False):
        path = self.path_input.text.strip()
        if not path:
            self.status.text = f"[color={T.RED_HEX}]请输入文件路径[/color]"
            return
        if not os.path.exists(path):
            self.status.text = f"[color={T.RED_HEX}]文件不存在: {path}[/color]"
            self.log_label.text = ""
            return
        try:
            with open(path, "r", errors="replace") as f:
                lines = f.readlines()
            if tail:
                lines = lines[-200:]
            else:
                lines = lines[:500]
            self._raw_lines = lines
            self.status.text = f"[color={T.GREEN_HEX}]已加载 {len(lines)} 行[/color]  {path}"
            self._show_raw()
        except Exception as e:
            self.status.text = f"[color={T.RED_HEX}]读取失败: {e}[/color]"

    def _show_raw(self):
        self.log_label.text = self._colorize(self._raw_lines)

    def _filter(self, keyword=None):
        kw = keyword or self.filter_input.text.strip()
        if not kw:
            self._show_raw()
            return
        filtered = [l for l in self._raw_lines if kw.lower() in l.lower()]
        self.status.text = f"[color={T.YELLOW_HEX}]过滤 '{kw}': {len(filtered)} 条[/color]"
        self.log_label.text = self._colorize(filtered)

    def _colorize(self, lines):
        out = []
        for line in lines:
            ll = line.strip()
            if not ll:
                continue
            low = ll.lower()
            if "error" in low or "fatal" in low or "exception" in low:
                out.append(f"[color={T.RED_HEX}]{ll}[/color]")
            elif "warn" in low:
                out.append(f"[color={T.YELLOW_HEX}]{ll}[/color]")
            elif "info" in low:
                out.append(f"[color={T.GREEN_HEX}]{ll}[/color]")
            else:
                out.append(ll)
        return "\n".join(out) if out else f"[color={T.TEXT_DIM[0]*255:.0f}{T.TEXT_DIM[1]*255:.0f}{T.TEXT_DIM[2]*255:.0f}]无内容[/color]"