import csv
import hashlib
import hmac
import json
import queue
import re
import secrets
import socket
import sqlite3
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from time import monotonic
from tkinter import filedialog, messagebox, simpledialog, ttk


APP_DIR = Path(__file__).resolve().parent
DATA_PATH = APP_DIR / "data.json"
SETTINGS_PATH = APP_DIR / "settings.json"
LEGACY_LOG_PATH = APP_DIR / "log_activity.json"
DEFAULT_DB_PATH = APP_DIR / "sarva_monitor.db"
SECURITY_ITERATIONS = 180000

BOX_KEYS = [f"{col}{row}" for row in range(1, 4) for col in "ABC"]
BOX_GRID = [[f"{col}{row}" for col in "ABC"] for row in range(1, 4)]
CONVEYOR_KEYS = [f"conveyor_{index}" for index in range(1, 6)]

COLORS = {
    "bg": "#e7eaee",
    "panel": "#f8fafc",
    "panel_alt": "#eef2f6",
    "ink": "#111827",
    "muted": "#64748b",
    "line": "#cbd5e1",
    "header": "#151a1f",
    "steel": "#334155",
    "teal": "#0f766e",
    "cyan": "#0891b2",
    "green": "#16a34a",
    "amber": "#d97706",
    "red": "#dc2626",
    "blue": "#2563eb",
    "white": "#ffffff",
}


DEFAULT_DATA = {
    "info_data": {
        "pcs_sorted": "0",
        "kg_sorted": "0",
        "pcs_per_hour": "0",
        "kg_per_hour": "0",
    },
    "box_manager": {key: "0" for key in BOX_KEYS},
    "trash": "0",
    "log_activity": [],
}

DEFAULT_SETTINGS = {
    "camera": {
        "exposure": 0,
        "gain": 0,
        "contrast": 0,
        "hue": 0,
        "brightness": 0,
        "auto": False,
    },
    "range": {
        "A1": ["1", "1"],
        "A2": ["2", "1"],
        "A3": ["3", "1"],
        "B1": ["1", "2"],
        "B2": ["2", "2"],
        "B3": ["3", "2"],
        "C1": ["1", "3"],
        "C2": ["2", "3"],
        "C3": ["3", "3"],
        "TRASH": ["1", "4"],
    },
    "conveyor": {key: 8 for key in CONVEYOR_KEYS},
    "database": {
        "type": "sqlite",
        "path": str(DEFAULT_DB_PATH),
    },
    "raspi": {
        "enabled": True,
        "host": "192.168.30.185",
        "port": "65432",
        "timeout": "1.5",
    },
    "security": {
        "admin_pin_salt": "",
        "admin_pin_hash": "",
        "pin_iterations": SECURITY_ITERATIONS,
    },
}


def clamp(value, low, high):
    return max(low, min(high, value))


def as_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def as_int(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def load_json(path, fallback):
    if not path.exists():
        return json.loads(json.dumps(fallback))
    try:
        with path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        return loaded if isinstance(loaded, type(fallback)) else json.loads(json.dumps(fallback))
    except (json.JSONDecodeError, OSError):
        return json.loads(json.dumps(fallback))

def enable_dpi_awareness():
    try:
        import ctypes

        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def save_json(path, payload):
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def normalize_settings(settings):
    merged = json.loads(json.dumps(DEFAULT_SETTINGS))
    if not isinstance(settings, dict):
        return merged

    camera = settings.get("camera", {})
    if isinstance(camera, dict):
        for key in merged["camera"]:
            if key == "auto":
                merged["camera"][key] = bool(camera.get(key, merged["camera"][key]))
            else:
                merged["camera"][key] = clamp(as_int(camera.get(key), merged["camera"][key]), -100, 100)

    ranges = settings.get("range") or settings.get("box_setting") or {}
    if isinstance(ranges, dict):
        for key in list(merged["range"]):
            value = ranges.get(key, merged["range"][key])
            if isinstance(value, (list, tuple)) and len(value) >= 2:
                merged["range"][key] = [str(value[0]), str(value[1])]

    conveyor = settings.get("conveyor", {})
    if isinstance(conveyor, dict):
        for key in CONVEYOR_KEYS:
            merged["conveyor"][key] = clamp(as_int(conveyor.get(key), merged["conveyor"][key]), 0, 20)

    database = settings.get("database", {})
    if isinstance(database, dict):
        legacy_name = database.get("name")
        if database.get("path"):
            merged["database"]["path"] = str(database.get("path"))
        elif legacy_name:
            merged["database"]["path"] = str(APP_DIR / f"{legacy_name}.db")
        merged["database"]["type"] = "sqlite"

    raspi = settings.get("raspi", {})
    if isinstance(raspi, dict):
        merged["raspi"]["enabled"] = bool(raspi.get("enabled", merged["raspi"]["enabled"]))
        merged["raspi"]["host"] = str(raspi.get("host", merged["raspi"]["host"]))
        merged["raspi"]["port"] = str(raspi.get("port", merged["raspi"]["port"]))
        merged["raspi"]["timeout"] = str(raspi.get("timeout", merged["raspi"]["timeout"]))

    security = settings.get("security", {})
    if isinstance(security, dict):
        merged["security"]["admin_pin_salt"] = str(security.get("admin_pin_salt", ""))
        merged["security"]["admin_pin_hash"] = str(security.get("admin_pin_hash", ""))
        merged["security"]["pin_iterations"] = clamp(
            as_int(security.get("pin_iterations"), SECURITY_ITERATIONS),
            100000,
            500000,
        )

    return merged


def normalize_data(data):
    merged = json.loads(json.dumps(DEFAULT_DATA))
    if not isinstance(data, dict):
        return merged

    info = data.get("info_data", {})
    if isinstance(info, dict):
        for key in merged["info_data"]:
            merged["info_data"][key] = str(info.get(key, merged["info_data"][key]))

    boxes = data.get("box_manager", {})
    if isinstance(boxes, dict):
        for key in BOX_KEYS:
            merged["box_manager"][key] = str(boxes.get(key, merged["box_manager"][key]))

    merged["trash"] = str(data.get("trash", merged["trash"]))

    logs = data.get("log_activity", [])
    if isinstance(logs, list):
        merged["log_activity"] = logs[-250:]

    if not merged["log_activity"] and LEGACY_LOG_PATH.exists():
        legacy_logs = load_json(LEGACY_LOG_PATH, [])
        if isinstance(legacy_logs, list):
            merged["log_activity"] = legacy_logs[-250:]

    return merged


def parse_log_entry(entry):
    if isinstance(entry, dict):
        return {
            "time": str(entry.get("time", "--:--:--")),
            "date": str(entry.get("date", "--/--")),
            "jenis": str(entry.get("jenis", entry.get("type", "-"))),
            "berat": str(entry.get("berat", entry.get("weight", "0"))),
            "box": str(entry.get("box", entry.get("destination", "-"))),
            "raw": "",
        }

    raw = str(entry)
    envelope = re.match(
        r"^\[(?P<time>\d{2}:\d{2}:\d{2})(?:\|(?P<pipe_date>\d{2}/\d{2}))?\](?:\[(?P<bracket_date>\d{2}/\d{2})\])?\s*(?P<body>.*)$",
        raw,
    )
    if envelope:
        groups = envelope.groupdict()
        body = groups.get("body") or ""
        detail = re.search(r"(?P<jenis>.*?)\s*-\s*(?P<berat>[\d.]+)\s*kg", body, flags=re.IGNORECASE)
        destination = re.search(r"(A[1-3]|B[1-3]|C[1-3]|TRASH|Sampah|INFO)\s*$", body, flags=re.IGNORECASE)
        return {
            "time": groups.get("time") or "--:--:--",
            "date": groups.get("pipe_date") or groups.get("bracket_date") or "--/--",
            "jenis": (detail.group("jenis") if detail else body or "-").strip(),
            "berat": detail.group("berat") if detail else "0",
            "box": (destination.group(1).upper() if destination else "-"),
            "raw": raw,
        }
    return {"time": "--:--:--", "date": "--/--", "jenis": raw, "berat": "-", "box": "-", "raw": raw}


def log_to_string(event):
    return f"[{event['time']}|{event['date']}] {event['jenis']} - {event['berat']}kg -> {event['box']}"


def format_number(value, digits=1):
    number = as_float(value)
    if abs(number - round(number)) < 0.01:
        return str(int(round(number)))
    return f"{number:.{digits}f}"


def resolve_db_path(path_value):
    raw = Path(str(path_value or DEFAULT_DB_PATH))
    return raw if raw.is_absolute() else APP_DIR / raw


def hash_pin(pin, salt_hex=None, iterations=SECURITY_ITERATIONS):
    salt_hex = salt_hex or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        str(pin).encode("utf-8"),
        bytes.fromhex(salt_hex),
        iterations,
    ).hex()
    return salt_hex, digest


def has_admin_pin(settings):
    security = settings.get("security", {})
    return bool(security.get("admin_pin_salt") and security.get("admin_pin_hash"))


def verify_pin(settings, pin):
    security = settings.get("security", {})
    salt = security.get("admin_pin_salt", "")
    expected = security.get("admin_pin_hash", "")
    iterations = as_int(security.get("pin_iterations"), SECURITY_ITERATIONS)
    if not salt or not expected or not pin:
        return False
    _, digest = hash_pin(pin, salt, iterations)
    return hmac.compare_digest(digest, expected)


