"""标签页：进程管理 - 美化版"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
import re
import traceback

import theme as T
from utils import run_cmd, esc, log_crash
from widgets import StyledCard, IconButton, SmallButton, ScrollLabel


class ProcessTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=6, spacing=6, **kwargs)

        # 控制栏
        ctrl = BoxLayout(size_hint_y=None, height=46, spacing=6)
        rb = IconButton(
            icon="↻", text="刷新进程",
            size_hint_x=0.5, background_color=T.BTN_PRIMARY,
        )
        rb.bind(on_press=self.refresh)
        ctrl.add_widget(rb)

        self.sort_btn = IconButton(
            icon="▼", text="排序:CPU",
            size_hint_x=0.5, background_color=T.BTN_NEUTRAL,
        )
        self.sort_btn.bind(on_press=self.toggle_sort)
        ctrl.add_widget(self.sort_btn)
        self.add_widget(ctrl)

        # 进程列表
        self.scroll = ScrollLabel(font_size=T.FONT_SM)
        self.scroll.text = (
            f"[color={T.ACCENT_HEX}]点击「↻ 刷新进程」查看进程列表[/color]"
        )
        self.add_widget(self.scroll)

        # Kill 栏
        kill_card = StyledCard(
            size_hint_y=None, height=56, orientation='horizontal',
            padding=[8, 6], spacing=6,
        )
        self.pid_input = TextInput(
            hint_text="输入 PID",
            size_hint_x=0.55, multiline=False, font_size=T.FONT_MD,
            background_color=T.BG_INPUT,
            foreground_color=T.TEXT_PRIMARY,
            hint_text_color=T.TEXT_DIM,
        )
        kill_card.add_widget(self.pid_input)
        kb = IconButton(
            icon="✕", text="强制结束",
            size_hint_x=0.45, background_color=T.BTN_DANGER,
        )
        kb.bind(on_press=self.kill_proc)
        kill_card.add_widget(kb)
        self.add_widget(kill_card)

        self.sort_cpu = True

    def toggle_sort(self, *args):
        self.sort_cpu = not self.sort_cpu
        self.sort_btn.text = "▼ 排序:CPU" if self.sort_cpu else "▼ 排序:内存"
        self.refresh()

    def refresh(self, *args):
        try:
            output = run_cmd("top -b -n 1 | head -35", root=True)
            if not output or output.startswith("["):
                output = run_cmd("ps -A | head -30", root=True)
            if not output:
                self.scroll.text = f"[color={T.YELLOW_HEX}]需要 Root 权限[/color]"
                return

            lines = output.split('\n')
            colored = []
            for i, line in enumerate(lines):
                safe = esc(line)
                if i == 0 or (line.lstrip().startswith('PID') or 'PID' in line.upper()[:20]):
                    colored.append(
                        f"[color={T.ACCENT_HEX}][b]{safe}[/b][/color]"
                    )
                elif '%' in line:
                    nums = re.findall(r'(\d+)%', line)
                    high = any(int(n) > 50 for n in nums) if nums else False
                    med = any(int(n) > 10 for n in nums) if nums else False
                    if high:
                        colored.append(f"[color={T.RED_HEX}]{safe}[/color]")
                    elif med:
                        colored.append(f"[color={T.YELLOW_HEX}]{safe}[/color]")
                    else:
                        colored.append(safe)
                else:
                    colored.append(safe)
            self.scroll.text = '\n'.join(colored)
        except Exception as e:
            log_crash(f"进程管理: {traceback.format_exc()}")
            self.scroll.text = f"[color={T.RED_HEX}]出错: {esc(str(e))}[/color]"

    def kill_proc(self, *args):
        pid = self.pid_input.text.strip()
        if not pid or not pid.isdigit():
            self.scroll.text = f"[color={T.RED_HEX}]请输入有效的 PID 数字[/color]"
            return
        result = run_cmd(f"kill -9 {pid}", root=True)
        if "error" in result.lower() or "denied" in result.lower():
            self.scroll.text = f"[color={T.RED_HEX}]结束失败: {esc(result)}[/color]"
        else:
            self.scroll.text = (
                f"[color={T.GREEN_HEX}]✓ 已强制结束进程 PID {esc(pid)}[/color]"
            )
        self.pid_input.text = ""
        Clock.schedule_once(lambda dt: self.refresh(), 0.5)