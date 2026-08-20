# ============================================================
# V16 ANTIVIRUS PRO - COMPLETE ANDROID VERSION
# Version: 16.2
# ============================================================

import os
import json
import time
import hashlib
import shutil
import threading
from pathlib import Path
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.properties import NumericProperty
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup

try:
    from plyer import notification
except Exception:
    notification = None


# ============================================================
# APP INFORMATION
# ============================================================

APP_NAME = "V16 Antivirus Pro"
VERSION = "16.2"


# ============================================================
# COLORS
# ============================================================

WHITE = (1, 1, 1, 1)
GREEN = (0.1, 0.9, 0.4, 1)
RED = (1, 0.2, 0.2, 1)
YELLOW = (1, 0.8, 0.1, 1)
PURPLE = (0.65, 0.3, 1, 1)
CYAN = (0.1, 0.8, 1, 1)
GRAY = (0.55, 0.6, 0.65, 1)
DARK = (0.015, 0.025, 0.04, 1)
PANEL = (0.025, 0.06, 0.09, 1)


# ============================================================
# DIRECTORIES
# ============================================================

APP_DIR = Path(
    App.get_running_app().user_data_dir
    if App.get_running_app()
    else os.path.join(
        os.path.expanduser("~"),
        ".v16antivirus"
    )
)

APP_DIR.mkdir(parents=True, exist_ok=True)

HISTORY_FILE = APP_DIR / "history.json"
CACHE_FILE = APP_DIR / "monitor_cache.json"
QUARANTINE_DIR = APP_DIR / "quarantine"

QUARANTINE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# SCAN SETTINGS
# ============================================================

CHUNK_SIZE = 64 * 1024

MAX_MONITOR_NEW_FILES_PER_CYCLE = 20

MONITOR_INTERVAL = 8


# ============================================================
# KNOWN MALWARE SHA-256 DATABASE
# ============================================================
#
# এখানে প্রকৃত IOC SHA-256 যোগ করা যাবে।
# কোনো hash database-এ না থাকলে সেটিকে malware বলা হবে না।
#

KNOWN_MALWARE_HASHES = {
    # "example_sha256_hash_here",
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
    ".vbe",
    ".js",
    ".jar",
    ".pif",
}


# ============================================================
# ANDROID PERMISSION
# ============================================================

def request_android_permissions():
    """
    Android runtime permissions.

    নতুন Android সংস্করণে storage access সীমিত হতে পারে।
    তাই permission request ব্যর্থ হলেও app বন্ধ হবে না।
    """

    try:
        from android.permissions import request_permissions

        permissions = [
            "android.permission.READ_EXTERNAL_STORAGE",
            "android.permission.WRITE_EXTERNAL_STORAGE",
        ]

        try:
            permissions.append(
                "android.permission.POST_NOTIFICATIONS"
            )
        except Exception:
            pass

        request_permissions(permissions)

    except Exception:
        pass


# ============================================================
# NOTIFICATION
# ============================================================

def notify_user(title, message):

    try:
        if notification is not None:
            notification.notify(
                title=title,
                message=message,
                app_name=APP_NAME,
                timeout=5
            )
    except Exception:
        pass


# ============================================================
# STORAGE ROOTS
# ============================================================

def scan_roots():

    possible_roots = [
        "/storage/emulated/0",
        "/sdcard",
    ]

    roots = []

    for root in possible_roots:

        try:

            path = Path(root)

            if path.exists() and os.access(root, os.R_OK):
                roots.append(path)

        except Exception:
            pass

    return roots


# ============================================================
# FILE ITERATOR
# ============================================================

def iter_files(root):

    try:

        for current_root, dirs, files in os.walk(
            str(root),
            topdown=True
        ):

            # Android protected directories
            dirs[:] = [
                d for d in dirs
                if d not in {
                    ".thumbnails",
                    "Android/data",
                    "Android/obb"
                }
            ]

            for filename in files:

                path = os.path.join(
                    current_root,
                    filename
                )

                try:

                    if os.path.isfile(path):
                        yield path

                except Exception:
                    continue

    except Exception:
        return


# ============================================================
# SHA-256
# ============================================================