class LocalStore:
    def __init__(self, path):
        self.lock = threading.Lock()
        self.path = resolve_db_path(path)
        self.conn = None
        self.open(self.path)

    def open(self, path):
        self.path = resolve_db_path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.conn:
            self.conn.close()
        self.conn = sqlite3.connect(self.path, check_same_thread=False, timeout=5)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.ensure_schema()

    def ensure_schema(self):
        statements = [
            """
            CREATE TABLE IF NOT EXISTS sorting_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_iso TEXT NOT NULL,
                time_text TEXT,
                date_text TEXT,
                jenis TEXT,
                berat_kg REAL,
                destination TEXT,
                confidence INTEGER,
                source TEXT DEFAULT 'ui'
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS operator_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_iso TEXT NOT NULL,
                message TEXT NOT NULL,
                payload_json TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS machine_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_iso TEXT NOT NULL,
                command TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                status TEXT NOT NULL,
                response_json TEXT,
                error TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS conveyor_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_iso TEXT NOT NULL,
                conveyor_key TEXT NOT NULL,
                speed_ms REAL NOT NULL,
                raw_value INTEGER NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS machine_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS reset_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_iso TEXT NOT NULL,
                reason TEXT,
                snapshot_json TEXT NOT NULL
            )
            """,
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_sorting_logs_unique
            ON sorting_logs (time_text, date_text, jenis, berat_kg, destination, source)
            """,
        ]
        with self.lock:
            for statement in statements:
                self.conn.execute(statement)
            self.conn.commit()

    def insert_operator_event(self, message, payload=None):
        with self.lock:
            self.conn.execute(
                "INSERT INTO operator_events (ts_iso, message, payload_json) VALUES (?, ?, ?)",
                (datetime.now().isoformat(timespec="seconds"), message, json.dumps(payload or {}, ensure_ascii=False)),
            )
            self.conn.commit()

    def insert_sort_log(self, event, source="ui"):
        with self.lock:
            self.conn.execute(
                """
                INSERT OR IGNORE INTO sorting_logs
                    (ts_iso, time_text, date_text, jenis, berat_kg, destination, confidence, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(timespec="seconds"),
                    str(event.get("time", "")),
                    str(event.get("date", "")),
                    str(event.get("jenis", "")),
                    as_float(event.get("berat", 0)),
                    str(event.get("box", "")),
                    as_int(event.get("confidence", 0)),
                    source,
                ),
            )
            self.conn.commit()

    def insert_command(self, command, payload, status="queued"):
        with self.lock:
            cursor = self.conn.execute(
                """
                INSERT INTO machine_commands (ts_iso, command, payload_json, status)
                VALUES (?, ?, ?, ?)
                """,
                (datetime.now().isoformat(timespec="seconds"), command, json.dumps(payload, ensure_ascii=False), status),
            )
            self.conn.commit()
            return cursor.lastrowid

    def update_command(self, command_id, status, response=None, error=""):
        with self.lock:
            self.conn.execute(
                """
                UPDATE machine_commands
                SET status = ?, response_json = ?, error = ?
                WHERE id = ?
                """,
                (status, json.dumps(response or {}, ensure_ascii=False), error, command_id),
            )
            self.conn.commit()

    def insert_conveyor_state(self, key, raw_value):
        with self.lock:
            self.conn.execute(
                """
                INSERT INTO conveyor_state (ts_iso, conveyor_key, speed_ms, raw_value)
                VALUES (?, ?, ?, ?)
                """,
                (datetime.now().isoformat(timespec="seconds"), key, as_int(raw_value) / 10, as_int(raw_value)),
            )
            self.conn.commit()

    def set_machine_state(self, key, value):
        with self.lock:
            self.conn.execute(
                """
                INSERT INTO machine_state (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
                """,
                (key, str(value), datetime.now().isoformat(timespec="seconds")),
            )
            self.conn.commit()

    def insert_reset_event(self, reason, snapshot):
        with self.lock:
            self.conn.execute(
                "INSERT INTO reset_events (ts_iso, reason, snapshot_json) VALUES (?, ?, ?)",
                (
                    datetime.now().isoformat(timespec="seconds"),
                    str(reason or ""),
                    json.dumps(snapshot, ensure_ascii=False),
                ),
            )
            self.conn.commit()

    def close(self):
        with self.lock:
            if self.conn:
                self.conn.close()
                self.conn = None


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _event=None):
        if self.tip:
            return
        x = self.widget.winfo_rootx() + 18
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tip,
            text=self.text,
            bg=COLORS["header"],
            fg=COLORS["white"],
            padx=8,
            pady=5,
            font=("Segoe UI", 9),
        )
        label.pack()

    def hide(self, _event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


class Section(tk.Frame):
    def __init__(self, parent, title, subtitle=None):
        super().__init__(
            parent,
            bg=COLORS["panel"],
            highlightthickness=1,
            highlightbackground=COLORS["line"],
            bd=0,
        )
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = tk.Frame(self, bg=COLORS["panel"])
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(8, 4))
        header.grid_columnconfigure(0, weight=1)

        tk.Label(
            header,
            text=title,
            bg=COLORS["panel"],
            fg=COLORS["ink"],
            font=("Segoe UI Semibold", 11),
        ).grid(row=0, column=0, sticky="w")

        if subtitle:
            tk.Label(
                header,
                text=subtitle,
                bg=COLORS["panel"],
                fg=COLORS["muted"],
                font=("Segoe UI", 8),
            ).grid(row=1, column=0, sticky="w", pady=(1, 0))

        self.body = tk.Frame(self, bg=COLORS["panel"])
        self.body.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 10))
        self.body.grid_columnconfigure(0, weight=1)
        self.body.grid_rowconfigure(0, weight=1)


class MetricCard(tk.Frame):
    def __init__(self, parent, title, unit="", accent=COLORS["teal"]):
        super().__init__(
            parent,
            bg=COLORS["white"],
            highlightthickness=1,
            highlightbackground=COLORS["line"],
            bd=0,
        )
        self.value_var = tk.StringVar(value="0")
        self.delta_var = tk.StringVar(value=unit)
        self.accent = accent

        self.grid_columnconfigure(0, weight=1)
        tk.Frame(self, bg=accent, width=5).grid(row=0, column=0, sticky="nsw", rowspan=3)
        tk.Label(
            self,
            text=title.upper(),
            bg=COLORS["white"],
            fg=COLORS["muted"],
            font=("Segoe UI Semibold", 7),
        ).grid(row=0, column=0, sticky="w", padx=(12, 8), pady=(7, 0))
        tk.Label(
            self,
            textvariable=self.value_var,
            bg=COLORS["white"],
            fg=COLORS["ink"],
            font=("Segoe UI Semibold", 15),
        ).grid(row=1, column=0, sticky="w", padx=(12, 8))
        tk.Label(
            self,
            textvariable=self.delta_var,
            bg=COLORS["white"],
            fg=COLORS["muted"],
            font=("Segoe UI", 7),
        ).grid(row=2, column=0, sticky="w", padx=(12, 8), pady=(0, 7))

    def set(self, value, delta=None):
        self.value_var.set(str(value))
        if delta is not None:
            self.delta_var.set(str(delta))


class BoxCell(tk.Frame):
    CAPACITY_KG = 100.0

    def __init__(self, parent, key, command):
        super().__init__(
            parent,
            bg=COLORS["white"],
            highlightthickness=1,
            highlightbackground=COLORS["line"],
            bd=0,
            cursor="hand2",
        )
        self.key = key
        self.command = command
        self.value = 0.0
        self.percent = 0
        self.configure(width=86, height=48)
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)

        self.key_label = tk.Label(
            self,
            text=key,
            bg=COLORS["white"],
            fg=COLORS["steel"],
            font=("Segoe UI Semibold", 7),
        )
        self.key_label.grid(row=0, column=0, sticky="w", padx=7, pady=(4, 0))

        self.value_label = tk.Label(
            self,
            text="0 kg",
            bg=COLORS["white"],
            fg=COLORS["ink"],
            font=("Segoe UI Semibold", 10),
        )
        self.value_label.grid(row=1, column=0, sticky="w", padx=7)

        self.bar = tk.Canvas(self, height=4, bg=COLORS["white"], highlightthickness=0, bd=0)
        self.bar.grid(row=2, column=0, sticky="ew", padx=7, pady=(1, 4))
        self.bar.bind("<Configure>", lambda _event: self.draw_bar())

        for widget in (self, self.key_label, self.value_label, self.bar):
            widget.bind("<Button-1>", lambda _event: self.command(self.key))
            widget.bind("<Enter>", lambda _event: self.configure(highlightbackground=COLORS["teal"]))
            widget.bind("<Leave>", lambda _event: self.configure(highlightbackground=COLORS["line"]))

    def set_value(self, value):
        self.value = as_float(value)
        self.percent = int(clamp((self.value / self.CAPACITY_KG) * 100, 0, 100))
        color = COLORS["green"]
        if self.percent >= 85:
            color = COLORS["red"]
        elif self.percent >= 65:
            color = COLORS["amber"]
        self.value_label.configure(text=f"{format_number(self.value)} kg", fg=color if self.percent >= 65 else COLORS["ink"])
        self.draw_bar()

    def draw_bar(self):
        width = max(self.bar.winfo_width(), 10)
        height = max(self.bar.winfo_height(), 5)
        self.bar.delete("all")
        self.bar.create_rectangle(0, 0, width, height, fill="#d9e0e8", outline="")
        fill_width = max(2, int(width * self.percent / 100))
        color = COLORS["green"] if self.percent < 65 else COLORS["amber"]
        if self.percent >= 85:
            color = COLORS["red"]
        self.bar.create_rectangle(0, 0, fill_width, height, fill=color, outline="")


class ConveyorRow(tk.Frame):
    def __init__(self, parent, name, value, on_change):
        super().__init__(parent, bg=COLORS["panel"])
        self.name = name
        self.on_change = on_change
        self.value_var = tk.IntVar(value=clamp(as_int(value), 0, 20))
        self.text_var = tk.StringVar(value=self.format_speed(self.value_var.get()))
        self.grid_columnconfigure(1, weight=1)

        tk.Label(
            self,
            text=name.replace("_", " ").title(),
            bg=COLORS["panel"],
            fg=COLORS["ink"],
            font=("Segoe UI Semibold", 8),
            width=11,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=1)

        self.scale = tk.Scale(
            self,
            from_=0,
            to=20,
            orient="horizontal",
            variable=self.value_var,
            command=self.changed,
            bg=COLORS["panel"],
            troughcolor="#cfd8e3",
            activebackground=COLORS["teal"],
            highlightthickness=0,
            bd=0,
            width=8,
            sliderlength=16,
            showvalue=False,
        )
        self.scale.grid(row=0, column=1, sticky="ew", padx=(7, 8), pady=0)

        tk.Label(
            self,
            textvariable=self.text_var,
            bg=COLORS["panel"],
            fg=COLORS["steel"],
            font=("Segoe UI Semibold", 8),
            width=8,
            anchor="e",
        ).grid(row=0, column=2, sticky="e", padx=(0, 7))

    @staticmethod
    def format_speed(raw_value):
        return f"{as_int(raw_value) / 10:.1f} m/s"

    def changed(self, value):
        numeric = clamp(as_int(value), 0, 20)
        self.text_var.set(self.format_speed(numeric))
        self.on_change(self.name, numeric)


