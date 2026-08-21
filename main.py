# ============================================================
# V16 ANTIVIRUS PRO
# Stable Android Antivirus Scanner
# Version 16.2
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
# CONFIGURATION
# ============================================================

APP_NAME = "V16 Antivirus Pro"
VERSION = "16.2"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "scan_history.json")

# Known malicious SHA-256 hashes.
# এখানে নিজের verified malware hashes যোগ করতে পারবে।
KNOWN_MALWARE_HASHES = {
    # "sha256_hash_here",
}


# Suspicious Android permissions.
SUSPICIOUS_PERMISSIONS = {
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


# ============================================================
# FILE HASH
# ============================================================

def sha256_file(file_path, chunk_size=1024 * 1024):
    """
    Calculate SHA-256 without loading the entire file into RAM.
    """

    digest = hashlib.sha256()

    try:
        with open(file_path, "rb") as f:
            while True:
                data = f.read(chunk_size)

                if not data:
                    break

                digest.update(data)

        return digest.hexdigest()

    except Exception:
        return None


# ============================================================
# APK ANALYZER
# ============================================================

class APKAnalyzer:

    @staticmethod
    def analyze(apk_path):
        result = {
            "valid_apk": False,
            "sha256": None,
            "confirmed_malware": False,
            "suspicious": False,
            "risk_score": 0,
            "permissions": [],
            "files": [],
            "reason": [],
        }

        # ----------------------------------------------------
        # SHA-256
        # ----------------------------------------------------

        file_hash = sha256_file(apk_path)

        result["sha256"] = file_hash

        if file_hash and file_hash.lower() in KNOWN_MALWARE_HASHES:
            result["confirmed_malware"] = True
            result["suspicious"] = True
            result["risk_score"] += 10
            result["reason"].append(
                "Known malicious SHA-256 hash matched"
            )

        # ----------------------------------------------------
        # ZIP/APK STRUCTURE
        # ----------------------------------------------------

        try:

            with zipfile.ZipFile(apk_path, "r") as apk:

                names = apk.namelist()

                result["files"] = names[:100]

                if "AndroidManifest.xml" not in names:
                    result["reason"].append(
                        "AndroidManifest.xml missing"
                    )
                    result["risk_score"] += 3
                else:
                    result["valid_apk"] = True

                if not any(
                    name.startswith("classes")
                    and name.endswith(".dex")
                    for name in names
                ):
                    result["reason"].append(
                        "classes.dex missing"
                    )
                    result["risk_score"] += 2

                # ------------------------------------------------
                # Scan APK binary content for permission names.
                # This is intentionally lightweight and does not
                # require pyaxmlparser.
                # ------------------------------------------------

                permission_text = ""

                try:

                    manifest_data = apk.read(
                        "AndroidManifest.xml"
                    )

                    permission_text = manifest_data.decode(
                        "latin-1",
                        errors="ignore"
                    )

                except Exception:
                    permission_text = ""

                for permission, score in SUSPICIOUS_PERMISSIONS.items():

                    if permission in permission_text:

                        result["permissions"].append(
                            permission
                        )

                        result["risk_score"] += score

        except zipfile.BadZipFile:

            result["reason"].append(
                "Invalid APK/ZIP structure"
            )

            result["risk_score"] += 5

        except Exception as exc:

            result["reason"].append(
                "APK analysis error: " + str(exc)
            )

            result["risk_score"] += 5

        # ----------------------------------------------------
        # FINAL CLASSIFICATION
        # ----------------------------------------------------

        if result["risk_score"] >= 8:
            result["suspicious"] = True

        return result


# ============================================================
# GENERAL FILE ANALYZER
# ============================================================

def analyze_file(file_path):

    result = {
        "file": file_path,
        "sha256": None,
        "confirmed_malware": False,
        "suspicious": False,
        "risk_score": 0,
        "reason": [],
    }

    if not os.path.isfile(file_path):
        return result

    file_hash = sha256_file(file_path)

    result["sha256"] = file_hash

    if file_hash and file_hash.lower() in KNOWN_MALWARE_HASHES:

        result["confirmed_malware"] = True
        result["suspicious"] = True
        result["risk_score"] = 10

        result["reason"].append(
            "Known malicious SHA-256 hash"
        )

        return result

    # --------------------------------------------------------
    # APK
    # --------------------------------------------------------

    if file_path.lower().endswith(".apk"):

        apk_result = APKAnalyzer.analyze(file_path)

        result.update(apk_result)

        return result

    # --------------------------------------------------------
    # Suspicious executable extensions
    # --------------------------------------------------------

    suspicious_extensions = {
        ".exe",
        ".scr",
        ".bat",
        ".cmd",
        ".vbs",
        ".ps1",
        ".pif",
    }

    extension = os.path.splitext(file_path)[1].lower()

    if extension in suspicious_extensions:

        result["suspicious"] = True
        result["risk_score"] += 4

        result["reason"].append(
            "Suspicious executable extension"
        )

    return result


# ============================================================
# HISTORY
# ============================================================

def load_history():

    try:

        if not os.path.exists(HISTORY_FILE):
            return []

        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

            if isinstance(data, list):
                return data

    except Exception:
        pass

    return []


def save_history(entry):

    history = load_history()

    history.insert(0, entry)

    # Keep last 100 records.
    history = history[:100]

    try:

        with open(
            HISTORY_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                history,
                f,
                indent=2,
                ensure_ascii=False
            )

    except Exception:
        pass


# ============================================================
# ANDROID STORAGE PATHS
# ============================================================

def get_scan_paths():

    paths = []

    candidates = [
        "/storage/emulated/0",
        "/sdcard",
    ]

    for path in candidates:

        if os.path.exists(path):

            if path not in paths:
                paths.append(path)

    # Application directory as fallback.
    if BASE_DIR not in paths:
        paths.append(BASE_DIR)

    return paths


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

        started = time.time()

        files_scanned = 0
        threats = 0
        suspicious = 0

        threat_results = []

        paths = get_scan_paths()

        # ----------------------------------------------------
        # Collect files
        # ----------------------------------------------------

        all_files = []

        for root_path in paths:

            if self.stop_requested:
                break

            try:

                for root, dirs, files in os.walk(
                    root_path,
                    topdown=True
                ):

                    if self.stop_requested:
                        break

                    # Avoid inaccessible/system directories.
                    dirs[:] = [
                        d for d in dirs
                        if d not in {
                            ".cache",
                            ".thumbnails",
                        }
                    ]

                    for filename in files:

                        if self.stop_requested:
                            break

                        full_path = os.path.join(
                            root,
                            filename
                        )

                        all_files.append(full_path)

            except Exception:
                continue

        total = len(all_files)

        if total == 0:

            self.callback(
                "done",
                {
                    "files": 0,
                    "threats": 0,
                    "suspicious": 0,
                    "time": time.time() - started,
                    "results": [],
                }
            )

            return

        # ----------------------------------------------------
        # Analyze
        # ----------------------------------------------------

        for index, file_path in enumerate(all_files):

            if self.stop_requested:
                break

            result = analyze_file(file_path)

            files_scanned += 1

            if result.get("confirmed_malware"):
                threats += 1
                threat_results.append(result)

            elif result.get("suspicious"):
                suspicious += 1
                threat_results.append(result)

            progress = (
                (index + 1) / total
            ) * 100

            self.callback(
                "progress",
                {
                    "progress": progress,
                    "files": files_scanned,
                    "threats": threats,
                    "suspicious": suspicious,
                    "current": file_path,
                }
            )

        elapsed = time.time() - started

        self.callback(
            "done",
            {
                "files": files_scanned,
                "threats": threats,
                "suspicious": suspicious,
                "time": elapsed,
                "results": threat_results,
            }
        )


# ============================================================
# UI
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

        title = Label(
            text="[b]King Taj 👑[/b]",
            markup=True,
            font_size=dp(28),
            size_hint_y=None,
            height=dp(55)
        )

        self.add_widget(title)

        subtitle = Label(
            text="V16 Antivirus Pro  •  Version 16.2",
            font_size=dp(15),
            size_hint_y=None,
            height=dp(30)
        )

        self.add_widget(subtitle)

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

        self.progress_label = Label(
            text="0%",
            size_hint_y=None,
            height=dp(30)
        )

        self.add_widget(self.progress_label)

        # ----------------------------------------------------
        # STATISTICS
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
        # HISTORY BUTTON
        # ----------------------------------------------------

        history_button = Button(
            text="📋  SCAN HISTORY",
            font_size=dp(17),
            size_hint_y=None,
            height=dp(50)
        )

        history_button.bind(
            on_release=self.show_history
        )

        self.add_widget(history_button)

        # ----------------------------------------------------
        # RESULT AREA
        # ----------------------------------------------------

        scroll = ScrollView()

        self.result_label = Label(
            text="No scan performed yet.",
            size_hint_y=None,
            valign="top",
            halign="left"
        )

        self.result_label.bind(
            texture_size=self.result_label.setter(
                "size"
            )
        )

        scroll.add_widget(
            self.result_label
        )

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

        self.progress_label.text = "0%"

        self.status.text = "Scanning..."

        self.stats.text = (
            "Files scanned: 0\n"
            "Threats: 0\n"
            "Suspicious: 0"
        )

        self.result_label.text = ""

        self.scanner = Scanner(
            self.scan_callback
        )

        thread = threading.Thread(
            target=self.scanner.scan,
            daemon=True
        )

        thread.start()

    # ========================================================
    # CALLBACK
    # ========================================================

    def scan_callback(self, event, data):

        Clock.schedule_once(
            lambda dt: self._update_ui(
                event,
                data
            )
        )

    # ========================================================
    # UI UPDATE
    # ========================================================

    def _update_ui(self, event, data):

        if event == "progress":

            value = data["progress"]

            self.progress.value = value

            self.progress_label.text = (
                f"{value:.1f}%"
            )

            self.status.text = (
                "Scanning: "
                + os.path.basename(
                    data["current"]
                )[:40]
            )

            self.stats.text = (
                f"Files scanned: {data['files']}\n"
                f"Threats: {data['threats']}\n"
                f"Suspicious: {data['suspicious']}"
            )

        elif event == "done":

            self.scanner = None

            self.scan_button.disabled = False

            self.progress.value = 100

            self.progress_label.text = "100%"

            files = data["files"]
            threats = data["threats"]
            suspicious = data["suspicious"]
            elapsed = data["time"]

            self.stats.text = (
                f"Files scanned: {files}\n"
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

            # ------------------------------------------------
            # Result text
            # ------------------------------------------------

            lines = [
                "========== SCAN RESULT ==========",
                f"Files scanned : {files}",
                f"Threats       : {threats}",
                f"Suspicious    : {suspicious}",
                f"Scan time     : {elapsed:.1f} seconds",
                "",
            ]

            for result in data["results"][:30]:

                file_name = result.get(
                    "file",
                    "Unknown"
                )

                lines.append(
                    "File: " + file_name
                )

                lines.append(
                    "SHA256: "
                    + str(
                        result.get(
                            "sha256",
                            "N/A"
                        )
                    )
                )

                lines.append(
                    "Risk score: "
                    + str(
                        result.get(
                            "risk_score",
                            0
                        )
                    )
                )

                for reason in result.get(
                    "reason",
                    []
                ):

                    lines.append(
                        "Reason: " + reason
                    )

                lines.append("")

            self.result_label.text = "\n".join(
                lines
            )

            # ------------------------------------------------
            # Save history
            # ------------------------------------------------

            history_entry = {
                "date": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "files": files,
                "threats": threats,
                "suspicious": suspicious,
                "time": round(elapsed, 2),
            }

            save_history(history_entry)

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
                "",
            ]

            for item in history[:50]:

                lines.append(
                    f"Date: {item.get('date', 'N/A')}"
                )

                lines.append(
                    f"Files: {item.get('files', 0)}"
                )

                lines.append(
                    f"Threats: {item.get('threats', 0)}"
                )

                lines.append(
                    f"Suspicious: "
                    f"{item.get('suspicious', 0)}"
                )

                lines.append(
                    f"Time: "
                    f"{item.get('time', 0)} sec"
                )

                lines.append("")

            text = "\n".join(lines)

        popup_content = ScrollView()

        label = Label(
            text=text,
            size_hint_y=None,
            halign="left",
            valign="top"
        )

        label.bind(
            texture_size=label.setter(
                "size"
            )
        )

        popup_content.add_widget(label)

        Popup(
            title="Scan History",
            content=popup_content,
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
