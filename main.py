# ============================================================
# V16 ANTIVIRUS PRO
# Stable Mini Base - V16.4
# ============================================================

import os
import time
import hashlib
import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView


# ============================================================
# APP
# ============================================================

APP_NAME = "V16 Antivirus Pro"
VERSION = "16.4"

CHUNK_SIZE = 1024 * 1024


# ============================================================
# KNOWN MALWARE SHA256
# ============================================================

KNOWN_MALWARE = {
    # এখানে পরে verified SHA-256 hash যোগ করা হবে
}


# ============================================================
# SUSPICIOUS EXTENSIONS
# ============================================================

SUSPICIOUS_EXTENSIONS = {
    ".exe",
    ".scr",
    ".bat",
    ".cmd",
    ".vbs",
    ".ps1",
    ".pif",
}


# ============================================================
# SHA256
# ============================================================

def calculate_sha256(path):

    try:

        sha = hashlib.sha256()

        with open(path, "rb") as file:

            while True:

                data = file.read(CHUNK_SIZE)

                if not data:
                    break

                sha.update(data)

        return sha.hexdigest()

    except Exception:

        return None


# ============================================================
# FILE SCAN
# ============================================================

def scan_file(path):

    result = {
        "file": path,
        "sha256": None,
        "threat": False,
        "suspicious": False,
        "reason": ""
    }

    file_hash = calculate_sha256(path)

    result["sha256"] = file_hash

    if file_hash in KNOWN_MALWARE:

        result["threat"] = True
        result["reason"] = "Known malware SHA-256"

        return result

    extension = os.path.splitext(path)[1].lower()

    if extension in SUSPICIOUS_EXTENSIONS:

        result["suspicious"] = True
        result["reason"] = "Suspicious file extension"

    return result


# ============================================================
# SCAN PATHS
# ============================================================

def get_scan_paths():

    paths = []

    storage = "/storage/emulated/0"

    if os.path.exists(storage):

        paths.append(storage)

    elif os.path.exists("/sdcard"):

        paths.append("/sdcard")

    else:

        paths.append(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )

    return paths


# ============================================================
# FILE COLLECTION
# ============================================================

def collect_files(stop_check):

    files = []

    for base in get_scan_paths():

        if stop_check():
            break

        try:

            for root, dirs, names in os.walk(base):

                if stop_check():
                    break

                dirs[:] = [
                    d for d in dirs
                    if d not in {
                        ".cache",
                        ".thumbnails"
                    }
                ]

                for name in names:

                    if stop_check():
                        break

                    path = os.path.join(root, name)

                    if os.path.isfile(path):

                        files.append(path)

        except Exception:

            continue

    return files


# ============================================================
# SCANNER
# ============================================================

class Scanner:

    def __init__(self, callback):

        self.callback = callback
        self.stop_requested = False

    def stop(self):

        self.stop_requested = True

    def scan(self):

        start_time = time.time()

        files = collect_files(
            lambda: self.stop_requested
        )

        total = len(files)

        scanned = 0
        threats = 0
        suspicious = 0

        results = []

        if total == 0:

            self.callback(
                "done",
                0,
                0,
                0,
                time.time() - start_time,
                results
            )

            return

        for index, path in enumerate(files):

            if self.stop_requested:
                break

            result = scan_file(path)

            scanned += 1

            if result["threat"]:

                threats += 1
                results.append(result)

            elif result["suspicious"]:

                suspicious += 1
                results.append(result)

            progress = (
                (index + 1) / total
            ) * 100

            self.callback(
                "progress",
                progress,
                scanned,
                threats,
                suspicious,
                path
            )

        self.callback(
            "done",
            scanned,
            threats,
            suspicious,
            time.time() - start_time,
            results
        )


# ============================================================
# USER INTERFACE
# ============================================================

