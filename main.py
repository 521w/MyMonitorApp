from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
import os

LOG_PATH = "/sdcard/py_monitor.log"

class LogView(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.scroll = ScrollView(size_hint=(1, 1))
        self.label = Label(size_hint_y=None, text="", halign="left", valign="top")
        self.label.bind(texture_size=self._update_height)
        self.scroll.add_widget(self.label)
        self.add_widget(self.scroll)
        Clock.schedule_interval(self.update_log, 0.5)

    def _update_height(self, *args):
        self.label.height = self.label.texture_size[1]
        self.label.text_size = (self.scroll.width, None)

    def update_log(self, dt):
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()[-300:]
            self.label.text = "".join(lines)

class MonitorApp(App):
    def build(self):
        return LogView()

if __name__ == "__main__":
    MonitorApp().run()from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
import os

LOG_PATH = "/sdcard/py_monitor.log"

class LogView(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.scroll = ScrollView(size_hint=(1, 1))
        self.label = Label(size_hint_y=None, text="", halign="left", valign="top")
        self.label.bind(texture_size=self._update_height)
        self.scroll.add_widget(self.label)
        self.add_widget(self.scroll)
        Clock.schedule_interval(self.update_log, 0.5)

    def _update_height(self, *args):
        self.label.height = self.label.texture_size[1]
        self.label.text_size = (self.scroll.width, None)

    def update_log(self, dt):
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()[-300:]
            self.label.text = "".join(lines)

class MonitorApp(App):
    def build(self):
        return LogView()

if __name__ == "__main__":
    MonitorApp().run()
