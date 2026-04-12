"""
Python Monitor v3.3 - Root 增强版（多文件结构）
"""

from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.label import Label
from kivy.core.window import Window
import traceback

from utils import request_android_perms, log_crash, CRASH_LOG
from tabs import (
    SystemMonitorTab, ProcessTab, TerminalTab,
    LogViewerTab, LogcatTab, ToolboxTab,
)


class MonitorApp(App):
    def build(self):
        try:
            Window.clearcolor = (0.08, 0.08, 0.12, 1)
            self.title = "Python Monitor"
            request_android_perms()

            tp = TabbedPanel(do_default_tab=False)
            tabs = [
                ("监控", SystemMonitorTab()),
                ("进程", ProcessTab()),
                ("终端", TerminalTab()),
                ("日志", LogViewerTab()),
                ("系统", LogcatTab()),
                ("工具", ToolboxTab()),
            ]
            for title, content in tabs:
                tab = TabbedPanelItem(text=title, font_size="13sp")
                tab.add_widget(content)
                tp.add_widget(tab)
            return tp

        except Exception as e:
            log_crash(f"启动崩溃: {traceback.format_exc()}")
            return Label(
                text=f"启动出错：\n{e}\n\n请查看 {CRASH_LOG}",
                halign="center", valign="middle",
            )


if __name__ == "__main__":
    try:
        MonitorApp().run()
    except Exception as e:
        log_crash(f"致命错误: {traceback.format_exc()}")