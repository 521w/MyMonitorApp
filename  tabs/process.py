"""标签页：进程管理 - 美化版"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
import re
import traceback

import theme as T
from utils import run_cmd, esc, log_crash
from widgets import StyledCard, IconButton, SmallButton, ScrollLabel


class ProcessTab(BoxLayout):──────────────────────────┘"
                f"[/color][/b]\n\n"

                f"[color={T.ACCENT_HEX}]● 处理器[/color]\n"
                f"  [color={cc}]{bar(cpu)} {cpu}%[/color]\n\n"

                f"[color={T.ACCENT_HEX}]● 内存[/color]\n"
                f"  [color={mc}]{bar(mp)} {mp}%[/color]\n"
                f"  [color={T.ACCENT_HEX}]已用[/color] {mu // 1024}MB  "
                f"[color={T.ACCENT_HEX}]共[/color] {mt // 1024}MB  "
                f"[color={T.GREEN_HEX}]可用 {ma // 1024}MB[/color]\n\n"

                f"[color={T.ACCENT_HEX}]● 电池[/color]\n"
                f"  电量 [b]{esc(bl)}%[/b]  {esc(bs_cn)}  温度 {esc(bt)}°C\n\n"

                f"[color={T.PURPLE_HEX}]━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/color]\n\n"

                f"  [color={T.ACCENT_HEX}]处理器温度[/color]  {esc(ct)}°C\n"
                f"  [color={T.ACCENT_HEX}]运行时间  [/color]  {esc(uptime)}\n"
                f"  [color={T.ACCENT_HEX}]内核版本  [/color]  {esc(kernel)}\n\n"

                f"[color={T.ACCENT_HEX}]● 磁盘空间[/color]\n"
                f"  {esc(disk)}\n\n"

                f"[color={T.ACCENT_HEX}]● 网络流量[/color] (接口 ↓接收 ↑发送)\n"
                f"  {esc(net)}\n"
            )
        except Exception as e:
            log_crash(f"系统监控: {traceback.format_exc()}")
            self.scroll.text = f"[color={T.RED_HEX}]读取出错: {esc(str(e))}[/color]"