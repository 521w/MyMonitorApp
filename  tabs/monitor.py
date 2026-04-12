"""标签页：系统监控"""

from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
import traceback

from utils import run_cmd, read_file_safe, esc, bar, log_crash


class SystemMonitorTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=8, spacing=6, **kwargs)
        self.prev_cpu = None

        scroll = ScrollView(size_hint=(1, 1))
        self.info = Label(
            text="正在加载...", size_hint_y=None,
            halign="left", valign="top",
            markup=True, font_size="14sp",
        )
        self.info.bind(
            texture_size=lambda *a: setattr(
                self.info, 'height', self.info.texture_size[1] + 40
            )
        )
        scroll.bind(
            width=lambda inst, w: setattr(
                self.info, 'text_size', (w - 16, None)
            )
        )
        scroll.add_widget(self.info)
        self.add_widget(scroll)

        btn = Button(
            text="手动刷新", size_hint_y=None, height=48,
            font_size="14sp", background_color=(0.2, 0.5, 0.8, 1),
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
            cc = "44ff44" if cpu < 50 else ("ffaa00" if cpu < 80 else "ff4444")

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
            mc = "44ff44" if mp < 60 else ("ffaa00" if mp < 85 else "ff4444")

            # 电池
            bb = '/sys/class/power_supply/battery'
            bl = read_file_safe(f'{bb}/capacity') or '?'
            bs = read_file_safe(f'{bb}/status') or '?'
            bt_raw = read_file_safe(f'{bb}/temp')
            bt = f"{int(bt_raw) / 10:.1f}" if bt_raw.isdigit() else '?'
            bs_cn = {'Charging': '充电中', 'Discharging': '放电中',
                     'Full': '已充满', 'Not charging': '未充电'}.get(bs, bs)

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
                uptime = f"{secs // 3600}小时 {(secs % 3600) // 60}分钟"
            else:
                uptime = '?'

            # 内核
            kv = read_file_safe('/proc/version')
            kernel = kv.split()[2] if kv and len(kv.split()) > 2 else '?'

            # 磁盘
            disk = run_cmd("df -h /data /sdcard 2>/dev/null | tail -2")

            # 网络
            net = run_cmd(
                "cat /proc/net/dev | awk 'NR>2{printf \"%s 接收:%s 发送:%s\\n\",$1,$2,$10}'"
            )

            self.info.text = (
                f"[b][color=88ccff]━━━ 系统监控仪表盘 ━━━[/color][/b]\n\n"
                f"[b]处理器[/b]\n"
                f"[color={cc}]  |{bar(cpu)}| {cpu}%[/color]\n\n"
                f"[b]内存[/b]\n"
                f"[color={mc}]  |{bar(mp)}| {mp}%[/color]\n"
                f"  已用 {mu // 1024}MB / 共 {mt // 1024}MB\n\n"
                f"[b]电池[/b]\n"
                f"  电量 {esc(bl)}% | {esc(bs_cn)} | 温度 {esc(bt)}°C\n\n"
                f"[b]处理器温度[/b]  {esc(ct)}°C\n"
                f"[b]运行时间[/b]    {esc(uptime)}\n"
                f"[b]内核版本[/b]    {esc(kernel)}\n\n"
                f"[b]磁盘空间[/b]\n  {esc(disk)}\n\n"
                f"[b]网络流量[/b]\n  {esc(net)}\n"
            )
        except Exception as e:
            log_crash(f"系统监控: {traceback.format_exc()}")
            self.info.text = f"[color=ff4444]读取出错: {esc(str(e))}[/color]"