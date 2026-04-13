"""自定义组件库 - 微信风格"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp
import theme as T


class BgContainer(BoxLayout):
    """全屏背景容器，支持纯色和图片"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self._bg_color = T.BG_DARK
        with self.canvas.before:
            self._color_inst = Color(*self._bg_color)
            self._rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

    def set_bg_color(self, color):
        self._color_inst.rgba = color
        self._rect.source = ""
        self._update_bg()

    def set_bg_image(self, path):
        import os
        if os.path.exists(path):
            self._color_inst.rgba = (1, 1, 1, 1)
            self._rect.source = path
            self._update_bg()
            return True
        return False

    def _update_bg(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size


class TopBar(BoxLayout):
    """顶部标题栏"""

    def __init__(self, title="监控", **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(48)
        self.padding = [dp(16), dp(4)]
        with self.canvas.before:
            Color(*T.BG_NAV)
            self._rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd, size=self._upd)
        self._title = Label(
            text=title, font_size=T.FONT_LG,
            color=T.TEXT_PRIMARY, bold=True,
            halign="left", valign="center",
        )
        self._title.bind(size=self._title.setter("text_size"))
        self.add_widget(self._title)

    def set_title(self, text):
        self._title.text = text

    def _upd(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size


class BottomNav(BoxLayout):
    """微信风格底部导航"""

    TAB_ICONS = [
        ("📊", "监控"), ("⚙", "进程"), ("💻", "终端"),
        ("📋", "日志"), ("📱", "系统"), ("🔧", "工具"), ("⚡", "设置"),
    ]

    def __init__(self, callback=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(56)
        self.padding = [dp(2), dp(2)]
        self._callback = callback
        self._buttons = []
        self._current = 0
        with self.canvas.before:
            Color(*T.BG_NAV)
            self._rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd, size=self._upd)

        for i, (icon, name) in enumerate(self.TAB_ICONS):
            btn = Button(
                text=f"{icon}\n{name}", font_size=T.FONT_SM,
                halign="center", background_normal="",
                background_color=(0, 0, 0, 0), color=T.TEXT_DIM,
            )
            btn._tab_index = i
            btn.bind(on_release=self._on_tab)
            self._buttons.append(btn)
            self.add_widget(btn)
        self._highlight(0)

    def _on_tab(self, btn):
        idx = btn._tab_index
        if idx != self._current:
            self._current = idx
            self._highlight(idx)
            if self._callback:
                self._callback(idx)

    def _highlight(self, idx):
        for i, btn in enumerate(self._buttons):
            btn.color = T.ACCENT if i == idx else T.TEXT_DIM

    def _upd(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size


class StyledCard(BoxLayout):
    """半透明圆角卡片"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = dp(12)
        self.spacing = dp(6)
        with self.canvas.before:
            Color(*T.BG_CARD)
            self._rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=T.RADIUS_MD
            )
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size


class StyledButton(Button):
    """主题按钮"""

    def __init__(self, bg_color=None, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_color = (0, 0, 0, 0)
        self.color = T.TEXT_PRIMARY
        self.font_size = T.FONT_MD
        self.size_hint_y = None
        self.height = dp(40)
        self._bg = bg_color or T.BTN_PRIMARY
        with self.canvas.before:
            Color(*self._bg)
            self._rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=T.RADIUS_SM
            )
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size


class StyledTextInput(TextInput):
    """主题输入框"""

    def __init__(self, **kwargs):
        kwargs.setdefault("background_color", T.BG_INPUT)
        kwargs.setdefault("foreground_color", T.TEXT_PRIMARY)
        kwargs.setdefault("cursor_color", T.ACCENT)
        kwargs.setdefault("font_size", T.FONT_MD)
        kwargs.setdefault("padding", [dp(10), dp(8)])
        kwargs.setdefault("multiline", False)
        super().__init__(**kwargs)


class StyledLabel(Label):
    """主题标签"""

    def __init__(self, **kwargs):
        kwargs.setdefault("color", T.TEXT_PRIMARY)
        kwargs.setdefault("font_size", T.FONT_MD)
        kwargs.setdefault("markup", True)
        super().__init__(**kwargs)