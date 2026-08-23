# ============================================================
# V16 ANTIVIRUS PRO
# Version 16.3
# ============================================================

import os
import json
import time
import hashlib
import zipfile
import threading
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup


# ============================================================
# VARIABLES
# ============================================================

APP_NAME = "V16 Antivirus Pro"
VERSION = "16.3"
CHUNK = 1024 * 1024
MAX_HISTORY = 100

BASE = os.path.dirname(os.path.abspath(__file__))
HISTORY = os.path.join(BASE, "scan_history.json")

MALWARE = {
    # "verified_sha256_hash_here",
}

PERMS = {
    "SEND_SMS": 2,
    "RECEIVE_SMS": 2,
    "READ_SMS": 2,
    "READ_CONTACTS": 1,
    "WRITE_CONTACTS": 1,
    "CALL_PHONE": 2,
    "RECORD_AUDIO": 1,
    "CAMERA": 1,
    "ACCESS_FINE_LOCATION": 1,
    "ACCESS_COARSE_LOCATION": 1,
    "SYSTEM_ALERT_WINDOW": 2,
    "RECEIVE_BOOT_COMPLETED": 1,
    "WRITE_SETTINGS": 2,
    "REQUEST_INSTALL_PACKAGES": 2,
    "BIND_ACCESSIBILITY_SERVICE": 3,
}

BAD_EXT = {
    ".exe", ".scr", ".bat", ".cmd",
    ".vbs", ".ps1", ".pif"
}


# ============================================================
# SHA256
# ============================================================

def sha256(path):
    try:
        h = hashlib.sha256()

        with open(path, "rb") as f:
            while True:
                data = f.read(CHUNK)

                if not data:
                    break

                h.update(data)

        return h.hexdigest()

    except Exception:
        return None


# ============================================================
# APK ANALYZER
# ============================================================

def analyze_apk(path):

    r = {
        "file": path,
        "sha256": sha256(path),
        "confirmed_malware": False,
        "suspicious": False,
        "risk_score": 0,
        "permissions": [],
        "reason": []
    }

    if r["sha256"] in MALWARE:
        r["confirmed_malware"] = True
        r["suspicious"] = True
        r["risk_score"] = 10
        r["reason"].append("Known malicious SHA-256")

    try:
        with zipfile.ZipFile(path, "r") as z:

            names = z.namelist()

            if "AndroidManifest.xml" not in names:
                r["reason"].append("AndroidManifest.xml missing")
                r["risk_score"] += 3

            if not any(
                x.startswith("classes") and x.endswith(".dex")
                for x in names
            ):
                r["reason"].append("classes.dex missing")
                r["risk_score"] += 2

            try:
                data = z.read("AndroidManifest.xml")
                text = data.decode("latin-1", errors="ignore")

                for p, score in PERMS.items():

                    if p in text:
                        r["permissions"].append(p)
                        r["risk_score"] += score

            except Exception:
                pass

    except zipfile.BadZipFile:
        r["reason"].append("Invalid APK/ZIP")
        r["risk_score"] += 5

    except Exception as e:
        r["reason"].append("APK error: " + str(e))
        r["risk_score"] += 5

    if r["risk_score"] >= 8:
        r["suspicious"] = True

    return r


# ============================================================
# FILE ANALYZER
# ============================================================

def analyze_file(path):

    if not os.path.isfile(path):
        return None

    h = sha256(path)

    r = {
        "file": path,
        "sha256": h,
        "confirmed_malware": False,
        "suspicious": False,
        "risk_score": 0,
        "reason": []
    }

    # Known malware
    if h in MALWARE:
        r["confirmed_malware"] = True
        r["suspicious"] = True
        r["risk_score"] = 10
        r["reason"].append("Known malicious SHA-256")
        return r

    # APK
    if path.lower().endswith(".apk"):
        return analyze_apk(path)

    # Suspicious extensions
    ext = os.path.splitext(path)[1].lower()

    if ext in BAD_EXT:
        r["suspicious"] = True
        r["risk_score"] = 4
        r["reason"].append("Suspicious executable extension")

    return r


# ============================================================
# HISTORY
# ============================================================

def load_history():

    try:
        if os.path.exists(HISTORY):

            with open(HISTORY, "r", encoding="utf-8") as f:
                data = json.load(f)

                if isinstance(data, list):
                    return data

    except Exception:
        pass

    return []


def save_history(data):

    try:
        history = load_history()
        history.insert(0, data)

        with open(HISTORY, "w", encoding="utf-8") as f:
            json.dump(
                history[:MAX_HISTORY],
                f,
                indent=2,
                ensure_ascii=False
            )

    except Exception:
        pass


# ============================================================
# SCAN PATHS
# ============================================================

def scan_paths():

    paths = []

    for p in (
        "/storage/emulated/0",
        "/sdcard"
    ):
        if os.path.exists(p):
            paths.append(p)

    if not paths:
        paths.append(BASE)

    return paths


# ============================================================
# SCANNER
# ============================================================

