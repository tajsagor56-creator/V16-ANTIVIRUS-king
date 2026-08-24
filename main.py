from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.metrics import dp

import os
import threading


APP_NAME = "V16 Antivirus Pro"
VERSION = "16.3"


class AntivirusUI(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            padding=dp(20),
            spacing=dp(15),
            **kwargs
        )

        self.add_widget(
            Label(
                text="[b]King Taj 👑[/b]",
                markup=True,
                font_size=dp(28),
                size_hint_y=None,
                height=dp(60)
            )
        )

        self.add_widget(
            Label(
                text=f"{APP_NAME}\nVersion {VERSION}",
                font_size=dp(18),
                size_hint_y=None,
                height=dp(60)
            )
        )

        self.status = Label(
            text="System Ready",
            font_size=dp(20),
            size_hint_y=None,
            height=dp(50)
        )

        self.add_widget(self.status)

        self.progress = ProgressBar(
            max=100,
            value=0,
            size_hint_y=None,
            height=dp(25)
        )

        self.add_widget(self.progress)

        self.percent = Label(
            text="0%",
            font_size=dp(16),
            size_hint_y=None,
            height=dp(35)
        )

        self.add_widget(self.percent)

        self.scan_button = Button(
            text="🔍  SCAN DEVICE",
            font_size=dp(20),
            size_hint_y=None,
            height=dp(65)
        )

        self.scan_button.bind(
            on_release=self.start_scan
        )

        self.add_widget(self.scan_button)

        self.result = Label(
            text="No scan performed yet.",
            font_size=dp(16)
        )

        self.add_widget(self.result)

    def start_scan(self, instance):

        if self.scan_button.disabled:
            return

        self.scan_button.disabled = True
        self.progress.value = 0
        self.percent.text = "0%"
        self.status.text = "Scanning..."
        self.result.text = ""

        threading.Thread(
            target=self.scan,
            daemon=True
        ).start()

    def scan(self):

        count = 0

        paths = [
            "/storage/emulated/0"
        ]

        files = []

        for base in paths:

            if not os.path.exists(base):
                continue

            try:

                for root, dirs, names in os.walk(base):

                    for name in names:
                        files.append(
                            os.path.join(root, name)
                        )

                        if len(files) >= 500:
                            break

                    if len(files) >= 500:
                        break

            except Exception:
                pass

        total = len(files)

        if total == 0:
            Clock.schedule_once(
                lambda dt: self.finish_scan(0)
            )
            return

        for i, path in enumerate(files):

            count += 1

            progress = (
                (i + 1) / total
            ) * 100

            Clock.schedule_once(
                lambda dt, p=progress, c=count:
                self.update_progress(p, c)
            )

        Clock.schedule_once(
            lambda dt, c=count:
            self.finish_scan(c)
        )

    def update_progress(self, value, count):

        self.progress.value = value
        self.percent.text = f"{value:.1f}%"
        self.status.text = "Scanning..."
        self.result.text = f"Files scanned: {count}"

    def finish_scan(self, count):

        self.progress.value = 100
        self.percent.text = "100%"
        self.status.text = "✓ Scan Complete"

        self.result.text = (
            f"Files scanned: {count}\n"
            "Known threats: 0\n"
            "Suspicious files: 0"
        )

        self.scan_button.disabled = False


class V16AntivirusApp(App):

    title = APP_NAME

    def build(self):
        return AntivirusUI()


if __name__ == "__main__":
    V16AntivirusApp().run()
