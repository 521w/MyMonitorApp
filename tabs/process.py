"""进程管理"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.metrics import dp
import subprocess
import theme as T
from widgets import StyledCard, StyledLabel, StyledButton, StyledTextInput


class ProcessTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(8), spacing=dp(8), **kwargs)

        # 顶部操作栏
        top = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        self.search_input = StyledTextInput(hint_text="搜索进程名/PID...", size_hint_x=0.6)
        btn_search = StyledButton(text="搜索", size_hint_x=0.2)
        btn_search.bind(on_release=lambda x: self.refresh())
        btn_all = StyledButton(text="全部", size_hint_x=0.2, bg_color=T.BTN_NEUTRAL)
        btn_all.bind(on_release=lambda x: self._show_all())
        top.add_widget(self.search_input)
        top.add_widget(btn_search)
        top.add_widget(btn_all)
        self.add_widget(top)

        # Kill 栏
        kill_bar = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        self.pid_input = StyledTextInput(hint_text="输入PID", size_hint_x=0.5)
        btn_kill = StyledButton(text="结束进程", size_hint_x=0.25, bg_color=T.BTN_DANGER)
        btn_kill.bind(on_release=lambda x: self._kill())
        btn_kill9 = StyledButton(text="强杀-9", size_hint_x=0.25, bg_color=T.BTN_DANGER)
        btn_kill9.bind(on_release=lambda x: self._kill(force=True))
        kill_bar.add_widget(self.pid_input)
        kill_bar.add_widget(btn_kill)
        kill_bar.add_widget(btn_kill9)
        self.add_widget(kill_bar)

        # 进程数统计
        self.count_label = StyledLabel(
            text="进程数: --", size_hint_y=None, height=dp(28),
            font_size=T.FONT_SM, color=T.TEXT_DIM,
        )
        self.add_widget(self.count_label)

        # 进程列表
        scroll = ScrollView()
        self.proc_list = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=dp(4)
        )
        self.proc_list.bind(minimum_height=self.proc_list.setter("height"))
        scroll.add_widget(self.proc_list)
        self.add_widget(scroll)

        # 状态
        self.status_label = StyledLabel(
            text="", size_hint_y=None, height=dp(28), font_size=T.FONT_SM
        )
        self.add_widget(self.status_label)

        Clock.schedule_once(lambda dt: self.refresh(), 1)

    def _run(self, cmd):
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            return r.stdout.strip(), r.stderr.strip()
        except Exception as e:
            return "", str(e)

    def refresh(self, *args):
        keyword = self.search_input.text.strip()
        if keyword:
            cmd = f"ps -eo pid,user,%cpu,%mem,comm 2>/dev/null | head -1 && ps -eo pid,user,%cpu,%mem,comm 2>/dev/null | grep -i '{keyword}'"
        else:
            cmd = "ps -eo pid,user,%cpu,%mem,comm 2>/dev/null | head -50"
        out, err = self._run(cmd)
        self._display(out, err)

    def _show_all(self):
        self.search_input.text = ""
        out, err = self._run("ps -eo pid,user,%cpu,%mem,comm 2>/dev/null | head -80")
        self._display(out, err)

    def _display(self, out, err):
        self.proc_list.clear_widgets()
        if not out:
            self.proc_list.add_widget(
                StyledLabel(text=f"[color={T.RED_HEX}]无结果 {err}[/color]",
                            size_hint_y=None, height=dp(30))
            )
            self.count_label.text = "进程数: 0"
            return
        lines = out.strip().split("\n")
        self.count_label.text = f"进程数: {max(0, len(lines) - 1)}"
        for i, line in enumerate(lines):
            color = T.ACCENT if i == 0 else T.TEXT_PRIMARY
            lbl = StyledLabel(
                text=line, size_hint_y=None, height=dp(26),
                font_size=T.FONT_SM, color=color, halign="left",
            )
            lbl.bind(size=lbl.setter("text_size"))
            self.proc_list.add_widget(lbl)

    def _kill(self, force=False):
        pid = self.pid_input.text.strip()
        if not pid or not pid.isdigit():
            self.status_label.text = f"[color={T.RED_HEX}]请输入有效PID[/color]"
            return
        sig = "-9 " if force else ""
        out, err = self._run(f"kill {sig}{pid}")
        if err:
            self.status_label.text = f"[color={T.RED_HEX}]失败: {err}[/color]"
        else:
            self.status_label.text = f"[color={T.GREEN_HEX}]已发送信号给 PID {pid}[/color]"
            Clock.schedule_once(lambda dt: self.refresh(), 0.5)