class Scanner:

    def __init__(self, callback):
        self.callback = callback
        self.stop = False

    def scan(self):

        start = time.time()
        files = []
        results = []

        # ----------------------------------------------------
        # Collect files
        # ----------------------------------------------------

        for base in scan_paths():

            if self.stop:
                break

            try:

                for root, dirs, names in os.walk(base):

                    if self.stop:
                        break

                    dirs[:] = [
                        d for d in dirs
                        if d not in (
                            ".cache",
                            ".thumbnails"
                        )
                    ]

                    for name in names:

                        if self.stop:
                            break

                        files.append(
                            os.path.join(root, name)
                        )

            except Exception:
                continue

        total = len(files)

        scanned = 0
        threats = 0
        suspicious = 0

        # ----------------------------------------------------
        # Analyze
        # ----------------------------------------------------

        for i, path in enumerate(files):

            if self.stop:
                break

            r = analyze_file(path)

            scanned += 1

            if r:

                if r["confirmed_malware"]:
                    threats += 1
                    results.append(r)

                elif r["suspicious"]:
                    suspicious += 1
                    results.append(r)

            progress = (
                ((i + 1) / total) * 100
                if total else 100
            )

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
            time.time() - start,
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
                font_size=dp(28),
                size_hint_y=None,
                height=dp(55)
            )
        )

        self.add_widget(
            Label(
                text=f"{APP_NAME}  •  Version {VERSION}",
                font_size=dp(15),
                size_hint_y=None,
                height=dp(30)
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
        # SCAN
        # ----------------------------------------------------

        self.scan_btn = Button(
            text="🔍  SCAN DEVICE",
            font_size=dp(20),
            size_hint_y=None,
            height=dp(60)
        )

        self.scan_btn.bind(
            on_release=self.start_scan
        )

        self.add_widget(self.scan_btn)

        # ----------------------------------------------------
        # HISTORY
        # ----------------------------------------------------

        history_btn = Button(
            text="📋  SCAN HISTORY",
            font_size=dp(17),
            size_hint_y=None,
            height=dp(50)
        )

        history_btn.bind(
            on_release=self.show_history
        )

        self.add_widget(history_btn)

        # ----------------------------------------------------
        # RESULTS
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
    # START
    # ========================================================

    def start_scan(self, instance):

        if self.scanner:
            return

        self.scan_btn.disabled = True
        self.progress.value = 0
        self.percent.text = "0%"
        self.status.text = "Scanning..."
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

    def scan_callback(
        self,
        event,
        *args
    ):

        Clock.schedule_once(
            lambda dt: self.update_ui(
                event,
                *args
            )
        )

    # ========================================================
    # UI UPDATE
    # ========================================================

    def update_ui(
        self,
        event,
        *args
    ):

        if event == "progress":

            value, scanned, threats, suspicious, path = args

            self.progress.value = value
            self.percent.text = f"{value:.1f}%"

            self.status.text = (
                "Scanning: "
                + os.path.basename(path)[:40]
            )

            self.stats.text = (
                f"Files scanned: {scanned}\n"
                f"Threats: {threats}\n"
                f"Suspicious: {suspicious}"
            )

        elif event == "done":

            scanned, threats, suspicious, elapsed, results = args

            self.scanner = None
            self.scan_btn.disabled = False

            self.progress.value = 100
            self.percent.text = "100%"

            self.stats.text = (
                f"Files scanned: {scanned}\n"
                f"Threats: {threats}\n"
                f"Suspicious: {suspicious}"
            )

            if threats:
                self.status.text = "⚠️ THREATS DETECTED"

            elif suspicious:
                self.status.text = "⚠️ Suspicious files found"

            else:
                self.status.text = "✓ No known threats found"

            lines = [
                "========== SCAN RESULT ==========",
                f"Files scanned : {scanned}",
                f"Threats       : {threats}",
                f"Suspicious    : {suspicious}",
                f"Scan time     : {elapsed:.1f} seconds",
                ""
            ]

            for r in results[:30]:

                lines.append(
                    "File: " + r.get("file", "Unknown")
                )

                lines.append(
                    "SHA256: " + str(
                        r.get("sha256", "N/A")
                    )
                )

                lines.append(
                    "Risk score: " + str(
                        r.get("risk_score", 0)
                    )
                )

                for reason in r.get("reason", []):
                    lines.append(
                        "Reason: " + reason
                    )

                if r.get("permissions"):
                    lines.append(
                        "Permissions: "
                        + ", ".join(
                            r["permissions"]
                        )
                    )

                lines.append("")

            self.result.text = "\n".join(lines)

            save_history({
                "date": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "files": scanned,
                "threats": threats,
                "suspicious": suspicious,
                "time": round(elapsed, 2)
            })

    # ========================================================
    # HISTORY
    # ========================================================

    def show_history(self, instance):

        history = load_history()

        if not history:
            text = "No scan history available."

        else:

            lines = [
                "========== SCAN HISTORY ==========",
                ""
            ]

            for x in history[:50]:

                lines += [
                    f"Date: {x.get('date', 'N/A')}",
                    f"Files: {x.get('files', 0)}",
                    f"Threats: {x.get('threats', 0)}",
                    f"Suspicious: {x.get('suspicious', 0)}",
                    f"Time: {x.get('time', 0)} sec",
                    ""
                ]

            text = "\n".join(lines)

        label = Label(
            text=text,
            size_hint_y=None,
            halign="left",
            valign="top"
        )

        label.bind(
            texture_size=label.setter("size")
        )

        scroll = ScrollView()
        scroll.add_widget(label)

        Popup(
            title="Scan History",
            content=scroll,
            size_hint=(0.92, 0.85)
        ).open()


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
