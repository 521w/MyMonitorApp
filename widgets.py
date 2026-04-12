"""
自定义 UI 组件 - 卡片、按钮、分隔线、标题
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle
import theme as T


class StyledCard(BoxLayout):
    """带圆角背景的卡片容器"""

    def __init__(self, bg_color=None, radius=None, **kwargs):
        kwargs.setdefault('orientation', 'vertical')
        kwargs.setdefault('padding', [12, 8])
        kwargs.setdefault('spacing', 6)
        super().__init__(**kwargs)

        self._bg_color = bg_color or T.BG_CARD
        self._radius = radius or T.RADIUS_MD

        with self.canvas.before:
            Color(*self._bg_color)
            self._rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=self._radius
            )
        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size


class SectionHeader(BoxLayout):
    """带图标和强调线的章节标题"""

    def __init__(self, text, icon="●", color_hex=None, **kwargs):
        kwargs.setdefault('size_hint_y', None)
        kwargs.setdefault('height', 36)
        kwargs.setdefault('padding', [4, 2])
        super().__init__(**kwargs)

        c = color_hex or T.ACCENT_HEX
        self.add_widget(Label(
            text=f"[color={c}]{icon}[/color] [b]{text}[/b]",
            markup=True, font_size=T.FONT_LG,
            halign="left", valign="middle",
            size_hint_x=1,
        ))
        self.children[0].bind(
            size=lambda w, s: setattr(w, 'text_size', (s[0], s[1]))
        )


class Divider(BoxLayout):
    """水平分隔线"""

    def __init__(self, color=None, **kwargs):
        kwargs.setdefault('size_hint_y', None)
        kwargs.setdefault('height', 1)
        super().__init__(**kwargs)
        c = color or (0.25, 0.27, 0.35, 1)
        with self.canvas.before:
            Color(*c)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size


class IconButton(Button):
    """带图标前缀的美化按钮"""

    def __init__(self, icon="", **kwargs):
        kwargs.setdefault('font_size', T.FONT_MD)
        kwargs.setdefault('size_hint_y', None)
        kwargs.setdefault('height', 44)
        kwargs.setdefault('background_normal', '')
        kwargs.setdefault('color', T.TEXT_PRIMARY)
        if icon and 'text' in kwargs:
            kwargs['text'] = f"{icon} {kwargs['text']}"
        super().__init__(**kwargs)


class SmallButton(Button):
    """小号快捷按钮"""

    def __init__(self, **kwargs):
        kwargs.setdefault('font_size', T.FONT_SM)
        kwargs.setdefault('size_hint_y', None)
        kwargs.setdefault('height', 36)
        kwargs.setdefault('background_normal', '')
        kwargs.setdefault('color', T.TEXT_PRIMARY)
        kwargs.setdefault('background_color', T.BTN_NEUTRAL)
        super().__init__(**kwargs)


class ScrollLabel(ScrollView):
    """可滚动的文本标签（封装常用模式）"""

    def __init__(self, font_size=None, **kwargs):
        super().__init__(**kwargs)
        self.label = Label(
            size_hint_y=None, text="",
            halign="left", valign="top",
            markup=True,
            font_size=font_size or T.FONT_MD,
        )
        self.label.bind(
            texture_size=lambda *a: setattr(
                self.label, 'height', self.label.texture_size[1] + 20
            )
        )
        self.bind(
            width=lambda inst, w: setattr(
                self.label, 'text_size', (w - 16, None)
            )
        )
        self.add_widget(self.label)

    @property
    def text(self):
        return self.label.text

    @text.setter
    def text(self, value):
        self.label.text = value

    def scroll_to_bottom(self):
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: setattr(self, 'scroll_y', 0), 0.1)