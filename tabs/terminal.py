"""标签页：Root 终端 - 美化版"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.clock import Clock

import theme as T
from utils import run_cmd, esc
from widgets import IconButton, SmallButton, ScrollLabel


class TerminalTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=6, spacing=4, **kwargs)

        # 输出区域
        self.scroll = ScrollLabel(font_size=T.FONT_MD)
        self.scroll.text = (
            f"[color={T.GREEN_HEX}]┌─ Root 终端 ─────────────────┐[/color]\n"
            f"[color=888888]│ 所有命令通过 su -c 执行          │[/color]\n"
            f"[color={T.GREEN_HEX}]└────────────────────────────┘[/color]\n"
        )
        self.add_widget(self.scroll)

        # 输入栏
        input_bar = BoxLayout(size_hint_y=None, height=48, spacing=4)
        self.cmd_input = TextInput(
            hint_text="# 输入命令...",
            size_hint_x=0.7, multiline=False, font_size=T.FONT_LG,
            background_color=T.BG_INPUT,
            foreground_color=(0.3, 1, 0.3, 1),
            hint_text_color=T.TEXT_DIM,
        )
        self.cmd_input.bind(on_text_validate=self.exec_cmd)
        input_bar.add_widget(self.cmd_input)

        run_btn = IconButton(
            icon="▶", text="执行",
            size_hint_x=0.3, background_color=T.BTN_SUCCESS,
        )
        run_btn.bind(on_press=self.exec_cmd)
        input_bar.add_widget(run_btn)
        self.add_widget(input_bar)

        # 快捷命令
        quick_bar = BoxLayout(size_hint_y=None, height=38, spacing=3)
        quick_cmds = [
            ("身份", "id"),
            ("磁盘", "df -h"),
            ("网络", "ip addr show"),
            ("属性", "getprop ro.build.display.id"),
            ("进程", "top -b -n 1 | head -15"),
            ("清屏", "__clear__"),
        ]
        for label, cmd in quick_cmds:
            btn = SmallButton(text=label)
            btn.cmd_text = cmd
            btn.bind(on_press=self.quick_cmd)
            quick_bar.add_widget(btn)
        self.add_widget(quick_bar)

        self.cwd = "/sdcard"

    def quick_cmd(self, btn):
        if btn.cmd_text == "__clear__":
            self.scroll.text = f"[color={T.GREEN_HEX}]✓ 已清屏[/color]\n"
            return
        self.cmd_input.text = btn.cmd_text
        self.exec_cmd()

    def exec_cmd(self, *args):
        cmd = self.cmd_input.text.strip()
        if not cmd:
            return
        self.cmd_input.text = ""
        self.scroll.text += (
            f"\n[color={T.GREEN_HEX}]❯ {esc(cmd)}[/color]\n"
        )

        try:
            if cmd.startswith("cd "):
                target = cmd[3:].strip()
                result = run_cmd(f"cd {target} && pwd", root=True)
                if result and not result.startswith("["):
                    self.cwd = result
                    self.scroll.text += (
                        f"[color={T.ACCENT_HEX}]目录: {esc(self.cwd)}[/color]\n"
                    )
                else:
                    self.scroll.text += (
                        f"[color={T.RED_HEX}]{esc(result)}[/color]\n"
                    )
            else:
                full = f"cd {self.cwd} 2>/dev/null; {cmd}"
                result = run_cmd(full, root=True, timeout=15)
                if result:
                    self.scroll.text += f"{esc(result)}\n"
                else:
                    self.scroll.text += "[color=888888]（无输出）[/color]\n"
        except Exception as e:
            self.scroll.text += f"[color={T.RED_HEX}]{esc(str(e))}[/color]\n"

        self.scroll.scroll_to_bottom()