class AntivirusUI(BoxLayout):

    def __init__(self, **kwargs):

        super().__init__(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(10),
            **kwargs
        )

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        self.add_widget(
            Label(
                text="[b]King Taj 👑[/b]",
                markup=True,
                font_size=dp(27),
                size_hint_y=None,
                height=dp(55)
            )
        )

        # ----------------------------------------------------
        # VERSION
        # ----------------------------------------------------

        self.add_widget(
            Label(
                text=(
                    f"{APP_NAME}\n"
                    f"Version {VERSION}"
                ),
                font_size=dp(15),
                size_hint_y=None,
                height=dp(55)
            )
        )

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        self.status = Label(
            text="System Ready",
            font_size=dp(18),
            size_hint_y=None,
            height=dp(45)
        )

        self.add_widget(self.status)

        # ----------------------------------------------------
        # PROGRESS
        # ----------------------------------------------------

        self.progress = ProgressBar(
            max=100,
            value=0,
            size_hint_y=None,
            height=dp(25)
        )

        self.add_widget(self.progress)

        self.percent = Label(
            text="0%",
            size_hint_y=None,
            height=dp(30)
        )

        self.add_widget(self.percent)

        # ----------------------------------------------------
        # STATS
        # ----------------------------------------------------

        self.stats = Label(
            text=(
                "Files scanned: 0\n"
                "Threats: 0\n"
                "Suspicious: 0"
            ),
            font_size=dp(16),
            size_hint_y=None,
            height=dp(80)
        )

        self.add_widget(self.stats)

        # ----------------------------------------------------
        # SCAN BUTTON
        # ----------------------------------------------------

        self.scan_button = Button(
            text="🔍  SCAN DEVICE",
            font_size=dp(20),
            size_hint_y=None,
            height=dp(60)
        )

        self.scan_button.bind(
            on_release=self.start_scan
        )

        self.add_widget(self.scan_button)

        # ----------------------------------------------------
        # RESULT AREA
        # ----------------------------------------------------

        scroll = ScrollView()

        self.result = Label(
            text="No scan performed yet.",
            size_hint_y=None,
            halign="left",
            valign="top"
        )

        self.result.bind(
            texture_size=self.result.setter("size")
        )

        scroll.add_widget(self.result)

        self.add_widget(scroll)

        self.scanner = None

    # ========================================================
    # START SCAN
    # ========================================================

    def start_scan(self, instance):

        if self.scanner is not None:
            return

        self.scan_button.disabled = True

        self.progress.value = 0
        self.percent.text = "0%"

        self.status.text = "Collecting files..."

        self.stats.text = (
            "Files scanned: 0\n"
            "Threats: 0\n"
            "Suspicious: 0"
        )

        self.result.text = ""

        self.scanner = Scanner(
            self.scan_callback
        )

        threading.Thread(
            target=self.scanner.scan,
            daemon=True
        ).start()

    # ========================================================
    # CALLBACK
    # ========================================================

    def scan_callback(self, event, *args):

        Clock.schedule_once(
            lambda dt: self.update_ui(
                event,
                *args
            )
        )

    # ========================================================
    # UPDATE UI
    # ========================================================

    def update_ui(self, event, *args):

        if event == "progress":

            (
                progress,
                scanned,
                threats,
                suspicious,
                path
            ) = args

            self.progress.value = progress

            self.percent.text = (
                f"{progress:.1f}%"
            )

            filename = os.path.basename(path)

            self.status.text = (
                "Scanning: "
                + filename[:45]
            )

            self.stats.text = (
                f"Files scanned: {scanned}\n"
                f"Threats: {threats}\n"
                f"Suspicious: {suspicious}"
            )

        elif event == "done":

            (
                scanned,
                threats,
                suspicious,
                elapsed,
                results
            ) = args

            self.scanner = None

            self.scan_button.disabled = False

            self.progress.value = 100
            self.percent.text = "100%"

            self.stats.text = (
                f"Files scanned: {scanned}\n"
                f"Threats: {threats}\n"
                f"Suspicious: {suspicious}"
            )

            if threats > 0:

                self.status.text = (
                    "⚠️ THREATS DETECTED"
                )

            elif suspicious > 0:

                self.status.text = (
                    "⚠️ Suspicious files found"
                )

            else:

                self.status.text = (
                    "✓ No known threats found"
                )

            lines = []

            lines.append(
                "========== SCAN RESULT =========="
            )

            lines.append(
                f"Files scanned : {scanned}"
            )

            lines.append(
                f"Threats       : {threats}"
            )

            lines.append(
                f"Suspicious    : {suspicious}"
            )

            lines.append(
                f"Scan time     : {elapsed:.1f} seconds"
            )

            lines.append("")

            for result in results[:20]:

                lines.append(
                    "File: "
                    + result["file"]
                )

                lines.append(
                    "SHA256: "
                    + str(
                        result["sha256"]
                    )
                )

                lines.append(
                    "Reason: "
                    + result["reason"]
                )

                lines.append("")

            if not results:

                lines.append(
                    "No suspicious files detected."
                )

            self.result.text = "\n".join(lines)


# ============================================================
# APP
# ============================================================

class V16AntivirusApp(App):

    title = APP_NAME

    def build(self):

        return AntivirusUI()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    V16AntivirusApp().run()
