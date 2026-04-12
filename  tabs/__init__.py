"""标签页模块"""

from tabs.monitor import SystemMonitorTab
from tabs.process import ProcessTab
from tabs.terminal import TerminalTab
from tabs.logviewer import LogViewerTab
from tabs.logcat import LogcatTab
from tabs.toolbox import ToolboxTab

__all__ = [
    'SystemMonitorTab',
    'ProcessTab',
    'TerminalTab',
    'LogViewerTab',
    'LogcatTab',
    'ToolboxTab',
]