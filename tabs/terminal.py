"""终端模拟器"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.metrics import dp
import subprocess, os, threading
import theme as T
from widgets import StyledCard, StyledLabel, StyledButton, StyledTextInput


class TerminalTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(8), spacing=dp(6), **kwargs)

        self.history = []
        self.hist_idx = -1
        self.cwd = os.environ.get("HOME", "/data/data")

        # 路径显示
        self.path_label = StyledLabel(
            text=f"[color={T.ACCENT_HEX}]{self.cwd}[/color]",
            size_hint_y=None, height=dp(24), font_size=T.FONT_SM,
        )
        self.add_widget(self.path_label)

        # 输出区域
        scroll = ScrollView()
        self.output = StyledLabel(
            text=f"[color={T.GREEN_HEX}]终端就绪，输入命令开始[/color]\n",
            size_hint_y=None, halign="left", valign="top",
            font_size=T.FONT_SM, color=T.TEXT_PRIMARY,
        )
        self.output.bind(texture_size=self._auto_height)
        scroll.add_widget(self.output)
        self.add_widget(scroll)
        self._scroll = scroll

        # 输入栏
        inp_bar = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        self.cmd_input = StyledTextInput(hint_text="输入命令...", size_hint_x=0.65)
        self.cmd_input.bind(on_text_validate=lambda x: self._exec())
        btn_run = StyledButton(text="执行", size_hint_x=0.2)
        btn_run.bind(on_release=lambda x: self._exec())
        btn_clr = StyledButton(text="清屏", size_hint_x=0.15, bg_color=T.BTN_NEUTRAL)
        btn_clr.bind(on_release=lambda x: self._clear())
        inp_bar.add_widget(self.cmd_input)
        inp_bar.add_widget(btn_run)
        inp_bar.add_widget(btn_clr)
        self.add_widget(inp_bar)

        # 快捷按钮
        quick = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(4))
        for label, cmd in [("ls", "ls -la"), ("pwd", "pwd"), ("df", "df -h"),
                           ("top", "top -bn1 | head -20"), ("id", "id")]:
            b = StyledButton(text=label, bg_color=T.BTN_NEUTRAL)
            b._cmd = cmd
            b.bind(on_release=lambda x: self._quick(x))
            quick.add_widget(b)
        self.add_widget(quick)

    def _auto_height(self, *args):
        self.output.height = max(self.output.texture_size[1] + dp(20), dp(100))
        self.output.text_size = (self.output.width, None)

    def _quick(self, btn):
        self.cmd_input.text = btn._cmd
        self._exec()

    def _exec(self):
        cmd = self.cmd_input.text.strip()
        if not cmd:
            return
        self.history.append(cmd)
        self.hist_idx = -1
        self.cmd_input.text = ""

        # cd command
        if cmd.startswith("cd "):
            target = cmd[3:].strip()
            target = os.path.expanduser(target)
            if not os.path.isabs(target):
                target = os.path.join(self.cwd, target)
            target = os.path.normpath(target)
            if os.path.isdir(target):
                self.cwd = target
                self.path_label.text = f"[color={T.ACCENT_HEX}]{self.cwd}[/color]"
                self._append(f"$ cd {target}\n", T.GREEN_HEX)
            else:
                self._append(f"cd: {target}: 目录不存在\n", T.RED_HEX)
            return

        self._append(f"[color={T.ACCENT_HEX}]$ {cmd}[/color]\n")

        def run_cmd():
            try:
                r = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True,
                    timeout=30, cwd=self.cwd,
                )
                out = r.stdout
                err = r.stderr
                Clock.schedule_once(lambda dt: self._show_result(out, err))
            except subprocess.TimeoutExpired:
                Clock.schedule_once(lambda dt: self._append("命令超时(30s)\n", T.RED_HEX))
            except Exception as e:
                Clock.schedule_once(lambda dt: self._append(f"错误: {e}\n", T.RED_HEX))

        threading.Thread(target=run_cmd, daemon=True).start()

    def _show_result(self, out, err):
        if out:
            self._append(out + "\n")
        if err:
            self._append(f"[color={T.YELLOW_HEX}]{err}[/color]\n")
        self._scroll_bottom()

    def _append(self, text, color=None):
        if color:
            text = f"[color={color}]{text}[/color]"
        self.output.text += text
        # 限制输出长度
        if len(self.output.text) > 50000:
            self.output.text = self.output.text[-30000:]
        self._scroll_bottom()

    def _scroll_bottom(self):
        Clock.schedule_once(lambda dt: setattr(self._scroll, 'scroll_y', 0), 0.1)

    def _clear(self):
        self.output.text = f"[color={T.GREEN_HEX}]已清屏[/color]\n"