from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
import os

# Android 权限请求（仅在 Android 上生效）
try:
    from android.permissions import request_permissions, Permission, check_permission
    from android.storage import primary_external_storage_path
    ANDROID = True
except ImportError:
    ANDROID = False

LOG_PATH = "/sdcard/py_monitor.log"


class LogView(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)

        self.scroll = ScrollView(size_hint=(1, 1))
        self.label = Label(
            size_hint_y=None,
            text="正在等待日志...",
            halign="left",
            valign="top",
            markup=True,
        )
        self.label.bind(texture_size=self._update_height)
        self.scroll.bind(width=self._update_text_width)
        self.scroll.add_widget(self.label)
        self.add_widget(self.scroll)

        # 先请求权限，再开始读日志
        if ANDROID:
            request_permissions(
                [Permission.MANAGE_EXTERNAL_STORAGE],
                callback=self._perm_callback,
            )
        else:
            Clock.schedule_interval(self.update_log, 0.5)

    def _perm_callback(self, permissions, grant_results):
        """权限回调：无论是否授权都开始轮询（读不到会显示提示）"""
        Clock.schedule_interval(self.update_log, 0.5)

    def _update_height(self, *args):
        self.label.height = self.label.texture_size[1]

    def _update_text_width(self, instance, width):
        """ScrollView 宽度变化时同步 Label 的 text_size"""
        self.label.text_size = (width, None)

    def update_log(self, dt):
        try:
            if os.path.exists(LOG_PATH):
                with open(LOG_PATH, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()[-300:]
                self.label.text = "".join(lines)
            else:
                self.label.text = (
                    f"日志文件不存在：{LOG_PATH}\n\n"
                    "请确认监控脚本已运行并输出到该路径。"
                )
        except PermissionError:
            self.label.text = (
                "[color=ff4444]权限不足[/color]\n\n"
                "请到 系统设置 → 应用 → Python Monitor → 权限\n"
                "→ 开启「所有文件访问」权限。"
            )
        except Exception as e:
            self.label.text = f"读取日志出错：{type(e).__name__}: {e}"


class MonitorApp(App):
    def build(self):
        return LogView()


if __name__ == "__main__":
    MonitorApp().run()