"""
Python Monitor v3.3 - Root 增强版（多文件结构）
"""

import os
import traceback

from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.core.text import LabelBase

from utils import request_android_perms, log_crash, CRASH_LOG


# ============================================================
# 中文字体注册 - 解决乱码
# ============================================================
def setup_chinese_font():
    """从系统或应用内查找中文字体并注册为默认字体"""

    # 1. 先检查应用内置字体（构建时下载的备用字体）
    app_dir = os.path.dirname(os.path.abspath(__file__))
    bundled_fonts = [
        os.path.join(app_dir, 'chinese.ttf'),
        os.path.join(app_dir, 'chinese.otf'),
    ]
    for path in bundled_fonts:
        if os.path.exists(path):
            try:
                LabelBase.register('Roboto', path)
                return True
            except Exception:
                continue

    # 2. 尝试 Android 系统中文字体（按可靠性排序）
    system_fonts = [
        '/system/fonts/NotoSansSC-Regular.otf',
        '/system/fonts/NotoSansHans-Regular.otf',
        '/system/fonts/DroidSansFallback.ttf',
        '/system/fonts/NotoSansCJK-Regular.ttc',
        '/system/fonts/DroidSansChinese.ttf',
        '/system/fonts/NotoSansSC-Medium.otf',
        '/system/fonts/Miui-Regular.ttf',
        '/system/fonts/RobotoFallback-Regular.ttf',
    ]
    for path in system_fonts:
        if os.path.exists(path):
            try:
                LabelBase.register('Roboto', path)
                return True
            except Exception:
                continue

    # 3. 搜索系统字体目录中任何中文相关字体
    font_dir = '/system/fonts'
    if os.path.isdir(font_dir):
        keywords = ['cjk', 'sc', 'hans', 'chinese', 'fallback', 'miui']
        try:
            for f in sorted(os.listdir(font_dir)):
                lower = f.lower()
                if any(kw in lower for kw in keywords):
                    full_path = os.path.join(font_dir, f)
                    try:
                        LabelBase.register('Roboto', full_path)
                        return True
                    except Exception:
                        continue
        except Exception:
            pass

    return False


# 在任何 UI 创建之前注册中文字体
_font_ok = setup_chinese_font()

# 延迟导入 tabs（确保字体已注册）
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

            if not _font_ok:
                log_crash("警告: 未找到中文字体，界面可能显示乱码")

            return tp

        except Exception as e:
            log_crash(f"启动崩溃: {traceback.format_exc()}")
            return Label(
                text=f"Error:\n{e}\n\nSee {CRASH_LOG}",
                halign="center", valign="middle",
            )


if __name__ == "__main__":
    try:
        MonitorApp().run()
    except Exception as e:
        log_crash(f"致命错误: {traceback.format_exc()}")