def calculate_sha256(path):

    sha = hashlib.sha256()

    try:

        with open(
            path,
            "rb"
        ) as file:

            while True:

                data = file.read(CHUNK_SIZE)

                if not data:
                    break

                sha.update(data)

        return sha.hexdigest()

    except Exception:
        return ""


# ============================================================
# FILE SIGNATURE FOR MONITOR
# ============================================================

def file_signature(path):

    try:

        stat = os.stat(path)

        return {
            "size": stat.st_size,
            "mtime": stat.st_mtime
        }

    except Exception:
        return None


# ============================================================
# LOAD JSON
# ============================================================

def load_json(path, default):

    try:

        if not path.exists():
            return default

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        return data

    except Exception:
        return default


# ============================================================
# SAVE JSON
# ============================================================

def save_json(path, data):

    try:

        temp = path.with_suffix(
            path.suffix + ".tmp"
        )

        with open(
            temp,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False
            )

        temp.replace(path)

    except Exception:
        pass


# ============================================================
# HISTORY
# ============================================================

def get_history():

    return load_json(
        HISTORY_FILE,
        []
    )


def add_history(result):

    history = get_history()

    history.insert(
        0,
        result
    )

    history = history[:500]

    save_json(
        HISTORY_FILE,
        history
    )


# ============================================================
# MONITOR CACHE
# ============================================================

def load_cache():

    return load_json(
        CACHE_FILE,
        {}
    )


def save_cache(cache):

    save_json(
        CACHE_FILE,
        cache
    )


# ============================================================
# QUARANTINE
# ============================================================

def quarantine(result):

    result["quarantined"] = False

    source = result.get("path")

    if not source:
        return result

    try:

        source_path = Path(source)

        if not source_path.exists():
            return result

        filename = source_path.name

        timestamp = int(time.time())

        destination = (
            QUARANTINE_DIR
            / f"{timestamp}_{filename}.quarantine"
        )

        shutil.move(
            str(source_path),
            str(destination)
        )

        result["quarantined"] = True

        result["quarantine_path"] = str(
            destination
        )

    except Exception:

        result["quarantined"] = False

    return result


# ============================================================
# FILE SCANNER
# ============================================================

def scan_one_file(path):

    path = str(path)

    name = os.path.basename(path)

    result = {
        "time": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "name": name,
        "path": path,
        "sha256": "",
        "verdict": "UNKNOWN",
        "quarantined": False,
    }

    try:

        if not os.path.isfile(path):

            result["verdict"] = "UNREADABLE"

            return result

        sha256 = calculate_sha256(
            path
        )

        result["sha256"] = sha256

        if sha256 in KNOWN_MALWARE_HASHES:

            result["verdict"] = (
                "CONFIRMED_MALWARE"
            )

        else:

            result["verdict"] = "CLEAN"

    except Exception:

        result["verdict"] = "UNREADABLE"

    return result


# ============================================================
# ROUNDED PANEL
# ============================================================

class Panel(BoxLayout):

    def __init__(
        self,
        **kwargs
    ):

        super().__init__(**kwargs)

        with self.canvas.before:

            Color(*PANEL)

            self.bg = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(14)]
            )

        self.bind(
            pos=self.update_bg,
            size=self.update_bg
        )

    def update_bg(
        self,
        *_args
    ):

        self.bg.pos = self.pos
        self.bg.size = self.size


# ============================================================
# ACTION BUTTON
# ============================================================

class ActionButton(Button):

    def __init__(
        self,
        accent=CYAN,
        **kwargs
    ):

        super().__init__(**kwargs)

        self.accent = accent

        self.color = WHITE

        self.background_normal = ""

        self.background_down = ""

        self.background_color = (
            0,
            0,
            0,
            0
        )

        with self.canvas.before:

            Color(*self.accent)

            self.rectangle = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(12)]
            )

        self.bind(
            pos=self.update_bg,
            size=self.update_bg
        )

    def update_bg(
        self,
        *_args
    ):

        self.rectangle.pos = self.pos
        self.rectangle.size = self.size


# ============================================================
# SECURITY GAUGE
# ============================================================

