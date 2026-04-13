"""工具箱"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
import subprocess, os
import theme as T
from widgets import StyledCard, StyledLabel, StyledButton, StyledTextInput


class ToolboxTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(8), spacing=dp(8), **kwargs)

        scroll = ScrollView()
        self.content = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=dp(8)
        )
        self.content.bind(minimum_height=self.content.setter("height"))

        # ---- 设备信息卡片 ----
        info_card = StyledCard(size_hint_y=None, height=dp(44))
        btn_info = StyledButton(text="📱 查看设备信息")
        btn_info.bind(on_release=lambda x: self._device_info())
        info_card.add_widget(btn_info)
        self.content.add_widget(info_card)

        # ---- Ping 工具 ----
        ping_card = StyledCard(size_hint_y=None, height=dp(90))
        ping_card.add_widget(
            StyledLabel(text=f"[color={T.ACCENT_HEX}]🌐 Ping 测试[/color]",
                        size_hint_y=None, height=dp(24), font_size=T.FONT_SM)
        )
        ping_bar = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        self.ping_input = StyledTextInput(text="8.8.8.8", hint_text="IP/域名", size_hint_x=0.65)
        btn_ping = StyledButton(text="Ping", size_hint_x=0.35)
        btn_ping.bind(on_release=lambda x: self._ping())
        ping_bar.add_widget(self.ping_input)
        ping_bar.add_widget(btn_ping)
        ping_card.add_widget(ping_bar)
        self.content.add_widget(ping_card)

        # ---- 端口扫描 ----
        port_card = StyledCard(size_hint_y=None, height=dp(90))
        port_card.add_widget(
            StyledLabel(text=f"[color={T.ACCENT_HEX}]🔌 端口检测[/color]",
                        size_hint_y=None, height=dp(24), font_size=T.FONT_SM)
        )
        port_bar = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        self.port_host = StyledTextInput(text="127.0.0.1", hint_text="主机", size_hint_x=0.45)
        self.port_num = StyledTextInput(text="8080", hint_text="端口", size_hint_x=0.25)
        btn_port = StyledButton(text="检测", size_hint_x=0.3)
        btn_port.bind(on_release=lambda x: self._check_port())
        port_bar.add_widget(self.port_host)
        port_bar.add_widget(self.port_num)
        port_bar.add_widget(btn_port)
        port_card.add_widget(port_bar)
        self.content.add_widget(port_card)

        # ---- 文件浏览 ----
        file_card = StyledCard(size_hint_y=None, height=dp(90))
        file_card.add_widget(
            StyledLabel(text=f"[color={T.ACCENT_HEX}]📂 文件浏览[/color]",
                        size_hint_y=None, height=dp(24), font_size=T.FONT_SM)
        )
        file_bar = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        self.dir_input = StyledTextInput(text="/sdcard", hint_text="目录路径", size_hint_x=0.65)
        btn_ls = StyledButton(text="列出", size_hint_x=0.35)
        btn_ls.bind(on_release=lambda x: self._list_dir())
        file_bar.add_widget(self.dir_input)
        file_bar.add_widget(btn_ls)
        file_card.add_widget(file_bar)
        self.content.add_widget(file_card)

        # ---- 快捷命令 ----
        quick_card = StyledCard(size_hint_y=None, height=dp(100))
        quick_card.add_widget(
            StyledLabel(text=f"[color={T.ACCENT_HEX}]⚡ 快捷命令[/color]",
                        size_hint_y=None, height=dp(24), font_size=T.FONT_SM)
        )
        row1 = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(4))
        cmds = [
            ("IP地址", "ip addr show | grep inet"),
            ("DNS", "getprop net.dns1"),
            ("开机时长", "uptime"),
        ]
        for name, cmd in cmds:
            b = StyledButton(text=name, bg_color=T.BTN_NEUTRAL)
            b._cmd = cmd
            b.bind(on_release=lambda x: self._quick(x))
            row1.add_widget(b)
        quick_card.add_widget(row1)
        self.content.add_widget(quick_card)

        # ---- 结果显示 ----
        self.result_card = StyledCard(size_hint_y=None, height=dp(200))
        self.result_label = StyledLabel(
            text=f"[color={T.ACCENT_HEX}]结果会显示在这里[/color]",
            halign="left", valign="top", font_size=T.FONT_SM,
        )
        self.result_label.bind(size=self.result_label.setter("text_size"))
        self.result_card.add_widget(self.result_label)
        self.content.add_widget(self.result_card)

        scroll.add_widget(self.content)
        self.add_widget(scroll)

    def _run(self, cmd):
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            return r.stdout.strip() or r.stderr.strip()
        except subprocess.TimeoutExpired:
            return "命令超时"
        except Exception as e:
            return str(e)

    def _show(self, text):
        if len(text) > 3000:
            text = text[:3000] + "\n... (截断)"
        self.result_label.text = text
        self.result_card.height = max(dp(200), dp(20) * text.count("\n") + dp(60))

    def _device_info(self):
        lines = []
        props = [
            ("型号", "ro.product.model"),
            ("品牌", "ro.product.brand"),
            ("系统版本", "ro.build.version.release"),
            ("SDK", "ro.build.version.sdk"),
            ("CPU架构", "ro.product.cpu.abi"),
            ("序列号", "ro.serialno"),
        ]
        for name, prop in props:
            val = self._run(f"getprop {prop}") or "N/A"
            lines.append(f"[color={T.ACCENT_HEX}]{name}:[/color] {val}")
        kernel = self._run("uname -r") or "N/A"
        lines.append(f"[color={T.ACCENT_HEX}]内核:[/color] {kernel}")
        self._show("\n".join(lines))

    def _ping(self):
        host = self.ping_input.text.strip()
        if not host:
            self._show(f"[color={T.RED_HEX}]请输入目标地址[/color]")
            return
        self._show(f"[color={T.YELLOW_HEX}]Ping {host} 中...[/color]")
        result = self._run(f"ping -c 4 -W 3 {host}")
        self._show(result)

    def _check_port(self):
        host = self.port_host.text.strip()
        port = self.port_num.text.strip()
        if not host or not port:
            self._show(f"[color={T.RED_HEX}]请输入主机和端口[/color]")
            return
        result = self._run(f"echo | timeout 3 nc -zv {host} {port} 2>&1")
        if "open" in result.lower() or "succeeded" in result.lower():
            self._show(f"[color={T.GREEN_HEX}]{host}:{port} 端口开放[/color]\n{result}")
        else:
            self._show(f"[color={T.RED_HEX}]{host}:{port} 端口关闭或超时[/color]\n{result}")

    def _list_dir(self):
        path = self.dir_input.text.strip()
        if not os.path.isdir(path):
            self._show(f"[color={T.RED_HEX}]目录不存在: {path}[/color]")
            return
        try:
            items = os.listdir(path)
            lines = [f"[color={T.ACCENT_HEX}]📂 {path}  ({len(items)} 项)[/color]", ""]
            for name in sorted(items)[:100]:
                full = os.path.join(path, name)
                if os.path.isdir(full):
                    lines.append(f"[color={T.ACCENT_HEX}]📁[/color] {name}/")
                else:
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
                    lines.append(f"  📄 {name}  [color={T.TEXT_DIM[0]*255:.0f}{T.TEXT_DIM[1]*255:.0f}{T.TEXT_DIM[2]*255:.0f}]({s})[/color]")
            self._show("\n".join(lines))
        except Exception as e:
            self._show(f"[color={T.RED_HEX}]读取失败: {e}[/color]")

    def _quick(self, btn):
        result = self._run(btn._cmd)
        self._show(result)