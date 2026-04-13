"""设置 - 背景/主题自定义"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp
import os
import theme as T
from widgets import StyledCard, StyledLabel, StyledButton, StyledTextInput


class SettingsTab(BoxLayout):
    app = None

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(8), spacing=dp(8), **kwargs)

        scroll = ScrollView()
        self.content = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=dp(10)
        )
        self.content.bind(minimum_height=self.content.setter("height"))

        # ======= 背景色预设 =======
        color_card = StyledCard(size_hint_y=None, height=dp(180))
        color_card.add_widget(
            StyledLabel(
                text=f"[color={T.ACCENT_HEX}]🎨 背景颜色预设[/color]",
                size_hint_y=None, height=dp(28), font_size=T.FONT_MD,
            )
        )
        grid = GridLayout(cols=4, spacing=dp(6), size_hint_y=None, height=dp(130))
        for name, color in T.BG_PRESETS.items():
            btn = StyledButton(text=name, bg_color=color)
            btn._preset_color = color
            btn.bind(on_release=self._set_preset)
            grid.add_widget(btn)
        color_card.add_widget(grid)
        self.content.add_widget(color_card)

        # ======= 自定义背景图片 =======
        img_card = StyledCard(size_hint_y=None, height=dp(130))
        img_card.add_widget(
            StyledLabel(
                text=f"[color={T.ACCENT_HEX}]🖼 自定义背景图片[/color]",
                size_hint_y=None, height=dp(28), font_size=T.FONT_MD,
            )
        )
        img_bar = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        self.img_input = StyledTextInput(
            hint_text="输入图片路径 (jpg/png/webp)", size_hint_x=0.7
        )
        btn_set = StyledButton(text="设置", size_hint_x=0.3)
        btn_set.bind(on_release=self._set_image)
        img_bar.add_widget(self.img_input)
        img_bar.add_widget(btn_set)
        img_card.add_widget(img_bar)

        self.img_status = StyledLabel(
            text="", size_hint_y=None, height=dp(24), font_size=T.FONT_SM
        )
        img_card.add_widget(self.img_status)
        self.content.add_widget(img_card)

        # ======= 图片浏览器 =======
        browse_card = StyledCard(size_hint_y=None, height=dp(90))
        browse_card.add_widget(
            StyledLabel(
                text=f"[color={T.ACCENT_HEX}]📂 快捷浏览图片[/color]",
                size_hint_y=None, height=dp(28), font_size=T.FONT_SM,
            )
        )
        browse_bar = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        for name, path in [("相册", "/sdcard/DCIM"), ("下载", "/sdcard/Download"),
                           ("图片", "/sdcard/Pictures")]:
            b = StyledButton(text=name, bg_color=T.BTN_NEUTRAL)
            b._browse_path = path
            b.bind(on_release=self._browse)
            browse_bar.add_widget(b)
        browse_card.add_widget(browse_bar)
        self.content.add_widget(browse_card)

        # 浏览结果
        self.browse_result = StyledCard(size_hint_y=None, height=dp(10))
        self.browse_label = StyledLabel(
            text="", halign="left", valign="top", font_size=T.FONT_SM,
        )
        self.browse_label.bind(size=self.browse_label.setter("text_size"))
        self.browse_result.add_widget(self.browse_label)
        self.content.add_widget(self.browse_result)

        # ======= 恢复默认 =======
        reset_card = StyledCard(size_hint_y=None, height=dp(60))
        btn_reset = StyledButton(text="🔄 恢复默认背景", bg_color=T.BTN_DANGER)
        btn_reset.bind(on_release=self._reset)
        reset_card.add_widget(btn_reset)
        self.content.add_widget(reset_card)

        scroll.add_widget(self.content)
        self.add_widget(scroll)

    def _set_preset(self, btn):
        color = btn._preset_color
        if self.app:
            self.app.bg.set_bg_color(color)
            cfg = T.load_config()
            cfg["bg_color"] = list(color)
            cfg.pop("bg_image", None)
            T.save_config(cfg)
            self.img_status.text = f"[color={T.GREEN_HEX}]已切换背景色[/color]"

    def _set_image(self, *args):
        path = self.img_input.text.strip()
        if not path:
            self.img_status.text = f"[color={T.RED_HEX}]请输入图片路径[/color]"
            return
        if not os.path.exists(path):
            self.img_status.text = f"[color={T.RED_HEX}]文件不存在: {path}[/color]"
            return
        if self.app and self.app.bg.set_bg_image(path):
            cfg = T.load_config()
            cfg["bg_image"] = path
            cfg.pop("bg_color", None)
            T.save_config(cfg)
            self.img_status.text = f"[color={T.GREEN_HEX}]背景已设置[/color]"
        else:
            self.img_status.text = f"[color={T.RED_HEX}]设置失败[/color]"

    def _browse(self, btn):
        path = btn._browse_path
        if not os.path.isdir(path):
            self.browse_label.text = f"[color={T.RED_HEX}]目录不存在: {path}[/color]"
            self.browse_result.height = dp(50)
            return
        exts = (".jpg", ".jpeg", ".png", ".webp", ".bmp")
        try:
            files = []
            for f in sorted(os.listdir(path)):
                if f.lower().endswith(exts):
                    full = os.path.join(path, f)
                    try:
                        size = os.path.getsize(full)
                        if size > 1024 * 1024:
                            s = f"{size / 1024 / 1024:.1f}MB"
                        elif size > 1024:
                            s = f"{size / 1024:.1f}KB"
                        else:
                            s = f"{size}B"
                    except Exception:
                        s = "?"
                    files.append(f"🖼 {full}  ({s})")
            if files:
                self.browse_label.text = "\n".join(files[:30])
                self.browse_result.height = dp(24) * min(len(files), 30) + dp(20)
            else:
                self.browse_label.text = f"[color={T.YELLOW_HEX}]未找到图片文件[/color]"
                self.browse_result.height = dp(50)
        except Exception as e:
            self.browse_label.text = f"[color={T.RED_HEX}]读取失败: {e}[/color]"
            self.browse_result.height = dp(50)

    def _reset(self, *args):
        if self.app:
            self.app.bg.set_bg_color(T.BG_DARK)
            cfg = T.load_config()
            cfg.pop("bg_color", None)
            cfg.pop("bg_image", None)
            T.save_config(cfg)
            self.img_status.text = f"[color={T.GREEN_HEX}]已恢复默认[/color]"