class SecurityGauge(Widget):

    value = NumericProperty(0)

    def __init__(
        self,
        **kwargs
    ):

        super().__init__(**kwargs)

        self.status = "READY"

        self.bind(
            value=self.redraw,
            pos=self.redraw,
            size=self.redraw
        )

    def set_value(
        self,
        value,
        status
    ):

        self.value = max(
            0,
            min(100, value)
        )

        self.status = status

        self.redraw()

    def redraw(
        self,
        *_args
    ):

        self.canvas.clear()

        with self.canvas:

            # Outer circle
            Color(
                0.08,
                0.12,
                0.16,
                1
            )

            Line(
                circle=(
                    self.center_x,
                    self.center_y,
                    min(
                        self.width,
                        self.height
                    ) / 2.6
                ),
                width=dp(10)
            )

            # Progress
            if self.status == "Threat Found":

                Color(*RED)

            elif self.status == "Safe":

                Color(*GREEN)

            else:

                Color(*CYAN)

            Line(
                circle=(
                    self.center_x,
                    self.center_y,
                    min(
                        self.width,
                        self.height
                    ) / 2.6,
                    0,
                    self.value * 3.6
                ),
                width=dp(10)
            )


# ============================================================
# MAIN ANTIVIRUS SCREEN
# ============================================================

