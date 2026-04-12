"""标签页：Root 终端"""

from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

from utils import run_cmd, esc


class TerminalTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=8, spacing=4, **kwargs)

        self.scroll = ScrollView(size_hint=(1, 1))
        self.output = Label(
            size_hint_y=None,
            text=(
                "[color=44ff44]Root 终端[/color]\n"
                "[color=888888]所有命令通过 su -c 以 Root 身份执行[/color]\n"
                "[color=888888]==============================[/color]\n"
            ),
            halign="left", valign="top",
            markup=True, font_size="13sp",
        )
        self.output.bind(
            texture_size=lambda *a: setattr(
                self.output, 'height', self.output.texture_size[1] + 20
            )
        )
        self.scroll.bind(
            width=lambda inst, w: setattr(
                self.output, 'text_size', (w - 8, None)
            )
        )
        self.scroll.add_widget(self.output)
        self.add_widget(self.scroll)

        input_bar = BoxLayout(size_hint_y=None, height=48, spacing=4)
        self.cmd_input = TextInput(
            hint_text="# 输入命令...",
            size_hint_x=0.7, multiline=False, font_size="14sp",
            background_color=(0.1, 0.1, 0.15, 1),
            foreground_color=(0.3, 1, 0.3, 1),
        )
        self.cmd_input.bind(on_text_validate=self.exec_cmd)
        input_bar.add_widget(self.cmd_input)

        run_btn = Button(
            text="执行", size_hint_x=0.3, font_size="14sp",
            background_color=(0.2, 0.7, 0.3, 1),
        )
        run_btn.bind(on_press=self.exec_cmd)
        input_bar.add_widget(run_btn)
        self.add_widget(input_bar)

        quick_bar = BoxLayout(size_hint_y=None, height=40, spacing=2)
        quick_cmds = [
            ("身份", "id"),
            ("磁盘", "df -h"),
            ("网络", "ip addr show"),
            ("系统", "getprop ro.build.display.id"),
            ("进程", "top -b -n 1 | head -15"),
            ("清屏", "__clear__"),
        ]
        for label, cmd in quick_cmds:
            btn = Button(
                text=label, font_size="11sp",
                background_color=(0.25, 0.25, 0.35, 1),
            )
            btn.cmd_text = cmd
            btn.bind(on_press=self.quick_cmd)
            quick_bar.add_widget(btn)
        self.add_widget(quick_bar)

        self.cwd = "/sdcard"

    def quick_cmd(self, btn):
        if btn.cmd_text == "__clear__":
            self.output.text = "[color=44ff44]已清屏[/color]\n"
            return
        self.cmd_input.text = btn.cmd_text
        self.exec_cmd()

    def exec_cmd(self, *args):
        cmd = self.cmd_input.text.strip()
        if not cmd:
            return
        self.cmd_input.text = ""
        self.output.text += f"\n[color=44ff44]# {esc(cmd)}[/color]\n"

        try:
            if cmd.startswith("cd "):
                target = cmd[3:].strip()
                result = run_cmd(f"cd {target} && pwd", root=True)
                if result and not result.startswith("["):
                    self.cwd = result
                    self.output.text += f"当前目录: {esc(self.cwd)}\n"
                else:
                    self.output.text += f"[color=ff4444]{esc(result)}[/color]\n"
            else:
                full = f"cd {self.cwd} 2>/dev/null; {cmd}"
                result = run_cmd(full, root=True, timeout=15)
                if result:
                    self.output.text += f"{esc(result)}\n"
                else:
                    self.output.text += "[color=888888]（无输出）[/color]\n"
        except Exception as e:
            self.output.text += f"[color=ff4444]{esc(str(e))}[/color]\n"

        Clock.schedule_once(
            lambda dt: setattr(self.scroll, 'scroll_y', 0), 0.1
        )