class SarvaDashboard(tk.Tk):
    def __init__(self):
        enable_dpi_awareness()
        super().__init__()
        self.title("SARVA Fish Sorting Monitor")
        self.configure(bg=COLORS["bg"])
        self.minsize(1180, 720)
        self.geometry("1366x768")
        try:
            self.state("zoomed")
        except tk.TclError:
            pass

        self.settings_data = normalize_settings(load_json(SETTINGS_PATH, DEFAULT_SETTINGS))
        self.data = normalize_data(load_json(DATA_PATH, DEFAULT_DATA))
        self.store = LocalStore(self.settings_data["database"]["path"])
        self.system_running = False
        self.uptime_seconds = 0
        self.timer_job = None
        self.data_poll_job = None
        self.camera_job = None
        self.auto_camera_job = None
        self.camera = None
        self.camera_modules = None
        self.camera_open_queue = queue.Queue()
        self.camera_opening = False
        self.camera_open_started = 0
        self.camera_open_timed_out = False
        self.camera_enabled = False
        self.camera_generation = 0
        self.closing = False
        self.camera_frame_index = 0
        self.last_camera_rgb = None
        self.last_frame_luma = 128
        self.last_frame_std = 0
        self.last_data_mtime = DATA_PATH.stat().st_mtime if DATA_PATH.exists() else 0
        self.camera_setting_vars = {}
        self.camera_value_vars = {}
        self.camera_auto_var = None
        self.db_settings_unlocked = False
        self.db_path_var = None
        self.db_path_entry = None
        self.db_browse_btn = None
        self.db_unlock_btn = None
        self.db_status_var = None
        self.current_detection = {
            "jenis": "Standby",
            "berat": "0",
            "box": "-",
            "confidence": "0%",
        }

        self.metric_cards = {}
        self.box_cells = {}
        self.log_rows = []
        self.conveyor_send_jobs = {}

        self.install_styles()
        self.create_layout()
        self.refresh_all()
        self.draw_camera_placeholder()
        self.tick_clock()

        self.bind("<F5>", lambda _event: self.refresh_all())
        self.bind("<space>", lambda _event: self.toggle_system())
        self.bind("<Control-r>", lambda _event: self.confirm_reset())
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def install_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Treeview",
            background=COLORS["white"],
            foreground=COLORS["ink"],
            fieldbackground=COLORS["white"],
            borderwidth=0,
            rowheight=26,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Treeview.Heading",
            background=COLORS["panel_alt"],
            foreground=COLORS["steel"],
            font=("Segoe UI Semibold", 8),
            borderwidth=0,
        )
        style.map("Treeview", background=[("selected", "#dbeafe")], foreground=[("selected", COLORS["ink"])])

    def create_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.create_header()

        main = tk.Frame(self, bg=COLORS["bg"])
        main.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        main.grid_columnconfigure(0, weight=5)
        main.grid_columnconfigure(1, weight=4)
        main.grid_columnconfigure(2, weight=3)
        main.grid_rowconfigure(0, weight=12)
        main.grid_rowconfigure(1, weight=1)

        self.create_camera_panel(main)
        self.create_metrics_panel(main)
        self.create_box_panel(main)
        self.create_conveyor_panel(main)
        self.create_log_panel(main)
        self.create_controls_panel(main)

    def create_header(self):
        header = tk.Frame(self, bg=COLORS["header"], height=76)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header.grid_propagate(False)
        header.grid_rowconfigure(0, weight=1)
        header.grid_columnconfigure(0, minsize=210)
        header.grid_columnconfigure(1, weight=1)
        header.grid_columnconfigure(2, minsize=96)

        brand = tk.Frame(header, bg=COLORS["header"])
        brand.grid(row=0, column=0, sticky="w", padx=16, pady=6)
        tk.Label(
            brand,
            text="SARVA",
            bg=COLORS["header"],
            fg=COLORS["white"],
            font=("Segoe UI Semibold", 17),
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            brand,
            text="Fish Sorting Monitor",
            bg=COLORS["header"],
            fg="#b6c2cf",
            font=("Segoe UI", 8),
        ).grid(row=1, column=0, sticky="w")

        center = tk.Frame(header, bg=COLORS["header"])
        center.grid(row=0, column=1, sticky="ew", pady=7)
        center.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.status_var = tk.StringVar(value="STANDBY")
        self.uptime_var = tk.StringVar(value="00:00:00")
        self.clock_var = tk.StringVar(value="--:--:--")
        self.camera_state_var = tk.StringVar(value="CAM OFF")

        self.create_header_chip(center, "STATUS", self.status_var, COLORS["amber"], 0)
        self.create_header_chip(center, "UPTIME", self.uptime_var, COLORS["cyan"], 1)
        self.create_header_chip(center, "CLOCK", self.clock_var, COLORS["green"], 2)
        self.create_header_chip(center, "VIDEO", self.camera_state_var, COLORS["steel"], 3)

        right = tk.Frame(header, bg=COLORS["header"])
        right.grid(row=0, column=2, sticky="e", padx=12)
        refresh = tk.Button(
            right,
            text="Refresh",
            bg="#26313c",
            fg=COLORS["white"],
            activebackground="#364553",
            activeforeground=COLORS["white"],
            bd=0,
            padx=14,
            pady=8,
            font=("Segoe UI Semibold", 9),
            command=self.refresh_all,
        )
        refresh.grid(row=0, column=0, padx=4)
        Tooltip(refresh, "Reload data.json and settings.json")

    def create_header_chip(self, parent, label, variable, accent, column):
        chip = tk.Frame(parent, bg="#1f2933", height=52, highlightthickness=1, highlightbackground="#334155")
        chip.grid(row=0, column=column, sticky="ew", padx=5)
        chip.grid_propagate(False)
        chip.grid_columnconfigure(1, weight=1)
        tk.Frame(chip, bg=accent, width=4).grid(row=0, column=0, sticky="ns", rowspan=2)
        tk.Label(chip, text=label, bg="#1f2933", fg="#9aa8b5", font=("Segoe UI Semibold", 7)).grid(
            row=0, column=1, sticky="w", padx=8, pady=(4, 0)
        )
        tk.Label(chip, textvariable=variable, bg="#1f2933", fg=COLORS["white"], font=("Segoe UI Semibold", 9)).grid(
            row=1, column=1, sticky="w", padx=8, pady=(0, 4)
        )

    def create_camera_panel(self, parent):
        section = Section(parent, "Camera Capture", "Camera feed")
        section.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))
        section.body.grid_rowconfigure(0, weight=1)
        section.body.grid_rowconfigure(1, weight=0)

        self.camera_canvas = tk.Canvas(section.body, bg="#101820", highlightthickness=0, bd=0, width=420, height=160)
        self.camera_canvas.grid(row=0, column=0, sticky="nsew")
        self.camera_canvas.bind("<Configure>", lambda _event: self.redraw_camera_surface())

        strip = tk.Frame(section.body, bg=COLORS["panel"])
        strip.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        strip.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.detect_vars = {}
        fields = [
            ("Object", "jenis"),
            ("Weight", "berat"),
            ("Route", "box"),
            ("Confidence", "confidence"),
        ]
        for col, (label, key) in enumerate(fields):
            item = tk.Frame(strip, bg=COLORS["white"], highlightthickness=1, highlightbackground=COLORS["line"])
            item.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 5, 0 if col == 3 else 5))
            self.detect_vars[key] = tk.StringVar(value="-")
            tk.Label(item, text=label.upper(), bg=COLORS["white"], fg=COLORS["muted"], font=("Segoe UI Semibold", 7)).pack(
                anchor="w", padx=9, pady=(7, 0)
            )
            tk.Label(
                item,
                textvariable=self.detect_vars[key],
                bg=COLORS["white"],
                fg=COLORS["ink"],
                font=("Segoe UI Semibold", 13),
            ).pack(anchor="w", padx=9, pady=(0, 7))

    def create_metrics_panel(self, parent):
        section = Section(parent, "Production Summary", "Shift totals")
        section.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        section.body.grid_columnconfigure((0, 1), weight=1)
        section.body.grid_rowconfigure((0, 1), weight=1)

        specs = [
            ("pcs_sorted", "Pcs Sorted", "total pcs", COLORS["teal"]),
            ("kg_sorted", "Kg Sorted", "total kg", COLORS["cyan"]),
            ("pcs_per_hour", "Pcs / Hour", "current rate", COLORS["green"]),
            ("kg_per_hour", "Kg / Hour", "current rate", COLORS["amber"]),
        ]
        for index, (key, title, unit, accent) in enumerate(specs):
            card = MetricCard(section.body, title, unit, accent)
            card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=5, pady=5)
            self.metric_cards[key] = card

    def create_box_panel(self, parent):
        section = Section(parent, "Box Manager", "Storage lanes")
        section.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=(0, 10))
        body = section.body
        for col in range(5):
            body.grid_columnconfigure(col, weight=1 if col < 4 else 2)
        for row in range(5):
            body.grid_rowconfigure(row, weight=1 if row else 0)

        tk.Label(body, text="", bg=COLORS["panel"], fg=COLORS["muted"]).grid(row=0, column=0)
        for col, label in enumerate("ABC", start=1):
            tk.Label(body, text=label, bg=COLORS["panel"], fg=COLORS["steel"], font=("Segoe UI Semibold", 11)).grid(
                row=0, column=col, pady=(0, 6)
            )

        for row_index, row_keys in enumerate(BOX_GRID, start=1):
            tk.Label(
                body,
                text=str(row_index),
                bg=COLORS["panel"],
                fg=COLORS["steel"],
                font=("Segoe UI Semibold", 9),
            ).grid(row=row_index, column=0, sticky="nsew", padx=(0, 5), pady=5)
            for col_index, key in enumerate(row_keys, start=1):
                cell = BoxCell(body, key, self.confirm_reset_box)
                cell.grid(row=row_index, column=col_index, sticky="nsew", padx=5, pady=5)
                self.box_cells[key] = cell

        trash = tk.Frame(body, bg="#fff5f5", highlightthickness=1, highlightbackground="#fecaca", bd=0, cursor="hand2")
        trash.grid(row=1, column=4, rowspan=3, sticky="nsew", padx=(10, 0), pady=5)
        trash.grid_columnconfigure(0, weight=1)
        trash.grid_rowconfigure(0, weight=1)
        trash.grid_rowconfigure(1, weight=0)
        trash.grid_rowconfigure(2, weight=0)
        trash.grid_rowconfigure(3, weight=1)
        self.trash_value_var = tk.StringVar(value="0 kg")
        tk.Label(trash, text="REJECT", bg="#fff5f5", fg=COLORS["red"], font=("Segoe UI Semibold", 10)).grid(
            row=1, column=0, sticky="s", pady=(0, 4)
        )
        tk.Label(trash, textvariable=self.trash_value_var, bg="#fff5f5", fg=COLORS["red"], font=("Segoe UI Semibold", 21)).grid(
            row=2, column=0, sticky="n", pady=(0, 2)
        )
        tk.Label(trash, text="reject bin", bg="#fff5f5", fg="#991b1b", font=("Segoe UI", 8)).grid(row=3, column=0, sticky="n")
        for widget in trash.winfo_children() + [trash]:
            widget.bind("<Button-1>", lambda _event: self.confirm_reset_trash())

    def create_conveyor_panel(self, parent):
        section = Section(parent, "Velocity Manager", "Conveyor speed in m/s")
        section.grid(row=1, column=1, sticky="nsew", padx=(0, 10))
        section.body.grid_columnconfigure(0, weight=1)
        for row_index in range(len(CONVEYOR_KEYS)):
            section.body.grid_rowconfigure(row_index, weight=0, minsize=22)

        self.conveyor_rows = {}
        for index, key in enumerate(CONVEYOR_KEYS):
            row = ConveyorRow(section.body, key, self.settings_data["conveyor"].get(key, 0), self.on_conveyor_change)
            row.grid(row=index, column=0, sticky="ew", pady=0)
            self.conveyor_rows[key] = row

        hint = tk.Frame(section.body, bg=COLORS["panel_alt"], highlightthickness=1, highlightbackground=COLORS["line"])
        hint.grid(row=len(CONVEYOR_KEYS), column=0, sticky="ew", pady=(4, 0))
        section.body.grid_rowconfigure(len(CONVEYOR_KEYS), weight=0)
        section.body.grid_rowconfigure(len(CONVEYOR_KEYS) + 1, weight=1)
        tk.Label(
            hint,
            text="Conveyor tab values become the default speed when START SYSTEM runs.",
            bg=COLORS["panel_alt"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8),
        ).pack(anchor="w", padx=9, pady=5)

    def create_log_panel(self, parent):
        section = Section(parent, "Log Activity", "Recent sorting events")
        section.grid(row=0, column=2, sticky="nsew", pady=(0, 10))
        body = section.body
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        columns = ("time", "type", "weight", "dest")
        self.log_table = ttk.Treeview(body, columns=columns, show="headings", selectmode="browse")
        headings = {
            "time": ("Time", 74),
            "type": ("Object", 92),
            "weight": ("Kg", 54),
            "dest": ("Box", 54),
        }
        for col, (text, width) in headings.items():
            self.log_table.heading(col, text=text)
            self.log_table.column(col, width=width, minwidth=42, stretch=col == "type", anchor="w")
        self.log_table.grid(row=0, column=0, sticky="nsew")

        scroll = ttk.Scrollbar(body, orient="vertical", command=self.log_table.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.log_table.configure(yscrollcommand=scroll.set)
        self.log_table.tag_configure("reject", foreground=COLORS["red"])
        self.log_table.tag_configure("normal", foreground=COLORS["ink"])

    def create_controls_panel(self, parent):
        section = Section(parent, "Machine Control", "System commands")
        section.grid(row=1, column=2, sticky="nsew")
        body = section.body
        body.grid_columnconfigure(0, weight=1)
        for row in range(4):
            body.grid_rowconfigure(row, weight=1, uniform="machine_actions")

        self.start_btn = self.make_button(body, "START", COLORS["green"], self.start_system)
        self.stop_btn = self.make_button(body, "STOP", COLORS["red"], self.stop_system)
        self.reset_btn = self.make_button(body, "RESET", COLORS["amber"], self.confirm_reset)
        self.settings_btn = self.make_button(body, "SETTINGS", COLORS["steel"], self.open_settings_window)

        self.start_btn.grid(row=0, column=0, sticky="nsew", pady=(0, 4))
        self.stop_btn.grid(row=1, column=0, sticky="nsew", pady=4)
        self.reset_btn.grid(row=2, column=0, sticky="nsew", pady=4)
        self.settings_btn.grid(row=3, column=0, sticky="nsew", pady=(4, 0))

        self.route_var = tk.StringVar(value="Last route: -")
        self.health_var = tk.StringVar(value="Data file: ready")
        self.command_status_var = tk.StringVar(value="Raspi command: idle")

    def make_button(self, parent, text, color, command):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg=COLORS["white"],
            activebackground=color,
            activeforeground=COLORS["white"],
            bd=0,
            padx=10,
            pady=6,
            font=("Segoe UI Semibold", 9),
            cursor="hand2",
        )

    def start_camera(self):
        if self.camera_enabled:
            return
        self.camera_enabled = True
        self.camera_generation += 1
        self.camera_state_var.set("CAM START")
        self.load_optional_camera(self.camera_generation)
        self.update_camera()
        if self.settings_data.get("camera", {}).get("auto", False):
            self.auto_adjust_camera_settings()

    def stop_camera(self):
        self.camera_enabled = False
        self.camera_generation += 1
        self.camera_opening = False
        self.camera_open_timed_out = False
        if self.camera_job:
            self.after_cancel(self.camera_job)
            self.camera_job = None
        if self.auto_camera_job:
            self.after_cancel(self.auto_camera_job)
            self.auto_camera_job = None
        if self.camera:
            self.camera.release()
            self.camera = None
        self.last_camera_rgb = None
        self.camera_state_var.set("CAM OFF")
        self.draw_camera_placeholder()

    def load_optional_camera(self, generation):
        try:
            import cv2
            from PIL import Image, ImageTk
        except Exception:
            self.camera_modules = None
            self.camera_state_var.set("CAM SIM")
            return

        self.camera_modules = (cv2, Image, ImageTk)
        self.camera_state_var.set("CAM OPEN")
        self.camera_opening = True
        self.camera_open_timed_out = False
        self.camera_open_started = monotonic()
        threading.Thread(target=self.open_camera_worker, args=(cv2, generation), daemon=True).start()
        self.after(120, self.poll_camera_open)

    def open_camera_worker(self, cv2, generation):
        backends = [cv2.CAP_DSHOW] if hasattr(cv2, "CAP_DSHOW") else [0]
        for backend in backends:
            camera = None
            try:
                camera = cv2.VideoCapture(0, backend)
                if camera and camera.isOpened():
                    if hasattr(cv2, "VideoWriter_fourcc"):
                        camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
                    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                    camera.set(cv2.CAP_PROP_FPS, 60)
                    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    self.camera_open_queue.put((generation, "ok", camera))
                    return
            except Exception as exc:
                self.camera_open_queue.put((generation, "error", str(exc)))
            if camera:
                camera.release()
        self.camera_open_queue.put((generation, "none", None))

    def poll_camera_open(self):
        if self.closing:
            return
        try:
            generation, status, payload = self.camera_open_queue.get_nowait()
        except queue.Empty:
            if self.camera_opening and not self.camera_open_timed_out and monotonic() - self.camera_open_started > 2.5:
                self.camera_open_timed_out = True
                self.camera_state_var.set("CAM SIM")
            self.after(500 if self.camera_open_timed_out else 160, self.poll_camera_open)
            return

        if generation != self.camera_generation or not self.camera_enabled:
            if status == "ok" and payload:
                payload.release()
            return

        self.camera_opening = False
        self.camera_open_timed_out = False
        if status == "ok":
            self.camera = payload
            self.apply_camera_settings(save=False)
            cv2 = self.camera_modules[0]
            fps = self.camera.get(cv2.CAP_PROP_FPS) or 60
            self.camera_state_var.set(f"CAM 0 {int(round(fps))}FPS")
        else:
            self.camera = None
            self.camera_state_var.set("CAM SIM")

    def apply_camera_settings(self, save=True):
        if save:
            save_json(SETTINGS_PATH, self.settings_data)
        if not self.camera or not self.camera_modules:
            return

        cv2 = self.camera_modules[0]
        settings = self.settings_data.get("camera", {})
        auto = bool(settings.get("auto", False))
        for auto_value in ((0.75 if auto else 0.25), (1 if auto else 0)):
            try:
                self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, auto_value)
            except Exception:
                pass

        if auto:
            return

        prop_map = {
            "brightness": getattr(cv2, "CAP_PROP_BRIGHTNESS", None),
            "contrast": getattr(cv2, "CAP_PROP_CONTRAST", None),
            "exposure": getattr(cv2, "CAP_PROP_EXPOSURE", None),
            "gain": getattr(cv2, "CAP_PROP_GAIN", None),
            "hue": getattr(cv2, "CAP_PROP_HUE", None),
        }
        for key, prop in prop_map.items():
            if prop is None:
                continue
            try:
                self.camera.set(prop, int(settings.get(key, 0)))
            except Exception:
                pass

    def apply_preview_adjustments(self, frame, cv2):
        settings = self.settings_data.get("camera", {})
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean, std = cv2.meanStdDev(gray)
        self.last_frame_luma = float(mean[0][0])
        self.last_frame_std = float(std[0][0])

        brightness = as_int(settings.get("brightness"))
        exposure = as_int(settings.get("exposure"))
        contrast = as_int(settings.get("contrast"))
        gain = as_int(settings.get("gain"))
        hue = as_int(settings.get("hue"))

        alpha = clamp(1.0 + (contrast / 120.0) + (max(gain, 0) / 220.0), 0.25, 2.4)
        beta = clamp((brightness * 1.1) + (exposure * 0.45) + (gain * 0.28), -150, 150)
        adjusted = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)
        if hue:
            hsv = cv2.cvtColor(adjusted, cv2.COLOR_BGR2HSV)
            hsv[:, :, 0] = (hsv[:, :, 0].astype("int16") + int(hue * 0.9)) % 180
            adjusted = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        return cv2.cvtColor(adjusted, cv2.COLOR_BGR2RGB)

    def tick_clock(self):
        self.clock_var.set(datetime.now().strftime("%H:%M:%S"))
        if self.system_running:
            self.uptime_seconds += 1
            self.uptime_var.set(self.format_duration(self.uptime_seconds))
            self.update_rates()
        self.timer_job = self.after(1000, self.tick_clock)

    def update_camera(self):
        if not self.camera_enabled:
            return
        if self.camera and self.camera_modules:
            cv2, Image, ImageTk = self.camera_modules
            ok, frame = self.camera.read()
            if ok:
                self.last_camera_rgb = self.apply_preview_adjustments(frame, cv2)
                self.render_camera_rgb(self.last_camera_rgb)
            else:
                self.draw_camera_placeholder()
        else:
            self.draw_camera_placeholder()
        self.camera_job = self.after(16 if self.camera else 33, self.update_camera)

    def redraw_camera_surface(self):
        if self.last_camera_rgb is not None and self.camera_modules:
            self.render_camera_rgb(self.last_camera_rgb)
        else:
            self.draw_camera_placeholder()

    def render_camera_rgb(self, frame_rgb):
        _, Image, ImageTk = self.camera_modules
        canvas_width = max(self.camera_canvas.winfo_width(), 1)
        canvas_height = max(self.camera_canvas.winfo_height(), 1)
        if canvas_width < 2 or canvas_height < 2:
            return
        image = Image.fromarray(frame_rgb)
        src_width, src_height = image.size
        scale = min(canvas_width / src_width, canvas_height / src_height)
        target_width = max(1, int(src_width * scale))
        target_height = max(1, int(src_height * scale))
        image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        self.camera_canvas.delete("all")
        self.camera_canvas.create_rectangle(0, 0, canvas_width, canvas_height, fill="#101820", outline="")
        self.camera_canvas.create_image(canvas_width // 2, canvas_height // 2, image=photo, anchor="center")
        self.camera_canvas.image = photo
        self.draw_detection_overlay(canvas_width, canvas_height)

    def draw_camera_placeholder(self):
        width = max(self.camera_canvas.winfo_width(), 1)
        height = max(self.camera_canvas.winfo_height(), 1)
        if width < 2 or height < 2:
            return
        if not self.camera_enabled:
            self.camera_canvas.delete("all")
            self.camera_canvas.create_rectangle(0, 0, width, height, fill="#101820", outline="")
            self.camera_canvas.create_text(
                width // 2,
                height // 2 - 8,
                text="CAMERA OFF",
                fill="#cbd5e1",
                font=("Segoe UI Semibold", 18),
            )
            if height >= 160:
                self.camera_canvas.create_text(
                    width // 2,
                    height // 2 + 22,
                    text="Press START SYSTEM to enable camera and machine polling",
                    fill="#94a3b8",
                    font=("Segoe UI", 10),
                )
            return
        settings = self.settings_data.get("camera", {})
        brightness = as_int(settings.get("brightness"))
        exposure = as_int(settings.get("exposure"))
        contrast = as_int(settings.get("contrast"))
        gain = as_int(settings.get("gain"))
        hue = as_int(settings.get("hue"))
        self.last_frame_luma = clamp(105 + brightness * 0.55 + exposure * 0.35 + gain * 0.22, 20, 235)
        self.last_frame_std = clamp(38 + contrast * 0.3, 10, 90)
        base = int(clamp(self.last_frame_luma * 0.18, 10, 42))
        lane = int(clamp(self.last_frame_luma * 0.32, 35, 92))
        fish_shift = int(clamp(hue + 100, 0, 200))
        self.camera_canvas.delete("all")
        self.camera_canvas.create_rectangle(0, 0, width, height, fill=f"#{base:02x}{base + 8:02x}{base + 14:02x}", outline="")

        lane_y = int(height * 0.58)
        self.camera_canvas.create_rectangle(0, lane_y - 46, width, lane_y + 44, fill=f"#{lane:02x}{lane + 10:02x}{lane + 18:02x}", outline="")
        for x in range(-80, width + 90, 64):
            offset = (self.camera_frame_index * 9) % 64
            self.camera_canvas.create_line(x + offset, lane_y - 46, x + 36 + offset, lane_y + 44, fill="#3b4a58", width=2)

        fish_x = int(width * 0.47 + (self.camera_frame_index % 8 - 4) * 3)
        fish_y = lane_y - 6
        fish_color = f"#{clamp(178 + fish_shift // 8, 0, 255):02x}{clamp(196 + brightness // 8, 0, 255):02x}{clamp(210 - fish_shift // 10, 0, 255):02x}"
        self.camera_canvas.create_oval(fish_x - 92, fish_y - 32, fish_x + 78, fish_y + 28, fill=fish_color, outline="#8393a2", width=2)
        self.camera_canvas.create_polygon(
            fish_x + 70,
            fish_y,
            fish_x + 125,
            fish_y - 34,
            fish_x + 116,
            fish_y,
            fish_x + 125,
            fish_y + 34,
            fill="#b8c4cf",
            outline="#8393a2",
        )
        self.camera_canvas.create_oval(fish_x - 58, fish_y - 9, fish_x - 45, fish_y + 4, fill="#111827", outline="")
        self.camera_canvas.create_line(fish_x - 20, fish_y - 28, fish_x + 28, fish_y - 4, fill="#8a99a8", width=2)
        self.draw_detection_overlay(width, height)

        self.camera_canvas.create_text(
            16,
            18,
            text="CAMERA TEST PATTERN",
            anchor="w",
            fill="#94a3b8",
            font=("Consolas", 9),
        )
        self.camera_frame_index += 1

    def draw_detection_overlay(self, width, height):
        x1 = int(width * 0.23)
        y1 = int(height * 0.30)
        x2 = int(width * 0.76)
        y2 = int(height * 0.75)
        color = "#22c55e" if self.system_running else "#f59e0b"
        self.camera_canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=2)
        label = f"{self.current_detection['jenis']}  {self.current_detection['berat']} kg  {self.current_detection['box']}"
        self.camera_canvas.create_rectangle(x1, y1 - 24, x1 + 260, y1, fill=color, outline=color)
        self.camera_canvas.create_text(x1 + 8, y1 - 12, text=label, anchor="w", fill=COLORS["white"], font=("Segoe UI Semibold", 9))

    def refresh_all(self):
        self.settings_data = normalize_settings(load_json(SETTINGS_PATH, DEFAULT_SETTINGS))
        self.data = normalize_data(load_json(DATA_PATH, DEFAULT_DATA))
        db_path = resolve_db_path(self.settings_data["database"].get("path"))
        if db_path != self.store.path:
            self.store.open(db_path)
        self.apply_camera_settings(save=False)
        self.refresh_conveyors_from_settings()
        self.refresh_metrics()
        self.refresh_boxes()
        self.refresh_logs()
        self.sync_json_logs_to_sqlite()
        self.refresh_detection()
        self.health_var.set(f"Data file: {DATA_PATH.name} loaded")

    def refresh_conveyors_from_settings(self):
        for key, row in self.conveyor_rows.items():
            value = clamp(as_int(self.settings_data.get("conveyor", {}).get(key)), 0, 20)
            row.value_var.set(value)
            row.text_var.set(ConveyorRow.format_speed(value))

    def refresh_metrics(self):
        info = self.data.get("info_data", {})
        for key, card in self.metric_cards.items():
            value = info.get(key, "0")
            if key.startswith("kg"):
                value = format_number(value)
            card.set(value)

    def refresh_boxes(self):
        for key, cell in self.box_cells.items():
            cell.set_value(self.data["box_manager"].get(key, "0"))
        self.trash_value_var.set(f"{format_number(self.data.get('trash', '0'))} kg")

    def refresh_logs(self):
        for row in self.log_table.get_children():
            self.log_table.delete(row)
        self.log_rows = [parse_log_entry(item) for item in self.data.get("log_activity", [])][-250:]
        for entry in reversed(self.log_rows[-80:]):
            tag = "reject" if entry["box"].upper() in {"TRASH", "SAMPAH"} else "normal"
            self.log_table.insert("", "end", values=(entry["time"], entry["jenis"], entry["berat"], entry["box"]), tags=(tag,))

    def sync_json_logs_to_sqlite(self):
        for item in self.data.get("log_activity", []):
            entry = parse_log_entry(item)
            self.store.insert_sort_log(
                {
                    "time": entry["time"],
                    "date": entry["date"],
                    "jenis": entry["jenis"],
                    "berat": entry["berat"],
                    "box": entry["box"],
                    "confidence": 0,
                },
                source="json",
            )

    def refresh_detection(self):
        self.detect_vars["jenis"].set(self.current_detection["jenis"])
        self.detect_vars["berat"].set(f"{self.current_detection['berat']} kg")
        self.detect_vars["box"].set(self.current_detection["box"])
        self.detect_vars["confidence"].set(self.current_detection["confidence"])
        self.route_var.set(f"Last route: {self.current_detection['box']}")

    def build_command_payload(self, command, extra=None):
        payload = {
            "command": command,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "source": "sarva_pc_ui",
            "conveyor": {key: as_int(value) / 10 for key, value in self.settings_data.get("conveyor", {}).items()},
            "range": self.settings_data.get("range", {}),
        }
        if extra:
            payload.update(extra)
        return payload

    def dispatch_machine_command(self, command, extra=None):
        payload = self.build_command_payload(command, extra)
        command_id = self.store.insert_command(command, payload, status="queued")
        self.command_status_var.set(f"Raspi command: {command} queued")
        threading.Thread(target=self.send_raspi_command_worker, args=(command_id, command, payload), daemon=True).start()

    def send_raspi_command_worker(self, command_id, command, payload):
        cfg = self.settings_data.get("raspi", {})
        if not cfg.get("enabled", True):
            self.store.update_command(command_id, "skipped", {"reason": "raspi disabled"})
            self.after(0, lambda: self.command_status_var.set("Raspi command: disabled in settings"))
            return

        host = str(cfg.get("host", "")).strip()
        port = as_int(cfg.get("port"), 65432)
        timeout = as_float(cfg.get("timeout"), 1.5)
        if not host or port <= 0:
            self.store.update_command(command_id, "failed", error="invalid raspi host/port")
            self.after(0, lambda: self.command_status_var.set("Raspi command: invalid host/port"))
            return

        message = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        try:
            with socket.create_connection((host, port), timeout=timeout) as client:
                client.settimeout(timeout)
                client.sendall(message)
                try:
                    response_raw = client.recv(4096)
                except socket.timeout:
                    response_raw = b""
            response = {}
            if response_raw:
                try:
                    response = json.loads(response_raw.decode("utf-8"))
                except json.JSONDecodeError:
                    response = {"raw": response_raw.decode("utf-8", errors="replace")}
            self.store.update_command(command_id, "sent", response)
            self.after(0, lambda: self.command_status_var.set(f"Raspi command: {command} sent"))
        except OSError as exc:
            error_text = str(exc)
            self.store.update_command(command_id, "failed", error=error_text)
            self.after(0, lambda: self.command_status_var.set(f"Raspi command failed: {error_text}"))

    def start_system(self):
        if self.system_running:
            return
        self.system_running = True
        self.status_var.set("RUNNING")
        self.refresh_conveyors_from_settings()
        self.start_camera()
        self.store.set_machine_state("system_status", "RUNNING")
        self.dispatch_machine_command(
            "system_start",
            {
                "status": "RUNNING",
                "conveyor_defaults": {key: as_int(value) / 10 for key, value in self.settings_data.get("conveyor", {}).items()},
            },
        )
        self.log_operator_event("Sistem dimulai")
        self.poll_live_data()

    def stop_system(self):
        self.system_running = False
        self.status_var.set("STOPPED")
        self.stop_camera()
        self.store.set_machine_state("system_status", "STOPPED")
        self.dispatch_machine_command("system_stop", {"status": "STOPPED"})
        if self.data_poll_job:
            self.after_cancel(self.data_poll_job)
            self.data_poll_job = None
        self.log_operator_event("Sistem dihentikan")

    def toggle_system(self):
        if self.system_running:
            self.stop_system()
        else:
            self.start_system()

    def confirm_reset(self):
        first = messagebox.askyesno(
            "Reset Sistem",
            "Reset akan menghapus statistik, isi box, reject bin, dan log tampilan. Lanjutkan?",
        )
        if not first:
            return
        confirmation = simpledialog.askstring(
            "Konfirmasi Reset",
            "Ketik RESET untuk konfirmasi kedua.",
            parent=self,
        )
        if confirmation != "RESET":
            self.store.insert_operator_event("Reset cancelled: confirmation mismatch", {})
            messagebox.showinfo("Reset dibatalkan", "Konfirmasi tidak sesuai.")
            return
        self.reset_system("operator_double_confirm")

    def reset_system(self, reason="operator"):
        snapshot = {
            "reason": reason,
            "data": self.data,
            "system_running": self.system_running,
            "uptime_seconds": self.uptime_seconds,
        }
        self.store.insert_reset_event(reason, snapshot)
        self.store.insert_operator_event("Reset confirmed", {"reason": reason})
        self.system_running = False
        self.status_var.set("RESET")
        self.stop_camera()
        if self.data_poll_job:
            self.after_cancel(self.data_poll_job)
            self.data_poll_job = None
        self.uptime_seconds = 0
        self.uptime_var.set("00:00:00")
        self.data = normalize_data(DEFAULT_DATA)
        save_json(DATA_PATH, self.data)
        self.current_detection = {"jenis": "Standby", "berat": "0", "box": "-", "confidence": "0%"}
        self.store.set_machine_state("system_status", "RESET")
        self.dispatch_machine_command("system_reset", {"status": "RESET", "reason": reason})
        self.refresh_all()
        self.log_operator_event("Sistem direset")

    def poll_live_data(self):
        if not self.system_running:
            return
        try:
            mtime = DATA_PATH.stat().st_mtime if DATA_PATH.exists() else 0
            if mtime != self.last_data_mtime:
                self.last_data_mtime = mtime
                self.data = normalize_data(load_json(DATA_PATH, DEFAULT_DATA))
                self.refresh_metrics()
                self.refresh_boxes()
                self.refresh_logs()
                self.sync_json_logs_to_sqlite()
                self.health_var.set("Live data synced")
        except OSError as exc:
            self.health_var.set(f"Live data error: {exc}")
        self.data_poll_job = self.after(250, self.poll_live_data)

    def log_operator_event(self, message):
        now = datetime.now()
        event = {
            "time": now.strftime("%H:%M:%S"),
            "date": now.strftime("%d/%m"),
            "jenis": message,
            "berat": "0",
            "box": "INFO",
        }
        self.data.setdefault("log_activity", []).append(log_to_string(event))
        self.data["log_activity"] = self.data["log_activity"][-250:]
        save_json(DATA_PATH, self.data)
        self.store.insert_operator_event(message, event)
        self.refresh_logs()

    def route_for_detection(self, fish, weight):
        if fish == "Sampah" or weight < 0.4:
            return "TRASH"
        column = "A" if weight < 1.25 else "B" if weight < 2.4 else "C"
        row = 1 if weight < 1.0 else 2 if weight < 2.2 else 3
        return f"{column}{row}"

    def ingest_sort_event(self, event):
        fish = str(event.get("jenis", "Unknown"))
        weight = as_float(event.get("berat", 0.0))
        box = str(event.get("box") or event.get("destination") or self.route_for_detection(fish, weight)).upper()
        if box == "SAMPAH":
            box = "TRASH"

        self.current_detection = {
            "jenis": fish,
            "berat": format_number(weight),
            "box": box,
            "confidence": f"{as_int(event.get('confidence'), 94)}%",
        }

        if box == "TRASH":
            self.data["trash"] = str(round(as_float(self.data.get("trash")) + weight, 1))
        elif box in self.data["box_manager"]:
            self.data["box_manager"][box] = str(round(as_float(self.data["box_manager"].get(box)) + weight, 1))

        info = self.data["info_data"]
        info["pcs_sorted"] = str(as_int(info.get("pcs_sorted")) + 1)
        info["kg_sorted"] = str(round(as_float(info.get("kg_sorted")) + weight, 1))
        self.update_rates()

        now = datetime.now()
        payload = {
            "time": str(event.get("time", now.strftime("%H:%M:%S"))),
            "date": str(event.get("date", now.strftime("%d/%m"))),
            "jenis": fish,
            "berat": format_number(weight),
            "box": box,
        }
        self.data.setdefault("log_activity", []).append(log_to_string(payload))
        self.data["log_activity"] = self.data["log_activity"][-250:]
        save_json(DATA_PATH, self.data)
        self.store.insert_sort_log({**payload, "confidence": event.get("confidence", 0)}, source="ui")

        self.refresh_metrics()
        self.refresh_boxes()
        self.refresh_logs()
        self.refresh_detection()

    def update_rates(self):
        seconds = max(self.uptime_seconds, 1)
        hours = seconds / 3600
        info = self.data.get("info_data", {})
        pcs = as_float(info.get("pcs_sorted"))
        kg = as_float(info.get("kg_sorted"))
        info["pcs_per_hour"] = str(int(round(pcs / hours))) if self.system_running else info.get("pcs_per_hour", "0")
        info["kg_per_hour"] = str(round(kg / hours, 1)) if self.system_running else info.get("kg_per_hour", "0")
        self.refresh_metrics()

    def confirm_reset_box(self, key):
        if messagebox.askyesno("Reset Box", f"Reset isi box {key} ke 0 kg?"):
            self.data["box_manager"][key] = "0"
            save_json(DATA_PATH, self.data)
            self.refresh_boxes()
            self.dispatch_machine_command("reset_box", {"box": key})
            self.log_operator_event(f"Box {key} direset")

    def confirm_reset_trash(self):
        if messagebox.askyesno("Reset Reject Bin", "Reset reject/trash bin ke 0 kg?"):
            self.data["trash"] = "0"
            save_json(DATA_PATH, self.data)
            self.refresh_boxes()
            self.dispatch_machine_command("reset_reject_bin", {"box": "TRASH"})
            self.log_operator_event("Reject bin direset")

    def on_conveyor_change(self, key, value):
        self.settings_data.setdefault("conveyor", {})[key] = value
        save_json(SETTINGS_PATH, self.settings_data)
        self.store.insert_conveyor_state(key, value)
        self.schedule_conveyor_command(key, value)

    def schedule_conveyor_command(self, key, value):
        previous = self.conveyor_send_jobs.get(key)
        if previous:
            self.after_cancel(previous)
        self.conveyor_send_jobs[key] = self.after(180, lambda: self.send_conveyor_command(key, value))

    def send_conveyor_command(self, key, value):
        self.conveyor_send_jobs.pop(key, None)
        self.dispatch_machine_command(
            "set_conveyor_speed",
            {
                "conveyor_key": key,
                "speed_ms": as_int(value) / 10,
                "raw_value": as_int(value),
            },
        )

    def export_csv(self):
        filename = filedialog.asksaveasfilename(
            title="Export sorting log",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not filename:
            return
        rows = [parse_log_entry(item) for item in self.data.get("log_activity", [])]
        try:
            with open(filename, "w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["time", "date", "object", "weight_kg", "destination"])
                for row in rows:
                    writer.writerow([row["time"], row["date"], row["jenis"], row["berat"], row["box"]])
            self.health_var.set(f"Exported: {Path(filename).name}")
        except OSError as exc:
            messagebox.showerror("Export gagal", str(exc))

    def open_settings_window(self):
        if hasattr(self, "settings_window") and self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.focus()
            return

        self.settings_window = tk.Toplevel(self)
        self.settings_window.title("SARVA Settings")
        self.settings_window.geometry("780x640")
        self.settings_window.minsize(720, 560)
        self.settings_window.configure(bg=COLORS["bg"])
        self.settings_window.transient(self)
        self.settings_window.grab_set()

        self.settings_window.grid_columnconfigure(0, weight=1)
        self.settings_window.grid_rowconfigure(1, weight=1)

        top = tk.Frame(self.settings_window, bg=COLORS["header"], height=52)
        top.grid(row=0, column=0, sticky="ew")
        top.grid_propagate(False)
        tk.Label(top, text="Settings", bg=COLORS["header"], fg=COLORS["white"], font=("Segoe UI Semibold", 15)).pack(
            side="left", padx=16
        )

        notebook = ttk.Notebook(self.settings_window)
        self.settings_notebook = notebook
        notebook.grid(row=1, column=0, sticky="nsew", padx=12, pady=12)

        camera_tab = self.make_settings_tab(notebook)
        conveyor_tab = self.make_settings_tab(notebook)
        range_tab = self.make_settings_tab(notebook)
        data_tab = self.make_settings_tab(notebook)
        database_tab = self.make_settings_tab(notebook)
        raspi_tab = self.make_settings_tab(notebook)
        notebook.add(camera_tab, text="Camera")
        notebook.add(conveyor_tab, text="Conveyor")
        notebook.add(range_tab, text="Range")
        notebook.add(data_tab, text="Data")
        notebook.add(database_tab, text="SQLite")
        notebook.add(raspi_tab, text="Raspi WiFi")

        setting_vars = {"camera": {}, "conveyor": {}, "range": {}, "database": {}, "raspi": {}}
        self.populate_camera_settings(camera_tab, setting_vars["camera"])
        self.populate_conveyor_settings(conveyor_tab, setting_vars["conveyor"])
        self.populate_range_settings(range_tab, setting_vars["range"])
        self.populate_data_tools(data_tab)
        self.populate_database_settings(database_tab, setting_vars["database"])
        self.populate_raspi_settings(raspi_tab, setting_vars["raspi"])

        buttons = tk.Frame(self.settings_window, bg=COLORS["bg"])
        buttons.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        buttons.grid_columnconfigure(0, weight=1)
        tk.Button(
            buttons,
            text="Cancel",
            bg=COLORS["steel"],
            fg=COLORS["white"],
            bd=0,
            padx=18,
            pady=9,
            command=self.close_settings,
        ).grid(row=0, column=1, padx=5)
        tk.Button(
            buttons,
            text="Apply",
            bg=COLORS["green"],
            fg=COLORS["white"],
            bd=0,
            padx=18,
            pady=9,
            command=lambda: self.apply_settings(setting_vars),
        ).grid(row=0, column=2, padx=5)

        self.center_window(self.settings_window)

    def make_settings_tab(self, notebook):
        tab = tk.Frame(notebook, bg=COLORS["panel"])
        tab.grid_columnconfigure(0, weight=1)
        return tab

    def populate_camera_settings(self, parent, var_bucket):
        self.camera_setting_vars = var_bucket
        self.camera_value_vars = {}
        parent.grid_columnconfigure(1, weight=1)
        row = 0
        for key in ["brightness", "exposure", "contrast", "gain", "hue"]:
            value = self.settings_data["camera"].get(key, 0)
            tk.Label(parent, text=key.title(), bg=COLORS["panel"], fg=COLORS["ink"], font=("Segoe UI", 10)).grid(
                row=row, column=0, sticky="w", padx=18, pady=12
            )
            var = tk.IntVar(value=value)
            value_var = tk.StringVar(value=str(value))
            scale = tk.Scale(
                parent,
                from_=-100,
                to=100,
                orient="horizontal",
                variable=var,
                command=lambda val, item=key, target=value_var: self.update_camera_setting(item, val, target),
                bg=COLORS["panel"],
                troughcolor="#cfd8e3",
                highlightthickness=0,
                showvalue=False,
            )
            scale.grid(row=row, column=1, sticky="ew", padx=12, pady=8)
            tk.Label(parent, textvariable=value_var, bg=COLORS["panel"], fg=COLORS["steel"], width=5).grid(
                row=row, column=2, sticky="e", padx=18
            )
            var_bucket[key] = var
            self.camera_value_vars[key] = value_var
            row += 1

        auto_var = tk.BooleanVar(value=self.settings_data["camera"].get("auto", False))
        self.camera_auto_var = auto_var
        tk.Checkbutton(
            parent,
            text="Auto exposure/gain",
            variable=auto_var,
            command=lambda: self.update_camera_auto(auto_var),
            bg=COLORS["panel"],
            fg=COLORS["ink"],
            activebackground=COLORS["panel"],
            font=("Segoe UI", 10),
        ).grid(row=row, column=0, columnspan=3, sticky="w", padx=16, pady=12)
        var_bucket["auto"] = auto_var
        tk.Label(
            parent,
            text="Realtime: sliders update preview and camera hardware immediately.",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8),
        ).grid(row=row + 1, column=0, columnspan=3, sticky="w", padx=18, pady=(0, 12))

    def update_camera_setting(self, key, value, label_var=None):
        numeric = clamp(as_int(value), -100, 100)
        self.settings_data.setdefault("camera", {})[key] = numeric
        if label_var is not None:
            label_var.set(str(numeric))
        if key in self.camera_setting_vars:
            self.camera_setting_vars[key].set(numeric)
        self.apply_camera_settings(save=True)
        self.redraw_camera_surface()

    def update_camera_auto(self, auto_var):
        auto_enabled = bool(auto_var.get())
        self.settings_data.setdefault("camera", {})["auto"] = auto_enabled
        self.apply_camera_settings(save=True)
        if auto_enabled:
            if self.auto_camera_job:
                self.after_cancel(self.auto_camera_job)
                self.auto_camera_job = None
            self.auto_adjust_camera_settings()
        elif self.auto_camera_job:
            self.after_cancel(self.auto_camera_job)
            self.auto_camera_job = None

    def auto_adjust_camera_settings(self):
        if not self.settings_data.get("camera", {}).get("auto", False):
            self.auto_camera_job = None
            return
        target_luma = 128
        error = target_luma - float(self.last_frame_luma)
        contrast_target = clamp(int((42 - self.last_frame_std) * 0.7), -20, 35)
        changes = {
            "exposure": int(round(error * 0.08)),
            "brightness": int(round(error * 0.10)),
            "gain": int(round(error * 0.05)),
            "contrast": int(round((contrast_target - as_int(self.settings_data["camera"].get("contrast"))) * 0.18)),
        }
        for key, delta in changes.items():
            old = as_int(self.settings_data["camera"].get(key))
            new_value = clamp(old + delta, -100, 100)
            self.settings_data["camera"][key] = new_value
            if key in self.camera_setting_vars:
                self.camera_setting_vars[key].set(new_value)
            if key in self.camera_value_vars:
                self.camera_value_vars[key].set(str(new_value))
        self.apply_camera_settings(save=True)
        self.redraw_camera_surface()
        self.auto_camera_job = self.after(260, self.auto_adjust_camera_settings)

    def populate_conveyor_settings(self, parent, var_bucket):
        parent.grid_columnconfigure(1, weight=1)
        tk.Label(
            parent,
            text="Default speed sent to Raspi when START SYSTEM runs.",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=18, pady=(16, 4))
        for row, key in enumerate(CONVEYOR_KEYS, start=1):
            value = self.settings_data["conveyor"].get(key, 0)
            tk.Label(parent, text=key.replace("_", " ").title(), bg=COLORS["panel"], fg=COLORS["ink"], font=("Segoe UI", 10)).grid(
                row=row, column=0, sticky="w", padx=18, pady=12
            )
            var = tk.IntVar(value=value)
            value_var = tk.StringVar(value=ConveyorRow.format_speed(value))
            scale = tk.Scale(
                parent,
                from_=0,
                to=20,
                orient="horizontal",
                variable=var,
                command=lambda val, item=key, target=value_var: self.update_conveyor_setting(item, val, target),
                bg=COLORS["panel"],
                troughcolor="#cfd8e3",
                highlightthickness=0,
                showvalue=False,
            )
            scale.grid(row=row, column=1, sticky="ew", padx=12, pady=8)
            tk.Label(parent, textvariable=value_var, bg=COLORS["panel"], fg=COLORS["steel"], width=9).grid(
                row=row, column=2, sticky="e", padx=(0, 8)
            )
            var_bucket[key] = var

    def update_conveyor_setting(self, key, value, label_var=None):
        numeric = clamp(as_int(value), 0, 20)
        self.settings_data.setdefault("conveyor", {})[key] = numeric
        if label_var is not None:
            label_var.set(ConveyorRow.format_speed(numeric))
        if key in self.conveyor_rows:
            self.conveyor_rows[key].value_var.set(numeric)
            self.conveyor_rows[key].text_var.set(ConveyorRow.format_speed(numeric))
        self.on_conveyor_change(key, numeric)

    def populate_range_settings(self, parent, var_bucket):
        for col in range(6):
            parent.grid_columnconfigure(col, weight=1)
        positions = BOX_KEYS + ["TRASH"]
        for index, key in enumerate(positions):
            row = index // 2
            base_col = (index % 2) * 3
            tk.Label(parent, text=key, bg=COLORS["panel"], fg=COLORS["ink"], font=("Segoe UI Semibold", 10)).grid(
                row=row, column=base_col, sticky="w", padx=(18, 4), pady=10
            )
            x_var = tk.StringVar(value=self.settings_data["range"].get(key, ["", ""])[0])
            y_var = tk.StringVar(value=self.settings_data["range"].get(key, ["", ""])[1])
            tk.Entry(parent, textvariable=x_var, width=8, relief="flat", highlightthickness=1, highlightbackground=COLORS["line"]).grid(
                row=row, column=base_col + 1, sticky="ew", padx=4, ipady=6
            )
            tk.Entry(parent, textvariable=y_var, width=8, relief="flat", highlightthickness=1, highlightbackground=COLORS["line"]).grid(
                row=row, column=base_col + 2, sticky="ew", padx=(4, 18), ipady=6
            )
            var_bucket[key] = (x_var, y_var)

    def populate_data_tools(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        tk.Label(
            parent,
            text="Data tools",
            bg=COLORS["panel"],
            fg=COLORS["ink"],
            font=("Segoe UI Semibold", 12),
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(18, 6))
        tk.Label(
            parent,
            text="Load JSON refreshes the dashboard from data.json. Export CSV saves the visible sorting log.",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
        ).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 14))

        actions = tk.Frame(parent, bg=COLORS["panel"])
        actions.grid(row=2, column=0, sticky="w", padx=18, pady=6)
        tk.Button(
            actions,
            text="LOAD DATA",
            command=self.refresh_all,
            bg=COLORS["teal"],
            fg=COLORS["white"],
            activebackground="#115e59",
            activeforeground=COLORS["white"],
            bd=0,
            padx=18,
            pady=10,
            font=("Segoe UI Semibold", 10),
        ).grid(row=0, column=0, padx=(0, 8))
        tk.Button(
            actions,
            text="EXPORT CSV",
            command=self.export_csv,
            bg=COLORS["cyan"],
            fg=COLORS["white"],
            activebackground="#0e7490",
            activeforeground=COLORS["white"],
            bd=0,
            padx=18,
            pady=10,
            font=("Segoe UI Semibold", 10),
        ).grid(row=0, column=1, padx=8)

        db_path = resolve_db_path(self.settings_data["database"].get("path"))
        tk.Label(
            parent,
            text=f"SQLite: {db_path.name}",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8),
        ).grid(row=3, column=0, sticky="w", padx=18, pady=(14, 0))

    def populate_database_settings(self, parent, var_bucket):
        self.db_settings_unlocked = False
        parent.grid_columnconfigure(1, weight=1)
        parent.grid_columnconfigure(2, weight=0)

        self.db_status_var = tk.StringVar(
            value="Locked. Admin PIN required." if has_admin_pin(self.settings_data) else "No admin PIN. Create one first."
        )
        tk.Label(parent, textvariable=self.db_status_var, bg=COLORS["panel"], fg=COLORS["red"], font=("Segoe UI Semibold", 10)).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=18, pady=(16, 8)
        )
        self.db_unlock_btn = tk.Button(
            parent,
            text="UNLOCK DB SETTINGS" if has_admin_pin(self.settings_data) else "SET ADMIN PIN",
            command=self.unlock_database_settings,
            bg=COLORS["steel"],
            fg=COLORS["white"],
            activebackground="#475569",
            activeforeground=COLORS["white"],
            bd=0,
            padx=12,
            pady=7,
        )
        self.db_unlock_btn.grid(row=0, column=2, sticky="e", padx=18, pady=(16, 8))

        tk.Label(parent, text="Database Type", bg=COLORS["panel"], fg=COLORS["ink"], font=("Segoe UI", 10)).grid(
            row=1, column=0, sticky="w", padx=18, pady=12
        )
        tk.Label(parent, text="SQLite local file", bg=COLORS["panel"], fg=COLORS["steel"], font=("Segoe UI Semibold", 10)).grid(
            row=1, column=1, sticky="w", padx=18, pady=12
        )

        tk.Label(parent, text="DB Path", bg=COLORS["panel"], fg=COLORS["ink"], font=("Segoe UI", 10)).grid(
            row=2, column=0, sticky="w", padx=18, pady=12
        )
        path_var = tk.StringVar(value=self.settings_data["database"].get("path", str(DEFAULT_DB_PATH)))
        self.db_path_var = path_var
        self.db_path_entry = tk.Entry(
            parent,
            textvariable=path_var,
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLORS["line"],
            state="disabled",
        )
        self.db_path_entry.grid(row=2, column=1, sticky="ew", padx=(18, 8), ipady=7)
        self.db_browse_btn = tk.Button(
            parent,
            text="Browse",
            command=lambda: self.pick_database_path(path_var),
            bg=COLORS["steel"],
            fg=COLORS["white"],
            activebackground="#475569",
            activeforeground=COLORS["white"],
            bd=0,
            padx=12,
            pady=7,
            state="disabled",
        )
        self.db_browse_btn.grid(row=2, column=2, sticky="e", padx=(0, 18))
        var_bucket["path"] = path_var

        tk.Label(
            parent,
            text="Tables: sorting_logs, operator_events, machine_commands, conveyor_state, machine_state.",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8),
        ).grid(row=3, column=0, columnspan=3, sticky="w", padx=18, pady=(4, 12))

    def pick_database_path(self, target_var):
        if not self.db_settings_unlocked:
            messagebox.showwarning("Access denied", "Unlock DB settings with admin PIN first.")
            return
        filename = filedialog.asksaveasfilename(
            title="SQLite database file",
            initialdir=str(APP_DIR),
            initialfile="sarva_monitor.db",
            defaultextension=".db",
            filetypes=[("SQLite database", "*.db"), ("All files", "*.*")],
        )
        if filename:
            target_var.set(filename)

    def unlock_database_settings(self):
        if not has_admin_pin(self.settings_data):
            self.create_admin_pin()
            return
        pin = simpledialog.askstring("Admin PIN", "Enter admin PIN", parent=self.settings_window, show="*")
        if pin is None:
            return
        if not verify_pin(self.settings_data, pin):
            self.store.insert_operator_event("DB settings unlock failed", {})
            messagebox.showerror("Access denied", "Wrong admin PIN.")
            return
        self.enable_database_controls()
        self.store.insert_operator_event("DB settings unlocked", {})

    def create_admin_pin(self):
        pin = simpledialog.askstring("Set Admin PIN", "Create admin PIN, minimum 6 characters", parent=self.settings_window, show="*")
        if pin is None:
            return
        if len(pin) < 6:
            messagebox.showerror("Invalid PIN", "Use at least 6 characters.")
            return
        confirm = simpledialog.askstring("Confirm Admin PIN", "Repeat admin PIN", parent=self.settings_window, show="*")
        if confirm != pin:
            messagebox.showerror("Invalid PIN", "PIN confirmation does not match.")
            return
        salt, digest = hash_pin(pin)
        self.settings_data.setdefault("security", {})["admin_pin_salt"] = salt
        self.settings_data["security"]["admin_pin_hash"] = digest
        self.settings_data["security"]["pin_iterations"] = SECURITY_ITERATIONS
        save_json(SETTINGS_PATH, self.settings_data)
        self.enable_database_controls()
        self.store.insert_operator_event("Admin PIN created", {})

    def enable_database_controls(self):
        self.db_settings_unlocked = True
        if self.db_status_var:
            self.db_status_var.set("Unlocked. DB path can be changed.")
        if self.db_path_entry:
            self.db_path_entry.configure(state="normal")
        if self.db_browse_btn:
            self.db_browse_btn.configure(state="normal")
        if self.db_unlock_btn:
            self.db_unlock_btn.configure(text="UNLOCKED", state="disabled", bg=COLORS["green"])

    def populate_raspi_settings(self, parent, var_bucket):
        parent.grid_columnconfigure(1, weight=1)
        enabled_var = tk.BooleanVar(value=self.settings_data["raspi"].get("enabled", True))
        tk.Checkbutton(
            parent,
            text="Enable command sending to Raspberry Pi over WiFi",
            variable=enabled_var,
            bg=COLORS["panel"],
            fg=COLORS["ink"],
            activebackground=COLORS["panel"],
            font=("Segoe UI", 10),
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=16, pady=12)
        var_bucket["enabled"] = enabled_var

        fields = [
            ("host", "Raspi IP / Host"),
            ("port", "TCP Port"),
            ("timeout", "Timeout (s)"),
        ]
        for index, (key, label) in enumerate(fields, start=1):
            tk.Label(parent, text=label, bg=COLORS["panel"], fg=COLORS["ink"], font=("Segoe UI", 10)).grid(
                row=index, column=0, sticky="w", padx=18, pady=12
            )
            var = tk.StringVar(value=self.settings_data["raspi"].get(key, ""))
            tk.Entry(
                parent,
                textvariable=var,
                relief="flat",
                highlightthickness=1,
                highlightbackground=COLORS["line"],
            ).grid(row=index, column=1, sticky="ew", padx=18, ipady=7)
            var_bucket[key] = var

        tk.Label(
            parent,
            text="Protocol: newline-free JSON over TCP. Raspi returns optional JSON ACK.",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8),
        ).grid(row=4, column=0, columnspan=3, sticky="w", padx=18, pady=(4, 12))

    def apply_settings(self, setting_vars):
        for key, var in setting_vars["camera"].items():
            self.settings_data["camera"][key] = bool(var.get()) if key == "auto" else int(var.get())
        self.apply_camera_settings(save=False)
        self.redraw_camera_surface()
        for key, var in setting_vars["conveyor"].items():
            self.settings_data["conveyor"][key] = int(var.get())
            if key in self.conveyor_rows:
                self.conveyor_rows[key].value_var.set(int(var.get()))
                self.conveyor_rows[key].text_var.set(ConveyorRow.format_speed(int(var.get())))
        for key, (x_var, y_var) in setting_vars["range"].items():
            self.settings_data["range"][key] = [x_var.get(), y_var.get()]
        if self.db_settings_unlocked:
            db_path_before = resolve_db_path(self.settings_data["database"].get("path"))
            self.settings_data["database"]["type"] = "sqlite"
            self.settings_data["database"]["path"] = setting_vars["database"]["path"].get()
            db_path_after = resolve_db_path(self.settings_data["database"].get("path"))
            if db_path_after != db_path_before:
                self.store.open(db_path_after)
        for key, var in setting_vars["raspi"].items():
            self.settings_data["raspi"][key] = bool(var.get()) if key == "enabled" else var.get()
        save_json(SETTINGS_PATH, self.settings_data)
        self.health_var.set(f"Settings saved | DB: {self.store.path.name}")
        self.close_settings()

    def close_settings(self):
        if hasattr(self, "settings_window") and self.settings_window:
            self.settings_window.destroy()
            self.settings_window = None

    def center_window(self, window):
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = self.winfo_rootx() + (self.winfo_width() - width) // 2
        y = self.winfo_rooty() + (self.winfo_height() - height) // 2
        window.geometry(f"{width}x{height}+{max(x, 0)}+{max(y, 0)}")

    @staticmethod
    def format_duration(seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def on_close(self):
        self.closing = True
        self.stop_camera()
        if self.timer_job:
            self.after_cancel(self.timer_job)
        if self.data_poll_job:
            self.after_cancel(self.data_poll_job)
        for job in list(self.conveyor_send_jobs.values()):
            self.after_cancel(job)
        self.store.close()
        self.destroy()


if __name__ == "__main__":
    app = SarvaDashboard()
    app.mainloop()
