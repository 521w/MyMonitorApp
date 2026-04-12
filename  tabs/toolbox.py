"""标签页：工具箱 - 实用 Root 工具集"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.clock import Clock

import theme as T
from utils import run_cmd, esc
from widgets import StyledCard, IconButton, SmallButton, ScrollLabel, Divider


class ToolboxTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=6, spacing=4, **kwargs)

        # 工具按钮区
        tool_grid = BoxLayout(size_hint_y=None, height=90, spacing=4,
                              orientation='vertical')

        row1 = BoxLayout(size_hint_y=None, height=42, spacing=4)
        tools_r1 = [
            ("◈ 设备信息", self.device_info),
            ("◆ WiFi信息", self.wifi_info),
            ("▸ 存储详情", self.storage_info),
        ]
        for label, callback in tools_r1:
            btn = IconButton(
                text=label, background_color=T.BTN_PRIMARY,
                size_hint_x=1.0 / len(tools_r1),
            )
            btn.bind(on_press=lambda x, cb=callback: cb())
            row1.add_widget(btn)
        tool_grid.add_widget(row1)

        row2 = BoxLayout(size_hint_y=None, height=42, spacing=4)
        tools_r2 = [
            ("● 电池详情", self.battery_detail),
            ("◉ 已装应用", self.list_apps),
            ("★ 硬件信息", self.hw_info),
        ]
        for label, callback in tools_r2:
            btn = IconButton(
                text=label, background_color=T.BTN_NEUTRAL,
                size_hint_x=1.0 / len(tools_r2),
            )
            btn.bind(on_press=lambda x, cb=callback: cb())
            row2.add_widget(btn)
        tool_grid.add_widget(row2)
        self.add_widget(tool_grid)

        self.add_widget(Divider())

        # Ping 工具
        ping_bar = BoxLayout(size_hint_y=None, height=44, spacing=4)
        self.ping_input = TextInput(
            hint_text="输入地址 Ping 测试（如 baidu.com）",
            size_hint_x=0.65, multiline=False, font_size=T.FONT_MD,
            background_color=T.BG_INPUT,
            foreground_color=T.TEXT_PRIMARY,
            hint_text_color=T.TEXT_DIM,
        )
        self.ping_input.bind(on_text_validate=lambda x: self.do_ping())
        ping_bar.add_widget(self.ping_input)
        pb = IconButton(
            icon="▶", text="Ping",
            size_hint_x=0.35, background_color=T.BTN_SUCCESS,
        )
        pb.bind(on_press=lambda x: self.do_ping())
        ping_bar.add_widget(pb)
        self.add_widget(ping_bar)

        # 输出区域
        self.scroll = ScrollLabel(font_size=T.FONT_SM)
        self.scroll.text = (
            f"[color={T.ACCENT_HEX}]"
            f"┌─ 工具箱 ──────────────────┐\n"
            f"│  点击上方按钮使用各种工具    │\n"
            f"│  输入地址可进行 Ping 测试    │\n"
            f"└──────────────────────────┘"
            f"[/color]"
        )
        self.add_widget(self.scroll)

        # 底部快捷操作
        bottom = BoxLayout(size_hint_y=None, height=38, spacing=3)
        quick_ops = [
            ("截屏", self.screenshot),
            ("清缓存", self.clear_cache),
            ("DNS", self.dns_lookup),
            ("端口", self.open_ports),
        ]
        for label, callback in quick_ops:
            btn = SmallButton(text=label)
            btn.bind(on_press=lambda x, cb=callback: cb())
            bottom.add_widget(btn)
        self.add_widget(bottom)

    def _show(self, title, cmd, root=True, timeout=8):
        """通用：执行命令并格式化显示"""
        self.scroll.text = f"[color=888888]正在执行 {esc(title)}...[/color]"
        result = run_cmd(cmd, root=root, timeout=timeout)
        self.scroll.text = (
            f"[color={T.ACCENT_HEX}]━━ {esc(title)} ━━[/color]\n\n"
            f"{esc(result) if result else '[color=888888]（无输出）[/color]'}"
        )

    def device_info(self):
        cmds = [
            "echo '设备型号:  '$(getprop ro.product.model)",
            "echo '制造商:    '$(getprop ro.product.manufacturer)",
            "echo '品牌:      '$(getprop ro.product.brand)",
            "echo 'Android:   '$(getprop ro.build.version.release)",
            "echo 'SDK:       '$(getprop ro.build.version.sdk)",
            "echo '安全补丁:  '$(getprop ro.build.version.security_patch)",
            "echo '构建号:    '$(getprop ro.build.display.id)",
            "echo '处理器:    '$(getprop ro.product.board)",
            "echo 'ABI:       '$(getprop ro.product.cpu.abi)",
            "echo '序列号:    '$(getprop ro.serialno)",
            "echo '蓝牙名称:  '$(getprop net.bt.name)",
        ]
        self._show("设备信息", " && ".join(cmds))

    def wifi_info(self):
        cmds = [
            "echo '── WiFi 状态 ──'",
            "ip addr show wlan0 2>/dev/null || echo 'WiFi 未连接'",
            "echo ''",
            "echo '── DNS 服务器 ──'",
            "getprop net.dns1",
            "getprop net.dns2",
            "echo ''",
            "echo '── 网关 ──'",
            "ip route | head -3",
        ]
        self._show("WiFi 信息", " && ".join(cmds))

    def storage_info(self):
        self._show("存储详情", "df -h 2>/dev/null")

    def battery_detail(self):
        self._show("电池详情", "dumpsys battery 2>/dev/null", timeout=10)

    def list_apps(self):
        self._show(
            "已装应用（前30个）",
            "pm list packages -3 to_bottom())
        bb.add_widget(sb2)
        self.add_widget(bb)

        self.paused = False
        self.filter_on = False
        self.last_mt = 0
        Clock.schedule_interval(self.update, 0.5)

    def toggle_pause(self, *args):
        self.paused = not self.paused
        if self.paused:
            self.pbtn.text = "▶ 继续"
            self.pbtn.background_color = T.BTN_WARN
        else:
            self.pbtn.text = "⏸ 暂停"
            self.pbtn.background_color = T.BTN_PRIMARY

    def toggle_filter(self, *args):
        self.filter_on = not self.filter_on
        if self.filter_on:
            self.fbtn.text = "● 过滤:开"
            self.fbtn.background_color = T.BTN_SUCCESS
        else:
            self.fbtn.text = "◯ 过滤:关"
            self.fbtn.background_color = T.BTN_NEUTRAL
        self.last_mt = 0

    def update(self, dt):
        if self.paused:
            return
        try:
            if not os.path.exists(LOG_PATH):
                self.scroll.text = (
                    f"[color={T.YELLOW_HEX}]日志文件不存在[/color]\n"
                    f"路径：{esc(LOG_PATH)}"
                )
                self.status.text = f"[color={T.YELLOW_HEX}]◇ 文件未找到[/color]"
                return

            st = os.stat(LOG_PATH)
            if st.st_mtime == self.last_mt:
                return
            self.last_mt = st.st_mtime

            lines = tail_read(LOG_PATH, MAX_LINES)
            if not lines:
                self.scroll.text = "[color=888888]日志文件为空[/color]"
                return

            kw = self.search.text.strip()
            if self.filter_on and kw:
                lines = [l for l in lines if kw.lower() in l.lower()]

            display = []
            for line in lines:
                line = line.rstrip('\n\r')
                safe = esc(line)
                colored = colorize(safe)
                if kw and kw.lower() in line.lower():
                    colored = f"[color=00ffff]▸[/color] {colored}"
                display.append(colored)

            self.scroll.text = '\n'.join(display)

            t = time.strftime("%H:%M:%S", time.localtime(st.st_mtime))
            sz = format_size(st.st_size)
            fi = f" | 过滤后 {len(display)} 行" if (self.filter_on and kw) else ""
            self.status.text = (
                f"[color={T.ACCENT_HEX}]◇ {sz} | "
                f"{len(lines)} 行{fi} | {t}[/color]"
            )
            self.scroll.scroll_to_bottom()
        except PermissionError:
            self.scroll.text = (
                f"[color={T.RED_HEX}]权限不足，请授权文件访问[/color]"
            )
        except Exception as e:
            log_crash(f"日志查看: {traceback.format_exc()}")
            self.scroll.text = (
                f"[color={T.RED_HEX}]出错: {esc(str(e))}[/color]"
            )