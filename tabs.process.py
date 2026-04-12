"""标签页：进程管理"""

from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
import re
import traceback

from utils import run_cmd, esc, log_crash


class ProcessTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=8, spacing=4, **kwargs)

        ctrl = BoxLayout(size_hint_y=None, height=44, spacing=4)
        rb = Button(
            text="刷新进程", size_hint_x=0.5,
            font_size="13sp", background_color=(0.2, 0.5, 0.8, 1),
        )
        rb.bind(on_press=self.refresh)
        ctrl.add_widget(rb)

        self.sort_btn = Button(
            text="排序:CPU", size_hint_x=0.5,
            font_size="13sp", background_color=(0.3, 0.3, 0.4, 1),
        )
        self.sort_btn.bind(on_press=self.toggle_sort)
        ctrl.add_widget(self.sort_btn)
        self.add_widget(ctrl)

        self.scroll = ScrollView(size_hint=(1, 1))
        self.label = Label(
            size_hint_y=None, text="点击「刷新进程」查看...",
            halign="left", valign="top",
            markup=True, font_size="12sp",
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

        kill_bar = BoxLayout(size_hint_y=None, height=44, spacing=4)
        self.pid_input = TextInput(
            hint_text="输入 PID 杀进程",
            size_hint_x=0.6, multiline=False, font_size="13sp",
            background_color=(0.15, 0.15, 0.2, 1),
            foreground_color=(1, 1, 1, 1),
        )
        kill_bar.add_widget(self.pid_input)
        kb = Button(
            text="强制结束", size_hint_x=0.4,
            font_size="13sp", background_color=(0.8, 0.2, 0.2, 1),
        )
        kb.bind(on_press=self.kill_proc)
        kill_bar.add_widget(kb)
        self.add_widget(kill_bar)

        self.sort_cpu = True

    def toggle_sort(self, *args):
        self.sort_cpu = not self.sort_cpu
        self.sort_btn.text = "排序:CPU" if self.sort_cpu else "排序:内存"
        self.refresh()

    def refresh(self, *args):
        try:
            output = run_cmd("top -b -n 1 | head -35", root=True)
            if not output or output.startswith("["):
                output = run_cmd("ps -A | head -30", root=True)
            if not output:
                self.label.text = "[color=ffaa00]需要 Root 权限[/color]"
                return

            lines = output.split('\n')
            colored = []
            for i, line in enumerate(lines):
                safe = esc(line)
                if i == 0 or line.startswith(' ') and 'PID' in line.upper():
                    colored.append(f"[color=88ccff][b]{safe}[/b][/color]")
                elif '%' in line:
                    nums = re.findall(r'(\d+)%', line)
                    high = any(int(n) > 50 for n in nums) if nums else False
                    med = any(int(n) > 10 for n in nums) if nums else False
                    if high:
                        colored.append(f"[color=ff4444]{safe}[/color]")
                    elif med:
                        colored.append(f"[color=ffaa00]{safe}[/color]")
                    else:
                        colored.append(safe)
                else:
                    colored.append(safe)
            self.label.text = '\n'.join(colored)
        except Exception as e:
            log_crash(f"进程管理: {traceback.format_exc()}")
            self.label.text = f"[color=ff4444]出错: {esc(str(e))}[/color]"

    def kill_proc(self, *args):
        pid = self.pid_input.text.strip()
        if not pid or not pid.isdigit():
            self.label.text = "[color=ff4444]请输入有效的 PID 数字[/color]"
            return
        result = run_cmd(f"kill -9 {pid}", root=True)
        if "error" in result.lower() or "denied" in result.lower():
            self.label.text = f"[color=ff4444]结束失败: {esc(result)}[/color]"
        else:
            self.label.text = f"[color=44ff44]已强制结束进程 PID {esc(pid)}[/color]"
        self.pid_input.text = ""
        Clock.schedule_once(lambda dt: self.refresh(), 0.5)