class AntivirusScreen(BoxLayout):

    def __init__(
        self,
        **kwargs
    ):

        super().__init__(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(10),
            **kwargs
        )

        self.scanning = False

        self.monitor_busy = False

        self.scan_start = 0

        self.scanned_files = 0

        self.threats = 0

        self.last_scan_seconds = 0

        self.monitor_cache = load_cache()

        self.build_ui()

        request_android_permissions()

        Clock.schedule_interval(
            self.monitor_tick,
            MONITOR_INTERVAL
        )

    # ========================================================
    # LABEL HELPER
    # ========================================================

    def label(
        self,
        text,
        size,
        color=WHITE,
        **kwargs
    ):

        return Label(
            text=text,
            font_size=dp(size),
            color=color,
            halign="center",
            valign="middle",
            **kwargs
        )

    # ========================================================
    # BUILD UI
    # ========================================================

    def build_ui(self):

        # ====================================================
        # HEADER
        # ====================================================

        header = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(72)
        )

        header.add_widget(
            self.label(
                "KING TAJ 👑",
                15,
                YELLOW,
                size_hint_y=None,
                height=dp(28)
            )
        )

        header.add_widget(
            self.label(
                APP_NAME,
                22,
                WHITE
            )
        )

        self.add_widget(header)

        # ====================================================
        # SECURITY GAUGE
        # ====================================================

        gauge_panel = Panel(
            orientation="vertical",
            size_hint_y=None,
            height=dp(220),
            padding=dp(8)
        )

        self.gauge = SecurityGauge(
            size_hint_y=None,
            height=dp(150)
        )

        gauge_panel.add_widget(
            self.gauge
        )

        self.percent_label = self.label(
            "0%",
            20,
            CYAN,
            size_hint_y=None,
            height=dp(35)
        )

        gauge_panel.add_widget(
            self.percent_label
        )

        self.add_widget(
            gauge_panel
        )

        # ====================================================
        # HEALTH
        # ====================================================

        health_panel = Panel(
            orientation="vertical",
            size_hint_y=None,
            height=dp(100),
            padding=dp(10)
        )

        self.health_label = self.label(
            "SYSTEM HEALTH",
            12,
            GRAY
        )

        self.safe_label = self.label(
            "Ready to scan",
            22,
            GREEN
        )

        health_panel.add_widget(
            self.health_label
        )

        health_panel.add_widget(
            self.safe_label
        )

        self.add_widget(
            health_panel
        )

        # ====================================================
        # DEVICE STATUS
        # ====================================================

        status_panel = Panel(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(82),
            padding=dp(8)
        )

        status_left = BoxLayout(
            orientation="vertical"
        )

        status_left.add_widget(
            self.label(
                "DEVICE STATUS",
                11,
                GRAY
            )
        )

        self.device_status = self.label(
            "READY",
            16,
            GREEN
        )

        status_left.add_widget(
            self.device_status
        )

        status_right = BoxLayout(
            orientation="vertical"
        )

        status_right.add_widget(
            self.label(
                "THREATS",
                11,
                GRAY
            )
        )

        self.device_threat = self.label(
            "No Threats",
            16,
            GREEN
        )

        status_right.add_widget(
            self.device_threat
        )

        status_panel.add_widget(
            status_left
        )

        status_panel.add_widget(
            status_right
        )

        self.add_widget(
            status_panel
        )

        # ====================================================
        # SCAN BUTTON
        # ====================================================

        self.scan_button = ActionButton(
            text="SCAN DEVICE\nFull System Scan",
            accent=CYAN,
            size_hint_y=None,
            height=dp(70),
            font_size=dp(16)
        )

        self.scan_button.bind(
            on_press=self.start_full_scan
        )

        self.add_widget(
            self.scan_button
        )

        # ====================================================
        # LAST SCAN
        # ====================================================

        last_panel = Panel(
            orientation="vertical",
            padding=dp(10),
            size_hint_y=None,
            height=dp(125)
        )

        self.last_result = self.label(
            "No scan performed",
            13,
            WHITE
        )

        self.files_label = self.label(
            "Files Scanned\n0",
            13,
            CYAN
        )

        self.time_label = self.label(
            "Scan Time\n--:--",
            13,
            YELLOW
        )

        last_panel.add_widget(
            self.last_result
        )

        last_panel.add_widget(
            self.files_label
        )

        last_panel.add_widget(
            self.time_label
        )

        self.add_widget(
            last_panel
        )

        # ====================================================
        # HISTORY BUTTON
        # ====================================================

        self.history_button = ActionButton(
            text="▣  VIEW HISTORY   ›",
            accent=PURPLE,
            size_hint_y=None,
            height=dp(58)
        )

        self.history_button.bind(
            on_press=self.show_history
        )

        self.add_widget(
            self.history_button
        )

        # ====================================================
        # LIVE EVENTS
        # ====================================================

        live_panel = Panel(
            orientation="vertical",
            padding=dp(10),
            size_hint_y=None,
            height=dp(112)
        )

        self.live_title = self.label(
            "REAL-TIME PROTECTION\n(Auto Scan New Files)",
            13,
            GREEN,
            size_hint_y=None,
            height=dp(35)
        )

        self.live_event = self.label(
            "✓ Protection active\n"
            "Waiting for new or changed files...",
            13,
            WHITE
        )

        live_panel.add_widget(
            self.live_title
        )

        live_panel.add_widget(
            self.live_event
        )

        self.add_widget(
            live_panel
        )

        # ====================================================
        # NAVIGATION
        # ====================================================

        nav = BoxLayout(
            spacing=dp(4),
            size_hint_y=None,
            height=dp(58)
        )

        for name, callback in (
            ("HOME", self.home),
            ("SCAN", self.start_full_scan),
            (
                "HISTORY",
                self.show_history
            ),
            (
                "QUARANTINE",
                self.show_quarantine
            ),
            (
                "SETTINGS",
                self.show_info
            ),
        ):

            b = Button(
                text=name,
                font_size=dp(9),
                color=WHITE,
                background_normal="",
                background_color=(
                    0.02,
                    0.06,
                    0.09,
                    1
                )
            )

            b.bind(
                on_press=callback
            )

            nav.add_widget(b)

        self.add_widget(nav)

    # ========================================================
    # FULL SCAN
    # ========================================================

    def start_full_scan(
        self,
        *_args
    ):

        if self.scanning:
            return

        request_android_permissions()

        roots = scan_roots()

        if not roots:

            self.show_scan_error(
                "No readable storage location was found."
            )

            return

        self.scanning = True

        self.scan_start = time.time()

        self.scanned_files = 0

        self.threats = 0

        self.scan_button.disabled = True

        self.scan_button.text = (
            "SCANNING...\nPlease wait"
        )

        self.gauge.set_value(
            0,
            "Scanning"
        )

        self.percent_label.text = "0%"

        self.health_label.text = (
            "SYSTEM HEALTH"
        )

        self.safe_label.text = (
            "Scanning..."
        )

        self.safe_label.color = YELLOW

        self.device_status.text = (
            "SCANNING"
        )

        self.device_status.color = YELLOW

        self.device_threat.text = (
            "Security scan running"
        )

        self.last_result.text = (
            "Scanning..."
        )

        self.files_label.text = (
            "Files Scanned\n0"
        )

        self.time_label.text = (
            "Scan Time\n00:00"
        )

        thread = threading.Thread(
            target=self.scan_worker,
            args=(roots,),
            daemon=True
        )

        thread.start()

    # ========================================================
    # SCAN WORKER
    # ========================================================

    def scan_worker(
        self,
        roots
    ):

        try:

            files = []

            for root in roots:

                for path in iter_files(root):

                    files.append(path)

            total = max(
                1,
                len(files)
            )

            for index, path in enumerate(
                files,
                1
            ):

                if not self.scanning:
                    break

                result = scan_one_file(
                    path
                )

                self.scanned_files = index

                if (
                    result["verdict"]
                    == "CONFIRMED_MALWARE"
                ):

                    self.threats += 1

                    quarantine(
                        result
                    )

                add_history(
                    result
                )

                progress = int(
                    index * 100 / total
                )

                Clock.schedule_once(
                    lambda dt,
                    r=result,
                    p=progress:
                    self.scan_ui_update(
                        r,
                        p
                    )
                )

            elapsed = (
                time.time()
                - self.scan_start
            )

            Clock.schedule_once(
                lambda dt,
                e=elapsed:
                self.finish_scan(e)
            )

        except Exception as e:

            Clock.schedule_once(
                lambda dt,
                msg=str(e):
                self.show_scan_error(msg)
            )

    # ========================================================
    # SCAN UI
    # ========================================================

    def scan_ui_update(
        self,
        result,
        progress
    ):

        self.gauge.set_value(
            progress,
            (
                "Threat Found"
                if result["verdict"]
                == "CONFIRMED_MALWARE"
                else "Scanning"
            )
        )

        self.percent_label.text = (
            f"{progress}%"
        )

        self.files_label.text = (
            f"Files Scanned\n"
            f"{self.scanned_files:,}"
        )

        if (
            result["verdict"]
            == "CONFIRMED_MALWARE"
        ):

            self.safe_label.text = (
                "Threat Found"
            )

            self.safe_label.color = RED

            self.device_status.text = (
                "THREAT"
            )

            self.device_status.color = RED

            self.device_threat.text = (
                f"{self.threats} confirmed"
            )

            self.last_result.text = (
                "CONFIRMED MALWARE\n"
                + result["name"]
            )

            self.last_result.color = RED

            self.live_event.text = (
                "⚠ CONFIRMED MALWARE DETECTED\n"
                + result["name"]
                + "\nFile quarantined"
            )

            self.live_event.color = RED

            notify_user(
                APP_NAME,
                "Confirmed malware detected and quarantined."
            )

        else:

            self.last_result.text = (
                "Scanning\n"
                + result["name"]
            )

            self.last_result.color = GREEN

    # ========================================================
    # FINISH SCAN
    # ========================================================

    def finish_scan(
        self,
        elapsed
    ):

        if not self.scanning:
            return

        self.scanning = False

        self.last_scan_seconds = int(
            elapsed
        )

        self.scan_button.disabled = False

        self.scan_button.text = (
            "SCAN DEVICE\nFull System Scan"
        )

        self.gauge.set_value(
            100,
            (
                "Threat Found"
                if self.threats
                else "Safe"
            )
        )

        self.percent_label.text = "100%"

        self.files_label.text = (
            f"Files Scanned\n"
            f"{self.scanned_files:,}"
        )

        mins = (
            self.last_scan_seconds
            // 60
        )

        secs = (
            self.last_scan_seconds
            % 60
        )

        self.time_label.text = (
            f"Scan Time\n"
            f"{mins:02d}:{secs:02d}"
        )

        if self.threats:

            self.safe_label.text = (
                "Threat Found"
            )

            self.safe_label.color = RED

            self.device_status.text = (
                "THREAT"
            )

            self.device_status.color = RED

            self.device_threat.text = (
                f"{self.threats} confirmed"
            )

            self.last_result.text = (
                f"{self.threats} "
                "CONFIRMED MALWARE\n"
                "Quarantine completed "
                "where possible"
            )

            self.last_result.color = RED

        else:

            self.safe_label.text = (
                "Safe"
            )

            self.safe_label.color = GREEN

            self.device_status.text = (
                "SECURE"
            )

            self.device_status.color = GREEN

            self.device_threat.text = (
                "No Threats Found"
            )

            self.last_result.text = (
                "✓ No Threat Found\n"
                "Your accessible storage is safe"
            )

            self.last_result.color = GREEN

            self.live_event.text = (
                "✓ Scan completed\n"
                "No verified malware found"
            )

            self.live_event.color = GREEN

    # ========================================================
    # SCAN ERROR
    # ========================================================

    def show_scan_error(
        self,
        message
    ):

        self.scanning = False

        self.scan_button.disabled = False

        self.scan_button.text = (
            "SCAN DEVICE\nFull System Scan"
        )

        self.device_status.text = (
            "SCAN ERROR"
        )

        self.device_status.color = RED

        self.device_threat.text = (
            "See details"
        )

        self.safe_label.text = (
            "Scan Error"
        )

        self.safe_label.color = RED

        self.live_event.text = (
            "Scan stopped safely\n"
            + str(message)[:200]
        )

        self.live_event.color = RED

    # ========================================================
    # MONITOR
    # ========================================================

    def monitor_tick(
        self,
        *_args
    ):

        if (
            self.scanning
            or self.monitor_busy
        ):
            return

        roots = scan_roots()

        if not roots:
            return

        self.monitor_busy = True

        thread = threading.Thread(
            target=self.monitor_worker,
            args=(roots,),
            daemon=True
        )

        thread.start()

    # ========================================================
    # MONITOR WORKER
    # ========================================================

    def monitor_worker(
        self,
        roots
    ):

        try:

            new_files = []

            for root in roots:

                for path in iter_files(root):

                    if (
                        len(new_files)
                        >=
                        MAX_MONITOR_NEW_FILES_PER_CYCLE
                    ):
                        break

                    sig = file_signature(
                        path
                    )

                    if not sig:
                        continue

                    key = os.path.abspath(
                        path
                    )

                    old = self.monitor_cache.get(
                        key
                    )

                    if (
                        old is not None
                        and old != sig
                    ):

                        new_files.append(
                            path
                        )

                    self.monitor_cache[key] = sig

                if (
                    len(new_files)
                    >=
                    MAX_MONITOR_NEW_FILES_PER_CYCLE
                ):
                    break

            save_cache(
                self.monitor_cache
            )

            for path in new_files:

                result = scan_one_file(
                    path
                )

                add_history(
                    result
                )

                Clock.schedule_once(
                    lambda dt,
                    r=result:
                    self.live_scan_result(r)
                )

        except Exception:
            pass

        finally:

            Clock.schedule_once(
                lambda dt:
                self.clear_monitor_busy()
            )

    # ========================================================
    # CLEAR MONITOR
    # ========================================================

    def clear_monitor_busy(
        self
    ):

        self.monitor_busy = False

    # ========================================================
    # LIVE RESULT
    # ========================================================

    def live_scan_result(
        self,
        result
    ):

        if (
            result["verdict"]
            == "CONFIRMED_MALWARE"
        ):

            self.threats += 1

            quarantine(
                result
            )

            self.device_status.text = (
                "THREAT"
            )

            self.device_status.color = RED

            self.device_threat.text = (
                "New confirmed threat"
            )

            self.live_event.text = (
                "⚠ THREAT DETECTED\n"
                + result["name"]
                + "\nFile quarantined"
            )

            self.live_event.color = RED

            notify_user(
                APP_NAME,
                "New confirmed malware detected and quarantined."
            )

        else:

            self.live_event.text = (
                "✓ New File Detected & Scanned\n"
                + result["name"]
                + "\nNo verified malware found"
            )

            self.live_event.color = GREEN

    # ========================================================
    # HISTORY
    # ========================================================

    def show_history(
        self,
        *_args
    ):

        history = get_history()

        box = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(10)
        )

        scroll = ScrollView()

        rows = []

        if not history:

            rows.append(
                "No scan history yet."
            )

        for i, item in enumerate(
            history[:120],
            1
        ):

            verdict = item.get(
                "verdict",
                "UNKNOWN"
            )

            rows.append(
                f"{i}. "
                f"{item.get('time', '-')}\n"
                f"   File: "
                f"{item.get('name', '-')}\n"
                f"   Verdict: "
                f"{verdict}\n"
                f"   SHA-256: "
                f"{item.get('sha256', '-')}\n"
                f"   Quarantine: "
                f"{item.get('quarantined', False)}\n"
            )

        text = Label(
            text="\n".join(rows),
            color=WHITE,
            font_size=dp(12),
            halign="left",
            valign="top",
            size_hint_y=None
        )

        text.bind(
            texture_size=lambda obj,
            size:
            setattr(
                obj,
                "height",
                size[1] + dp(20)
            )
        )

        scroll.add_widget(
            text
        )

        box.add_widget(
            scroll
        )

        close = Button(
            text="CLOSE",
            size_hint_y=None,
            height=dp(50)
        )

        box.add_widget(
            close
        )

        popup = Popup(
            title="SCAN HISTORY",
            content=box,
            size_hint=(0.94, 0.90)
        )

        close.bind(
            on_press=popup.dismiss
        )

        popup.open()

    # ========================================================
    # QUARANTINE
    # ========================================================

    def show_quarantine(
        self,
        *_args
    ):

        try:

            files = sorted(
                QUARANTINE_DIR.iterdir(),
                key=lambda p:
                p.stat().st_mtime,
                reverse=True
            )

        except Exception:

            files = []

        names = [
            p.name
            for p in files[:100]
        ]

        if not names:

            names = [
                "Quarantine is empty."
            ]

        box = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(8)
        )

        scroll = ScrollView()

        text = Label(
            text="\n\n".join(names),
            color=WHITE,
            font_size=dp(13),
            halign="left",
            valign="top",
            size_hint_y=None
        )

        text.bind(
            texture_size=lambda obj,
            size:
            setattr(
                obj,
                "height",
                size[1] + dp(20)
            )
        )

        scroll.add_widget(
            text
        )

        box.add_widget(
            scroll
        )

        close = Button(
            text="CLOSE",
            size_hint_y=None,
            height=dp(50)
        )

        box.add_widget(
            close
        )

        popup = Popup(
            title="QUARANTINE",
            content=box,
            size_hint=(0.94, 0.90)
        )

        close.bind(
            on_press=popup.dismiss
        )

        popup.open()

    # ========================================================
    # HOME
    # ========================================================

    def home(
        self,
        *_args
    ):

        self.live_event.text = (
            "✓ Protection active\n"
            "Waiting for new or changed files..."
        )

        self.live_event.color = GREEN

    # ========================================================
    # SETTINGS / INFORMATION
    # ========================================================

    def show_info(
        self,
        *_args
    ):

        text = (
            f"{APP_NAME} {VERSION}\n\n"

            "Security baseline:\n"

            "• SHA-256 exact IOC matching\n"
            "• Confirmed-malware quarantine\n"
            "• Scan history\n"
            "• New/changed file monitoring\n"
            "• Permission-safe file traversal\n\n"

            "Important:\n"

            "Android protected/private app data "
            "may not be accessible to a normal "
            "Python/Kivy application."
        )

        close = Button(
            text="CLOSE",
            size_hint_y=None,
            height=dp(50)
        )

        box = BoxLayout(
            orientation="vertical",
            padding=dp(12)
        )

        box.add_widget(
            Label(
                text=text,
                color=WHITE,
                font_size=dp(13),
                halign="left",
                valign="top"
            )
        )

        box.add_widget(
            close
        )

        popup = Popup(
            title="V16 SECURITY",
            content=box,
            size_hint=(0.92, 0.70)
        )

        close.bind(
            on_press=popup.dismiss
        )

        popup.open()


# ============================================================
# APP
# ============================================================

class V16AntivirusApp(App):

    def build(self):

        self.title = (
            f"{APP_NAME} {VERSION}"
        )

        return AntivirusScreen()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    V16AntivirusApp().run()
