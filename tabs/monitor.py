"""系统监控"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.metrics import dp
import subprocess, os, socket
import theme as T
from widgets import StyledCard, StyledLabel, StyledButton


class SystemMonitorTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(8), spacing=dp(8), **kwargs)

        scroll = ScrollView()
        self.content = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=dp(8), padding=[0, dp(4)]
        )
        self.content.bind(minimum_height=self.content.setter("height"))

        cards = {
            "cpu": ("CPU: 读取中...", dp(130)),
            "mem": ("内存: 读取中...", dp(100)),
            "bat": ("电池: 读取中...", dp(80)),
            "disk": ("存储: 读取中...", dp(80)),
            "net": ("网络: 读取中...", dp(100)),
        }
        for key, (txt, h) in cards.items():
            card = StyledCard(size_hint_y=None, height=h)
            lbl = StyledLabel(text=txt, font_size=T.FONT_MD, halign="left", valign="top")
            lbl.bind(size=lbl.setter("text_size"))
            card.add_widget(lbl)
            self.content.add_widget(card)
            setattr(self, f"{key}_label", lbl)

        btn = StyledButton(text="🔄 刷新")
        btn.bind(on_release=lambda x: self.refresh())
        self.content.add_widget(btn)

        scroll.add_widget(self.content)
        self.add_widget(scroll)
        Clock.schedule_interval(self.refresh, 3)

    def _run(self, cmd):
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            return r.stdout.strip()
        except Exception:
            return ""

    def _color(self, pct):
        if pct < 60:
            return T.GREEN_HEX
        return T.YELLOW_HEX if pct < 85 else T.RED_HEX

    def refresh(self, *args):
        A = T.ACCENT_HEX
        G = T.GREEN_HEX

        # CPU
        try:
            loads = (self._run("cat /proc/loadavg") or "0 0 0").split()
            cores = self._run("nproc") or "?"
            freq = self._run("cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq")
            freq_s = f"{int(freq)//1000}MHz" if freq.isdigit() else "N/A"
            temp = self._run("cat /sys/class/thermal/thermal_zone0/temp")
            temp_s = f"{int(temp)/1000:.1f}°C" if temp.isdigit() else "N/A"
            self.cpu_label.text = (
                f"[color={A}]━━ CPU ━━[/color]\n"
                f"核心: [color={G}]{cores}[/color]   频率: [color={G}]{freq_s}[/color]\n"
                f"温度: [color={G}]{temp_s}[/color]\n"
                f"负载: [color={G}]{loads[0]}[/color] / [color={G}]{loads[1]}[/color] / [color={G}]{loads[2]}[/color]"
            )
        except Exception as e:
            self.cpu_label.text = f"[color={T.RED_HEX}]CPU 读取失败: {e}[/color]"

        # Memory
        try:
            mi = {}
            with open("/proc/meminfo") as f:
                for line in f:
                    p = line.split(":")
                    if len(p) == 2:
                        mi[p[0].strip()] = int(p[1].strip().split()[0])
            total = mi.get("MemTotal", 0) // 1024
            avail = mi.get("MemAvailable", 0) // 1024
            used = total - avail
            pct = (used / total * 100) if total else 0
            c = self._color(pct)
            self.mem_label.text = (
                f"[color={A}]━━ 内存 ━━[/color]\n"
                f"已用: [color={c}]{used}MB[/color] / {total}MB  ([color={c}]{pct:.1f}%[/color])\n"
                f"可用: [color={G}]{avail}MB[/color]"
            )
        except Exception as e:
            self.mem_label.text = f"[color={T.RED_HEX}]内存读取失败: {e}[/color]"

        # Battery
        try:
            level = self._run("cat /sys/class/power_supply/battery/capacity") or "N/A"
            status = self._run("cat /sys/class/power_supply/battery/status") or "N/A"
            temp = self._run("cat /sys/class/power_supply/battery/temp")
            temp_s = f"{int(temp)/10:.1f}°C" if temp and temp.lstrip('-').isdigit() else "N/A"
            c = G if level.isdigit() and int(level) > 30 else T.YELLOW_HEX if level.isdigit() and int(level) > 15 else T.RED_HEX
            self.bat_label.text = (
                f"[color={A}]━━ 电池 ━━[/color]\n"
                f"电量: [color={c}]{level}%[/color]   状态: {status}   温度: {temp_s}"
            )
        except Exception as e:
            self.bat_label.text = f"[color={T.RED_HEX}]电池读取失败: {e}[/color]"

        # Disk
        try:
            st = os.statvfs("/data")
            total_g = (st.f_blocks * st.f_frsize) / (1024 ** 3)
            free_g = (st.f_bavail * st.f_frsize) / (1024 ** 3)
            used_g = total_g - free_g
            pct = (used_g / total_g * 100) if total_g else 0
            c = self._color(pct)
            self.disk_label.text = (
                f"[color={A}]━━ 存储 ━━[/color]\n"
                f"已用: [color={c}]{used_g:.1f}GB[/color] / {total_g:.1f}GB  "
                f"([color={c}]{pct:.1f}%[/color])"
            )
        except Exception as e:
            self.disk_label.text = f"[color={T.RED_HEX}]存储读取失败: {e}[/color]"

        # Network
        try:
            # ★ 用 Python socket 获取本机IP（最可靠，不依赖shell命令格式）
            ip = "N/A"
            try:
                import socket
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(2)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                s.close()
            except Exception:
                # fallback 1: ip addr
                ip = self._run(
                    "ip -4 addr show 2>/dev/null | grep 'inet ' | grep -v '127.0.0.1' "
                    "| awk '{print $2}' | cut -d/ -f1 | head -1"
                ) or "N/A"
                if ip == "N/A":
                    # fallback 2: ifconfig
                    ip = self._run(
                        "ifconfig 2>/dev/null | grep 'inet addr' | grep -v '127.0.0.1' "
                        "| awk '{print $2}' | cut -d: -f2 | head -1"
                    ) or "N/A"

            # ★ 动态检测活跃网卡，不硬编码 wlan0
            rx_mb = 0
            tx_mb = 0
            iface = "N/A"
            # 按优先级尝试：wlan0(WiFi) → rmnet_data0(4G) → 其他
            for try_iface in ["wlan0", "rmnet_data0", "rmnet0", "eth0", "ccmni0"]:
                rx_path = f"/sys/class/net/{try_iface}/statistics/rx_bytes"
                if os.path.exists(rx_path):
                    iface = try_iface
                    rx = self._run(f"cat /sys/class/net/{try_iface}/statistics/rx_bytes")
                    tx = self._run(f"cat /sys/class/net/{try_iface}/statistics/tx_bytes")
                    rx_mb = int(rx) / (1024 ** 2) if rx and rx.isdigit() else 0
                    tx_mb = int(tx) / (1024 ** 2) if tx and tx.isdigit() else 0
                    break

            # 如果上面都没找到，扫描 /sys/class/net/ 下所有网卡
            if iface == "N/A":
                try:
                    for name in os.listdir("/sys/class/net/"):
                        if name == "lo":
                            continue
                        rx_path = f"/sys/class/net/{name}/statistics/rx_bytes"
                        if os.path.exists(rx_path):
                            iface = name
                            rx = self._run(f"cat {rx_path}")
                            tx = self._run(f"cat /sys/class/net/{name}/statistics/tx_bytes")
                            rx_mb = int(rx) / (1024 ** 2) if rx and rx.isdigit() else 0
                            tx_mb = int(tx) / (1024 ** 2) if tx and tx.isdigit() else 0
                            break
                except Exception:
                    pass

            self.net_label.text = (
                f"[color={A}]━━ 网络 ━━[/color]\n"
                f"IP: [color={G}]{ip}[/color]\n"
                f"网卡: [color={G}]{iface}[/color]\n"
                f"↓ {rx_mb:.1f}MB   ↑ {tx_mb:.1f}MB"
            )
        except Exception as e:
            self.net_label.text = f"[color={T.RED_HEX}]网络读取失败: {e}[/color]"
        except Exception as e:
            self.net_label.text = f"[color={T.RED_HEX}]网络读取失败: {e}[/color]"