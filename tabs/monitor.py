"""标签页：系统监控 - 卡片式仪表盘"""

from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
import traceback

import theme as T
from utils import run_cmd, read_file_safe, esc, bar, color_val, log_crash
from widgets import StyledCard, SectionHeader, IconButton, ScrollLabel, Divider


class SystemMonitorTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=6, spacing=6, **kwargs)
        self.prev_cpu = None

        self.scroll = ScrollLabel(font_size=T.FONT_MD)
        self.scroll.text = "[color=888888]正在加载系统信息...[/color]"
        self.add_widget(self.scroll)

        btn = IconButton(
            icon="↻", text="手动刷新",
            background_color=T.BTN_PRIMARY,
        )
        btn.bind(on_press=lambda x: self.update(0))
        self.add_widget(btn)

        Clock.schedule_interval(self.update, 3)

    def _cpu_sample(self):
        line = read_file_safe('/proc/stat')
        if not line:
            return None
        first = line.split('\n')[0].split()
        if len(first) < 5:
            return None
        vals = list(map(int, first[1:8] if len(first) >= 8 else first[1:]))
        return sum(vals), vals[3]

    def update(self, dt):
        try:
            # CPU
            s = self._cpu_sample()
            cpu = 0
            if s and self.prev_cpu:
                td = s[0] - self.prev_cpu[0]
                idd = s[1] - self.prev_cpu[1]
                cpu = round((1 - idd / td) * 100, 1) if td > 0 else 0
            self.prev_cpu = s
            cc = color_val(cpu)

            # 内存
            mi = {}
            for line in read_file_safe('/proc/meminfo').split('\n'):
                p = line.split()
                if len(p) >= 2:
                    mi[p[0].rstrip(':')] = int(p[1])
            mt = mi.get('MemTotal', 1)
            ma = mi.get('MemAvailable', mi.get('MemFree', 0))
            mu = mt - ma
            mp = round(mu / mt * 100, 1) if mt > 0 else 0
            mc = color_val(mp, 60, 85)

            # 电池
            bb = '/sys/class/power_supply/battery'
            bl = read_file_safe(f'{bb}/capacity') or '?'
            bs = read_file_safe(f'{bb}/status') or '?'
            bt_raw = read_file_safe(f'{bb}/temp')
            bt = f"{int(bt_raw) / 10:.1f}" if bt_raw.isdigit() else '?'
            bs_cn = {'Charging': '⚡ 充电中', 'Discharging': '🔋 放电中',
                     'Full': '✓ 已充满', 'Not charging': '─ 未充电'}.get(bs, bs)

            # CPU 温度
            ct = '?'
            for p in ['/sys/class/thermal/thermal_zone0/temp']:
                v = read_file_safe(p)
                if v and v.isdigit():
                    t = int(v)
                    ct = f"{t / 1000:.1f}" if t > 1000 else str(t)
                    break

            # 运行时间
            ur = read_file_safe('/proc/uptime')
            if ur:
                secs = int(float(ur.split()[0]))
                d = secs // 86400
                h = (secs % 86400) // 3600
                m = (secs % 3600) // 60
                uptime = f"{d}天 {h}时 {m}分" if d > 0 else f"{h}时 {m}分"
            else:
                uptime = '?'

            # 内核
            kv = read_file_safe('/proc/version')
            kernel = kv.split()[2] if kv and len(kv.split()) > 2 else '?'

            # 磁盘
            disk = run_cmd("df -h /data /sdcard 2>/dev/null | tail -2")

            # 网络 ← 关键修复：加 root=True
            net = run_cmd(
                "cat /proc/net/dev | awk 'NR>2{printf \"%s  ↓%s  ↑%s\\n\",$1,$2,$10}'",
                root=True,
            )

            self.scroll.text = (
                f"[b][color={T.ACCENT_HEX}]"
                f"┌──────────────────────────┐\n"
                f"│      系 统 监 控 仪 表 盘      │\n"
                f"└──────────────────────────┘"
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