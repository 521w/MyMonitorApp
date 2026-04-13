from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
import theme as T
from widgets import BgContainer, TopBar, BottomNav
from tabs import (
    SystemMonitorTab, ProcessTab, TerminalTab,
    LogViewerTab, LogcatTab, ToolboxTab, SettingsTab,
)


class MyMonitorApp(App):
    def build(self):
        self.title = "性能监控"
        cfg = T.load_config()

        self.bg = BgContainer()

        self.topbar = TopBar(title="📊 系统监控")
        self.bg.add_widget(self.topbar)

        self.sm = ScreenManager(transition=NoTransition())
        tab_classes = [
            SystemMonitorTab, ProcessTab, TerminalTab,
            LogViewerTab, LogcatTab, ToolboxTab, SettingsTab,
        ]
        self.tab_names = [
            "monitor", "process", "terminal",
            "logviewer", "logcat", "toolbox", "settings",
        ]
        self.tab_titles = [
            "📊 系统监控", "⚙ 进程管理", "💻 终端",
            "📋 日志查看", "📱 系统日志", "🔧 工具箱", "⚡ 设置",
        ]

        for cls, name in zip(tab_classes, self.tab_names):
            screen = Screen(name=name)
            tab = cls()
            if name == "settings":
                tab.app = self
            screen.add_widget(tab)
            self.sm.add_widget(screen)

        self.bg.add_widget(self.sm)

        self.navbar = BottomNav(callback=self.switch_tab)
        self.bg.add_widget(self.navbar)

        # 恢复保存的背景
        if cfg.get("bg_image"):
            self.bg.set_bg_image(cfg["bg_image"])
        elif cfg.get("bg_color"):
            self.bg.set_bg_color(tuple(cfg["bg_color"]))

        return self.bg

    def switch_tab(self, index):
        self.sm.current = self.tab_names[index]
        self.topbar.set_title(self.tab_titles[index])


if __name__ == "__main__":
    MyMonitorApp().run()