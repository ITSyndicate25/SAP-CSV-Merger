#!/usr/bin/env python3
"""
SAP CSV Merger — Merge daily SAP CSV files from shared folder.

Usage: python sap_merge.py
Requirements: Python 3.10+ (tkinter included by default)
"""

import csv
import os
import re
import subprocess
import threading
import tkinter as tk
import tkinter.font as tkfont
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import TypedDict

from theme import Card, Colors, Theme, Typography, px, style_tree_rows

# ─── Constants ────────────────────────────────────────────────────────────────

SHARED_FOLDER_PATH = r"\\192.168.136.8\iSAP_log"
MAPPED_DRIVE = "Z:"
MAPPED_FOLDER = r"Z:\iSAP_IF"
FILE_PATTERN = re.compile(r"^(\d{8})_FYBPL004\.csv$", re.IGNORECASE)
DATE_FORMAT = "%Y%m%d"
DATE_DISPLAY_FORMAT = "%Y-%m-%d"
SYNTHETIC_HEADERS = [
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
    "AA",
    "AB",
    "AC",
    "AD",
    "AE",
    "AF",
]
DATE_COLUMN_INDEX = 12  # Column M (0-indexed)
APP_VERSION = "1.1.0"
DATE_PRESETS = (("Today", "today"), ("7 days", "week"), ("Month", "month"))


class UpdateInfo(TypedDict):
    """Shape of a release lookup result."""

    update_available: bool
    latest_version: str
    release_url: str
    release_notes: str


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _enable_dpi_awareness() -> None:
    """Let Windows draw at physical pixels; otherwise the window is bitmap-scaled.

    Tk already scales fonts by the reported DPI, so only the window needs the
    hint. Failures here cost sharpness, never the ability to start.
    """
    if os.name != "nt":
        return
    import ctypes

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        return
    except (AttributeError, OSError):
        # Windows 8.0 has no shcore: fall through to the legacy switch.
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            return


def _is_folder_open_in_explorer(folder_path: str) -> bool:
    """Return True if any Explorer window has *folder_path* open.

    Uses PowerShell COM (built into Windows); returns False on any failure
    so the disconnect is never permanently blocked.
    """
    try:
        ps_script = (
            "$shell = New-Object -ComObject Shell.Application; "
            "$found = $false; "
            "foreach ($w in $shell.Windows()) { "
            "  if ($w.Document -and $w.Document.Folder) { "
            "    $p = $w.Document.Folder.Self.Path; "
            f'    if ($p -like "*{folder_path}*") {{ $found = $true; break }} '
            "  } "
            "}; "
            "Write-Output $found"
        )
        result = subprocess.run(
            ["powershell.exe", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0 and "True" in result.stdout
    except Exception:
        return False


# ─── Network Drive Management ─────────────────────────────────────────────────


class NetworkDriveManager:
    """Manages network drive mapping for SAP shared folder."""

    def __init__(self):
        self.is_connected = False

    def connect(self) -> tuple[bool, str]:
        """Map network drive. Returns (success, message)."""
        try:
            # First disconnect if already connected
            self.disconnect()

            # Map the drive
            cmd = (
                f'net use {MAPPED_DRIVE} "{SHARED_FOLDER_PATH}"'
                " /user:iSAP_log_user SPX8TD7bWd /persistent:no"
            )
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                self.is_connected = True
                return True, f"Connected to {MAPPED_DRIVE}"
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                return False, f"Connection failed: {error_msg}"

        except Exception as e:
            return False, f"Error: {str(e)}"

    def disconnect(self) -> tuple[bool, str]:
        """Disconnect network drive. Returns (success, message)."""
        try:
            cmd = f"net use {MAPPED_DRIVE} /delete"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                self.is_connected = False
                return True, "Disconnected"

            error_msg = (result.stderr.strip() or result.stdout.strip()).lower()
            if any(
                phrase in error_msg
                for phrase in ("in use", "open files", "2401", "has open files")
            ):
                return (
                    False,
                    "Please close all open iSAP folders before disconnecting"
                    " the network drive.",
                )
            err = result.stderr.strip() or result.stdout.strip()
            return False, f"Disconnect failed: {err}"

        except Exception as e:
            return False, f"Error: {str(e)}"

    def check_connection(self) -> bool:
        """Check if mapped drive exists and is accessible."""
        return os.path.exists(MAPPED_FOLDER)


# ─── File Operations ──────────────────────────────────────────────────────────


class SAPFileHandler:
    """Handles SAP CSV file detection and operations across main and archive folders."""

    def __init__(self):
        self.files: dict[str, Path] = {}  # date_string -> file_path
        # date_string -> source folder name ("" for main)
        self.file_sources: dict[str, str] = {}
        self.archive_folders: list[str] = []  # list of YYYYMM folder names

    def scan_folder(self) -> tuple[bool, str, list[str]]:
        """Scan main folder and all monthly archive subfolders for SAP CSV files."""
        if not os.path.exists(MAPPED_FOLDER):
            return False, f"Folder not found: {MAPPED_FOLDER}", []

        self.files.clear()
        self.file_sources.clear()
        self.archive_folders.clear()
        found_dates = []

        try:
            for item in os.listdir(MAPPED_FOLDER):
                item_path = Path(MAPPED_FOLDER) / item
                if item_path.is_dir():
                    # Check if it's a monthly archive folder (6 digits, all numeric)
                    if item.isdigit() and len(item) == 6:
                        self.archive_folders.append(item)
                        # Scan archive folder
                        for archived_file in os.listdir(item_path):
                            match = FILE_PATTERN.match(archived_file)
                            if match:
                                date_str = match.group(1)
                                file_path = item_path / archived_file
                                if file_path.is_file():
                                    self.files[date_str] = file_path
                                    self.file_sources[date_str] = item
                                    found_dates.append(date_str)
                else:
                    # File in main folder
                    match = FILE_PATTERN.match(item)
                    if match:
                        date_str = match.group(1)
                        file_path = Path(MAPPED_FOLDER) / item
                        if file_path.is_file():
                            self.files[date_str] = file_path
                            self.file_sources[date_str] = ""
                            found_dates.append(date_str)

            found_dates.sort()
            total_archives = len(self.archive_folders)
            msg = f"Found {len(found_dates)} files ({total_archives} archive folders)"
            return True, msg, found_dates

        except Exception as e:
            return False, f"Scan error: {str(e)}", []

    def get_files_in_range(
        self, start_date: str, end_date: str
    ) -> list[tuple[str, Path, bool]]:
        """
        Get files within date range.
        Returns list of (date_str, file_path, exists) tuples.
        """
        try:
            start = datetime.strptime(start_date, DATE_DISPLAY_FORMAT)
            end = datetime.strptime(end_date, DATE_DISPLAY_FORMAT)
        except ValueError:
            return []

        result = []
        current = start

        while current <= end:
            date_str = current.strftime(DATE_FORMAT)
            exists = date_str in self.files
            file_path = self.files.get(
                date_str, Path(MAPPED_FOLDER) / f"{date_str}_FYBPL004.csv"
            )
            result.append((date_str, file_path, exists))
            current += timedelta(days=1)

        return result

    def validate_file_date(
        self, file_path: Path, expected_date: str
    ) -> tuple[bool, str]:
        """
        Validate that Column L in CSV matches expected date.
        Returns (valid, message).
        """
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                reader = csv.reader(f)
                # Skip header row, read first data row
                next(reader, None)
                data_row = next(reader, None)

                if data_row is None:
                    return False, "File has no data rows"

                if len(data_row) <= DATE_COLUMN_INDEX:
                    return False, f"Column L missing (only {len(data_row)} columns)"

                file_date = data_row[DATE_COLUMN_INDEX].strip()

                if file_date == expected_date:
                    return True, "Date matches"
                else:
                    return (
                        False,
                        f"Date mismatch: file has {file_date},"
                        f" expected {expected_date}",
                    )

        except Exception as e:
            return False, f"Read error: {str(e)}"

    def read_csv_preview(
        self, file_path: Path, max_rows: int = 10
    ) -> tuple[list[str], list[list[str]]]:
        """
        Read CSV for preview. Returns (headers, rows).
        """
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                reader = csv.reader(f)
                rows = []

                for i, row in enumerate(reader):
                    if i >= max_rows:
                        break
                    # Pad row to match synthetic headers length
                    padded_row = row + [""] * (len(SYNTHETIC_HEADERS) - len(row))
                    rows.append(padded_row[: len(SYNTHETIC_HEADERS)])

                return SYNTHETIC_HEADERS, rows

        except Exception as e:
            return SYNTHETIC_HEADERS, [[f"Error reading file: {str(e)}"]]

    def merge_files(self, file_paths: list[Path]) -> tuple[bool, str, list[list[str]]]:
        """
        Merge multiple CSV files in order.
        Returns (success, message, all_rows).
        """
        valid_paths = [p for p in file_paths if p is not None and p.exists()]
        if not valid_paths:
            return False, "No valid files available to merge.", []

        all_rows = []
        total_rows = 0
        errors = []

        for file_path in valid_paths:
            try:
                with open(file_path, encoding="utf-8", errors="ignore") as f:
                    reader = csv.reader(f)
                    file_rows = 0

                    for row in reader:
                        # Pad row to match synthetic headers length
                        padded_row = row + [""] * (len(SYNTHETIC_HEADERS) - len(row))
                        all_rows.append(padded_row[: len(SYNTHETIC_HEADERS)])
                        file_rows += 1

                    total_rows += file_rows

            except Exception as e:
                errors.append(f"{file_path.name}: {str(e)}")

        if errors:
            return False, f"Errors: {'; '.join(errors)}", all_rows

        return True, f"Merged {total_rows} rows from {len(valid_paths)} files", all_rows


# ─── Main Application ─────────────────────────────────────────────────────────


class SAPMergerApp:
    """Main window: command bar, resizable workspace, action bar, status strip.

    Layout is three panes the user resizes with the sashes:
    date and source cards | SAP files, stacked over the CSV preview.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("SAP CSV Merger")
        root.configure(bg=Colors.BACKGROUND)
        Theme.configure(root)

        # Core components
        self.network_manager = NetworkDriveManager()
        self.file_handler = SAPFileHandler()
        self.found_dates: list[str] = []
        self.selected_files: list[Path] = []
        self.merged_data: list[list[str]] | None = None
        self.tree_file_map: dict[str, Path] = {}  # tree iid -> file_path

        # Layout state
        self._sash_placed = False
        self._preview_expanded = False
        self._preview_saved_sash = 0
        self._fit_job: str | None = None
        self._mono_font = tkfont.Font(
            family=Typography.MONO_FAMILY, size=Typography.SIZE_SM
        )

        self._apply_window_geometry()
        self.create_widgets()
        self.update_connection_status()

        self.root.bind("<Configure>", self._on_window_configure, add="+")
        self.root.bind("<Destroy>", self._cancel_pending_fit, add="+")
        self.root.after(2000, self.check_for_updates)

    # ── Layout primitives ─────────────────────────────────────────────────────

    def _px(self, value: float) -> int:
        return px(self.root, value)

    def _apply_window_geometry(self):
        """Open large enough for real data, shrunk to fit smaller displays."""
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        width = min(self._px(1460), screen_w - self._px(60))
        height = min(self._px(980), screen_h - self._px(100))
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2 - self._px(20))
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(
            min(self._px(860), screen_w),
            min(self._px(600), screen_h),
        )

    def create_widgets(self):
        """Build the window in reading order: chrome, filters, workspace, status."""
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)

        self._build_menu()
        self._build_command_bar()
        self._build_filter_bar()
        self._build_workspace()
        self._build_status_strip()

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Expand preview", command=self.toggle_preview_size)
        view_menu.add_command(label="Reset layout", command=self.reset_layout)
        menubar.add_cascade(label="View", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Check for Updates", command=self.check_for_updates)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=menubar)

    def _build_command_bar(self):
        bar = tk.Frame(self.root, bg=Colors.CHROME)
        bar.grid(row=0, column=0, sticky="ew")
        bar.columnconfigure(1, weight=1)

        brand = tk.Frame(bar, bg=Colors.CHROME)
        brand.grid(
            row=0, column=0, sticky="w", padx=(self._px(20), 0), pady=self._px(10)
        )
        tk.Label(
            brand,
            text="SAP CSV Merger",
            bg=Colors.CHROME,
            fg=Colors.CHROME_TEXT,
            font=Typography.TITLE,
        ).pack(anchor="w")
        tk.Label(
            brand,
            text="iSAP_IF   ·   FYBPL004 daily files",
            bg=Colors.CHROME,
            fg=Colors.CHROME_MUTED,
            font=Typography.CAPTION,
        ).pack(anchor="w", pady=(self._px(2), 0))

        self.status_chip = tk.Frame(bar, bg=Colors.SURFACE)
        self.status_chip.grid(row=0, column=2, padx=(0, self._px(16)))
        self.status_dot = tk.Label(
            self.status_chip, text="●", font=Typography.CAPTION, bg=Colors.SURFACE
        )
        self.status_dot.pack(
            side="left", padx=(self._px(10), self._px(6)), pady=self._px(4)
        )
        self.status_label = tk.Label(
            self.status_chip,
            text="Disconnected",
            font=Typography.UI_BOLD,
            bg=Colors.SURFACE,
            fg=Colors.ERROR,
        )
        self.status_label.pack(side="left", padx=(0, self._px(10)))

        actions = tk.Frame(bar, bg=Colors.CHROME)
        actions.grid(row=0, column=3, sticky="e", padx=(0, self._px(20)))

        self.connect_btn = ttk.Button(
            actions,
            text="Connect",
            style="Primary.TButton",
            command=self.connect_drive,
        )
        self.connect_btn.pack(side="left", padx=(0, self._px(8)))

        self.disconnect_btn = ttk.Button(
            actions,
            text="Disconnect",
            style="ChromeOutline.TButton",
            command=self.disconnect_drive,
            state="disabled",
        )
        self.disconnect_btn.pack(side="left", padx=(0, self._px(8)))

        self.scan_btn = ttk.Button(
            actions,
            text="Scan folder",
            style="ChromeOutline.TButton",
            command=self.scan_folder,
        )
        self.scan_btn.pack(side="left")

    def _build_workspace(self):
        body = ttk.Frame(self.root, style="App.TFrame")
        body.grid(row=2, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)

        self.vsplit = ttk.PanedWindow(body, orient="vertical")
        self.vsplit.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=self._px(14),
            pady=(self._px(12), 0),
        )

        self.files_card = Card(self.vsplit, "SAP files")
        self.preview_card = Card(self.vsplit, "CSV preview")
        self.vsplit.add(self.files_card, weight=1)
        self.vsplit.add(self.preview_card, weight=1)

        # Tk 8.6 panes have weight only: keep both usable by clamping the sash.
        self._vsplit_min = (self._px(180), self._px(170))
        for sequence in ("<Configure>", "<ButtonRelease-1>"):
            self.vsplit.bind(
                sequence,
                lambda event: self._clamp_split(self.vsplit, self._vsplit_min),
                add="+",
            )

        self._build_files_card()
        self._build_preview_card()
        self._build_action_bar(body)

    def _build_filter_bar(self):
        """Date range, quick ranges and Detect live above the tables."""
        wrap = tk.Frame(self.root, bg=Colors.BORDER)
        wrap.grid(row=1, column=0, sticky="ew")
        bar = ttk.Frame(wrap, style="Card.TFrame")
        bar.pack(fill="x", pady=(0, 1))  # the wrap shows through as a hairline

        pad = self._px(9)
        now = datetime.now()
        self.start_year_var = tk.StringVar(value=str(now.year))
        self.start_month_var = tk.StringVar(value=f"{now.month:02d}")
        self.start_day_var = tk.StringVar(value=f"{now.day:02d}")
        self.end_year_var = tk.StringVar(value=str(now.year))
        self.end_month_var = tk.StringVar(value=f"{now.month:02d}")
        self.end_day_var = tk.StringVar(value=f"{now.day:02d}")

        self._date_group(
            bar, "From", self.start_year_var, self.start_month_var, self.start_day_var
        ).pack(side="left", padx=(self._px(16), 0), pady=pad)

        ttk.Label(bar, text="→", style="CardMeta.TLabel").pack(
            side="left", padx=self._px(6), pady=pad
        )

        self._date_group(
            bar, "To", self.end_year_var, self.end_month_var, self.end_day_var
        ).pack(side="left", pady=pad)

        ttk.Separator(bar, orient="vertical").pack(
            side="left", fill="y", padx=self._px(12), pady=self._px(8)
        )

        for label, preset in DATE_PRESETS:
            ttk.Button(
                bar,
                text=label,
                style="Segment.TButton",
                command=lambda name=preset: self.apply_date_preset(name),
            ).pack(side="left", padx=(0, self._px(6)), pady=pad)

        self.detect_btn = ttk.Button(
            bar,
            text="Detect files",
            style="Primary.TButton",
            command=self.detect_files,
        )
        self.detect_btn.pack(side="left", padx=(self._px(10), 0), pady=pad)

    def _date_group(self, parent: tk.Misc, label: str, year, month, day) -> ttk.Frame:
        group = ttk.Frame(parent, style="Card.TFrame")
        ttk.Label(group, text=label, style="FieldLabel.TLabel").pack(
            side="left", padx=(0, self._px(8))
        )
        now = datetime.now()
        fields = (
            (year, [str(y) for y in range(now.year - 10, now.year + 2)], 6),
            (month, [f"{m:02d}" for m in range(1, 13)], 4),
            (day, [f"{d:02d}" for d in range(1, 32)], 4),
        )
        for var, values, width in fields:
            ttk.Combobox(
                group,
                textvariable=var,
                values=values,
                width=width,
                state="readonly",
            ).pack(side="left", padx=(0, self._px(6)))
        return group

    def _build_files_card(self):
        card = self.files_card
        self.file_count_label = ttk.Label(
            card.actions, text="0 files", style="Pill.TLabel"
        )
        self.file_count_label.pack(side="right")

        body = card.body
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)

        table = ttk.Frame(body, style="Card.TFrame")
        table.grid(
            row=0, column=0, sticky="nsew", padx=self._px(12), pady=(0, self._px(10))
        )
        table.columnconfigure(0, weight=1)
        table.rowconfigure(0, weight=1)

        self.file_tree = ttk.Treeview(
            table,
            columns=("date", "folder"),
            show="tree headings",
            selectmode="extended",
        )
        self.file_tree.heading("#0", text="File", anchor="w")
        self.file_tree.heading("date", text="Date", anchor="w")
        self.file_tree.heading("folder", text="Folder", anchor="w")
        self.file_tree.column(
            "#0", width=self._px(240), minwidth=self._px(160), stretch=True
        )
        self.file_tree.column(
            "date",
            width=self._px(92),
            minwidth=self._px(80),
            anchor="w",
            stretch=False,
        )
        self.file_tree.column(
            "folder",
            width=self._px(120),
            minwidth=self._px(90),
            anchor="w",
            stretch=False,
        )
        self.file_tree.grid(row=0, column=0, sticky="nsew")

        yscroll = ttk.Scrollbar(table, orient="vertical", command=self.file_tree.yview)
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll = ttk.Scrollbar(
            table, orient="horizontal", command=self.file_tree.xview
        )
        xscroll.grid(row=1, column=0, sticky="ew")
        self.file_tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        style_tree_rows(self.file_tree)
        self.file_tree.tag_configure("folder", foreground=Colors.TEXT_SECONDARY)
        self.file_tree.bind("<<TreeviewSelect>>", self.on_file_select)

        self.files_hint = tk.Label(
            table,
            text="No files loaded — press Scan folder",
            bg=Colors.SURFACE,
            fg=Colors.TEXT_MUTED,
            font=Typography.UI,
        )
        self.files_hint.place(relx=0.5, rely=0.5, anchor="center")

    def _build_preview_card(self):
        card = self.preview_card
        self.preview_info_label = ttk.Label(
            card.header, text="No file selected", style="CardMeta.TLabel"
        )
        self.preview_info_label.pack(side="left", padx=(self._px(10), 0))

        self.expand_btn = ttk.Button(
            card.actions,
            text="Expand",
            style="Ghost.TButton",
            command=self.toggle_preview_size,
        )
        self.expand_btn.pack(side="right")

        self.fit_columns_var = tk.BooleanVar(value=True)
        self.fit_columns = ttk.Checkbutton(
            card.actions,
            text="Fit columns",
            variable=self.fit_columns_var,
            style="Tool.TCheckbutton",
            command=self._fit_preview_columns,
        )
        self.fit_columns.pack(side="right", padx=(0, self._px(8)))

        body = card.body
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)

        table = ttk.Frame(body, style="Card.TFrame")
        table.grid(
            row=0, column=0, sticky="nsew", padx=self._px(12), pady=(0, self._px(10))
        )
        table.columnconfigure(0, weight=1)
        table.rowconfigure(0, weight=1)

        self.preview_tree = ttk.Treeview(
            table, columns=SYNTHETIC_HEADERS, show="headings"
        )
        for header in SYNTHETIC_HEADERS:
            self.preview_tree.heading(header, text=header)
            self.preview_tree.column(
                header,
                width=self._px(92),
                minwidth=self._px(40),
                anchor="w",
                stretch=False,
            )
        self.preview_tree.grid(row=0, column=0, sticky="nsew")

        yscroll = ttk.Scrollbar(
            table, orient="vertical", command=self.preview_tree.yview
        )
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll = ttk.Scrollbar(
            table, orient="horizontal", command=self.preview_tree.xview
        )
        xscroll.grid(row=1, column=0, sticky="ew")
        self.preview_tree.configure(
            yscrollcommand=yscroll.set, xscrollcommand=xscroll.set
        )
        style_tree_rows(self.preview_tree)
        self.preview_tree.bind("<Configure>", self._schedule_fit)

        self.preview_hint = tk.Label(
            table,
            text="Select a file to preview its first 10 rows",
            bg=Colors.SURFACE,
            fg=Colors.TEXT_MUTED,
            font=Typography.UI,
        )
        self.preview_hint.place(relx=0.5, rely=0.5, anchor="center")

    def _build_action_bar(self, body: tk.Misc):
        footer = ttk.Frame(body, style="App.TFrame")
        footer.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=self._px(14),
            pady=(self._px(10), self._px(12)),
        )
        footer.columnconfigure(0, weight=1)

        self.merge_info_label = ttk.Label(footer, text="", style="Body.TLabel")
        self.merge_info_label.grid(row=0, column=0, sticky="w")

        buttons = ttk.Frame(footer, style="App.TFrame")
        buttons.grid(row=0, column=1, sticky="e")

        self.merge_btn = ttk.Button(
            buttons,
            text="Merge selected",
            style="Success.TButton",
            command=self.merge_files,
        )
        self.merge_btn.pack(side="left", padx=(0, self._px(8)))

        self.export_btn = ttk.Button(
            buttons,
            text="Export merged",
            style="Primary.TButton",
            command=self.export_file,
            state="disabled",
        )
        self.export_btn.pack(side="left", padx=(0, self._px(8)))

        self.clear_btn = ttk.Button(
            buttons,
            text="Clear all",
            style="DangerOutline.TButton",
            command=self.clear_all,
        )
        self.clear_btn.pack(side="left")

    def _build_status_strip(self):
        strip = tk.Frame(self.root, bg=Colors.SURFACE_VARIANT)
        strip.grid(row=3, column=0, sticky="ew")
        tk.Frame(strip, bg=Colors.BORDER, height=1).pack(fill="x")

        inner = tk.Frame(strip, bg=Colors.SURFACE_VARIANT)
        inner.pack(fill="x", padx=self._px(16), pady=self._px(5))

        self.status_bar = tk.Label(
            inner,
            text="Ready",
            bg=Colors.SURFACE_VARIANT,
            fg=Colors.TEXT_SECONDARY,
            font=Typography.CAPTION,
            anchor="w",
        )
        self.status_bar.pack(side="left")
        tk.Label(
            inner,
            text=f"v{APP_VERSION}",
            bg=Colors.SURFACE_VARIANT,
            fg=Colors.TEXT_MUTED,
            font=Typography.CAPTION,
        ).pack(side="right")

    # ── Pane sizing ───────────────────────────────────────────────────────────

    def _clamp_split(self, paned: ttk.PanedWindow, minimums: tuple[int, int]):
        """Keep both panes usable; ttk lets the sash sit anywhere."""
        total = (
            paned.winfo_height()
            if str(paned.cget("orient")) == "vertical"
            else paned.winfo_width()
        )
        if total <= 1:
            return
        first_min, second_min = minimums
        position = self._sash(paned, 0)
        clamped = max(first_min, min(position, total - second_min - self._px(10)))
        if clamped != position:
            self._set_sash(paned, 0, clamped)

    def _sash(self, paned: ttk.PanedWindow, index: int) -> int:
        try:
            return int(paned.tk.call(str(paned), "sashpos", index))
        except (tk.TclError, ValueError):
            return 0

    def _set_sash(self, paned: ttk.PanedWindow, index: int, position: int):
        paned.tk.call(str(paned), "sashpos", index, int(position))

    def _on_window_configure(self, event: tk.Event):
        """Place the sash once, after the panes have a real size."""
        if event.widget is not self.root:
            return
        if self._sash_placed or self.vsplit.winfo_height() < self._px(320):
            return
        self._sash_placed = True
        self.root.after_idle(self.reset_layout)

    def reset_layout(self):
        """Restore the default even split between files and preview."""
        self._set_sash(self.vsplit, 0, int(self.vsplit.winfo_height() * 0.5))
        self._preview_expanded = False
        self.expand_btn.configure(text="Expand")
        self._fit_preview_columns()

    def toggle_preview_size(self):
        """Give the preview every available pixel, or return to the split."""
        if self._preview_expanded:
            self._set_sash(self.vsplit, 0, self._preview_saved_sash)
            self._preview_expanded = False
            self.expand_btn.configure(text="Expand")
            return

        self._preview_saved_sash = self._sash(self.vsplit, 0)
        self._set_sash(self.vsplit, 0, self._vsplit_min[0])
        self._preview_expanded = True
        self.expand_btn.configure(text="Restore")

    def _cancel_pending_fit(self, event: tk.Event):
        """Drop a queued refit; a timer outliving the window is a Tcl error."""
        if event.widget is not self.root or self._fit_job is None:
            return
        self.root.after_cancel(self._fit_job)
        self._fit_job = None

    def _schedule_fit(self, event: tk.Event | None = None):
        """Refit columns after a resize settles, not on every pixel."""
        if event is not None and event.widget is not self.preview_tree:
            return
        if not self.fit_columns_var.get():
            return
        if self._fit_job is not None:
            self.root.after_cancel(self._fit_job)
        self._fit_job = self.root.after(90, self._fit_preview_columns)

    def _fit_preview_columns(self):
        """Size each column to its widest visible value, then share spare width."""
        self._fit_job = None
        tree = self.preview_tree
        if not self.fit_columns_var.get():
            for header in SYNTHETIC_HEADERS:
                tree.column(header, width=self._px(92))
            return

        available = tree.winfo_width()
        if available <= 1:
            return

        padding = self._px(22)
        rows = [tree.item(iid, "values") for iid in tree.get_children()[:12]]
        widths = []
        for index, header in enumerate(SYNTHETIC_HEADERS):
            width = self._mono_font.measure(header) + padding
            for values in rows:
                if index < len(values):
                    width = max(
                        width, self._mono_font.measure(str(values[index])) + padding
                    )
            widths.append(min(max(width, self._px(46)), self._px(260)))

        total = sum(widths)
        if total < available:
            extra = (available - total) // len(widths)
            widths = [width + extra for width in widths]

        for header, width in zip(SYNTHETIC_HEADERS, widths, strict=True):
            tree.column(header, width=width, minwidth=self._px(40))

    # ── Connection state ──────────────────────────────────────────────────────

    def _set_status_chip(self, state: str, text: str):
        palette = {
            "connected": (Colors.SUCCESS_LIGHT, Colors.SUCCESS),
            "connecting": (Colors.WARNING_LIGHT, Colors.WARNING),
            "disconnected": (Colors.ERROR_LIGHT, Colors.ERROR),
        }
        background, foreground = palette[state]
        for widget in (self.status_chip, self.status_dot, self.status_label):
            widget.configure(bg=background)
        self.status_dot.configure(fg=foreground)
        self.status_label.configure(text=text, fg=foreground)

    def update_connection_status(self):
        """Reflect whether the SAP share is reachable."""
        if self.network_manager.check_connection():
            self._set_status_chip("connected", "Connected")
            self.connect_btn.configure(state="disabled")
            self.disconnect_btn.configure(state="normal")
        else:
            self._set_status_chip("disconnected", "Disconnected")
            self.connect_btn.configure(state="normal")
            self.disconnect_btn.configure(state="disabled")

    def connect_drive(self):
        """Connect to network drive."""
        self.set_status("Connecting...")
        self.connect_btn.configure(state="disabled")
        self._set_status_chip("connecting", "Connecting...")

        success, message = self.network_manager.connect()
        self.update_connection_status()

        if success:
            self.set_status(message)
            self.scan_folder()
        else:
            self.set_status(message)
            messagebox.showerror("Connection Error", message)

    def disconnect_drive(self):
        """Disconnect network drive."""
        self.set_status("Disconnecting...")
        self.disconnect_btn.configure(state="disabled")

        # Proactive check: is the shared folder open in Explorer?
        if _is_folder_open_in_explorer(MAPPED_FOLDER):
            messagebox.showwarning(
                "Folder in Use",
                "Please close all open iSAP folders before disconnecting"
                " the network drive.",
            )
            self.disconnect_btn.configure(state="normal")
            self.set_status("Disconnect cancelled — folder in use")
            return

        success, message = self.network_manager.disconnect()
        self.update_connection_status()

        if not success:
            messagebox.showerror("Disconnect Error", message)

        self.set_status(message)
        self.clear_all()

    # ── File detection ────────────────────────────────────────────────────────

    def scan_folder(self):
        """Scan folder for SAP CSV files."""
        self.set_status("Scanning folder...")
        success, message, dates = self.file_handler.scan_folder()
        self.found_dates = dates

        if success:
            self.set_status(message)
            self.populate_file_tree()
            self.file_count_label.configure(text=f"{len(dates)} files")
        else:
            self.set_status(message)
            messagebox.showerror("Scan Error", message)

    def populate_file_tree(self):
        """Populate file treeview with detected files from main and archive folders."""
        self.files_hint.place_forget()
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        self.tree_file_map.clear()
        self.selected_files.clear()

        current_dates = [
            date_str
            for date_str in self.found_dates
            if self.file_handler.file_sources.get(date_str, "") == ""
        ]
        if current_dates:
            self.file_tree.insert(
                "",
                "end",
                iid="current_files",
                text=f"Current folder ({len(current_dates)})",
                open=True,
                tags=("folder",),
            )

        for folder in sorted(self.file_handler.archive_folders, reverse=True):
            count = sum(
                1
                for date_str in self.found_dates
                if self.file_handler.file_sources.get(date_str, "") == folder
            )
            if count == 0:
                continue
            self.file_tree.insert(
                "",
                "end",
                iid=f"folder_{folder}",
                text=f"Archive {folder} ({count})",
                open=False,
                tags=("folder",),
            )

        for index, date_str in enumerate(self.found_dates):
            display_date = datetime.strptime(date_str, DATE_FORMAT).strftime(
                DATE_DISPLAY_FORMAT
            )
            file_path = self.file_handler.files.get(date_str)
            source = self.file_handler.file_sources.get(date_str, "")
            source_display = "Main" if source == "" else source

            parent = "current_files" if source == "" else f"folder_{source}"
            iid = f"file_{date_str}"
            self.file_tree.insert(
                parent,
                "end",
                iid=iid,
                text=file_path.name,
                values=(display_date, source_display),
                tags=("odd",) if index % 2 else (),
            )
            self.tree_file_map[iid] = file_path

        if not self.found_dates:
            self.file_tree.insert(
                "",
                "end",
                iid="empty",
                text="No SAP files found in the scanned folder",
                tags=("folder",),
            )

        # Auto-select all files
        if self.tree_file_map:
            self.file_tree.selection_set(list(self.tree_file_map.keys()))
            self.selected_files = list(self.tree_file_map.values())

    def detect_files(self):
        """Detect files in selected date range and auto-select in treeview."""
        # Build date strings from dropdowns
        start_date = (
            f"{self.start_year_var.get()}"
            f"-{self.start_month_var.get()}"
            f"-{self.start_day_var.get()}"
        )
        end_date = (
            f"{self.end_year_var.get()}"
            f"-{self.end_month_var.get()}"
            f"-{self.end_day_var.get()}"
        )

        # Validate date format
        try:
            start_dt = datetime.strptime(start_date, DATE_DISPLAY_FORMAT)
            end_dt = datetime.strptime(end_date, DATE_DISPLAY_FORMAT)
        except ValueError:
            messagebox.showerror("Invalid Date", "Please select valid dates.")
            return

        # Validate range
        if start_dt > end_dt:
            messagebox.showerror("Invalid Range", "Start date must be before end date.")
            return

        # Get files in range
        files_in_range = self.file_handler.get_files_in_range(start_date, end_date)

        # Clear current selection
        self.file_tree.selection_remove(self.file_tree.selection())
        self.selected_files.clear()

        found_count = 0
        missing_count = 0
        select_iids = []

        for date_str, _file_path, exists in files_in_range:
            if exists:
                iid = f"file_{date_str}"
                if iid in self.tree_file_map:
                    select_iids.append(iid)
                    found_count += 1

                    # Expand parent folder
                    source = self.file_handler.file_sources.get(date_str, "")
                    parent_iid = "current_files" if source == "" else f"folder_{source}"
                    self.file_tree.item(parent_iid, open=True)
            else:
                missing_count += 1

        if select_iids:
            self.file_tree.selection_set(select_iids)
            # on_file_select handler will update self.selected_files

        total = len(files_in_range)
        self.file_count_label.configure(
            text=f"{found_count} of {total} found · {missing_count} missing"
        )
        self.set_status(f"Found {found_count} files in range ({missing_count} missing)")

    def on_file_select(self, event):
        """Handle file selection in treeview."""
        selection = self.file_tree.selection()
        if not selection:
            return

        # Filter to file nodes only (skip folder nodes)
        file_iids = [iid for iid in selection if iid.startswith("file_")]
        self.selected_files = [
            self.tree_file_map[iid] for iid in file_iids if iid in self.tree_file_map
        ]

        # Show preview for the first selected file
        if file_iids and file_iids[0] in self.tree_file_map:
            file_path = self.tree_file_map[file_iids[0]]
            if file_path.exists():
                self.show_preview(file_path)
            else:
                self.clear_preview()
                self.preview_info_label.configure(
                    text=f"{file_path.name} · not available", style="CardWarning.TLabel"
                )
        else:
            self.clear_preview()

    def show_preview(self, file_path: Path):
        """Show CSV preview in treeview."""
        self.clear_preview()

        # Validate date
        date_str = file_path.stem[:8]  # Extract date from filename
        valid, message = self.file_handler.validate_file_date(file_path, date_str)

        # Read preview
        headers, rows = self.file_handler.read_csv_preview(file_path)

        # Insert rows into treeview
        for index, row in enumerate(rows):
            self.preview_tree.insert(
                "", "end", values=row, tags=("odd",) if index % 2 else ()
            )

        if valid:
            self.preview_info_label.configure(
                text=f"{file_path.name} · {len(rows)} rows shown",
                style="CardMeta.TLabel",
            )
        else:
            self.preview_info_label.configure(
                text=f"{file_path.name} · {message}", style="CardWarning.TLabel"
            )
        self.preview_hint.place_forget()
        self._fit_preview_columns()

    def clear_preview(self):
        """Clear preview treeview."""
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        self.preview_info_label.configure(
            text="No file selected", style="CardMeta.TLabel"
        )
        self.preview_hint.place(relx=0.5, rely=0.5, anchor="center")

    # ── Merge and export ──────────────────────────────────────────────────────

    def merge_files(self):
        """Merge selected files."""
        if not self.selected_files:
            messagebox.showwarning("No Files", "No files selected for merging.")
            return

        self.set_status("Merging files...")
        self.merge_btn.configure(state="disabled")

        success, message, merged_data = self.file_handler.merge_files(
            self.selected_files
        )

        if success:
            self.merged_data = merged_data
            self.export_btn.configure(state="normal")
            self.merge_info_label.configure(text=message, style="Success.TLabel")
            self.set_status(message)
            messagebox.showinfo("Merge Complete", message)
        else:
            self.set_status(message)
            messagebox.showerror("Merge Error", message)

        self.merge_btn.configure(state="normal")

    def export_file(self):
        """Export merged data to file."""
        if self.merged_data is None:
            messagebox.showwarning("No Data", "No merged data to export.")
            return

        # Ask for save location
        file_path = filedialog.asksaveasfilename(
            title="Export Merged CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"merged_sap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(SYNTHETIC_HEADERS)  # Write synthetic headers
                writer.writerows(self.merged_data)

            self.set_status(f"Exported to: {file_path}")
            messagebox.showinfo("Export Complete", f"File saved to:\n{file_path}")

        except Exception as e:
            error_msg = f"Export error: {str(e)}"
            self.set_status(error_msg)
            messagebox.showerror("Export Error", error_msg)

    # ── Dates, clearing, status ───────────────────────────────────────────────

    @staticmethod
    def _set_date_fields(year, month, day, value: datetime):
        year.set(str(value.year))
        month.set(f"{value.month:02d}")
        day.set(f"{value.day:02d}")

    def apply_date_preset(self, preset: str):
        """Fill both date fields from a common range in one click."""
        today = datetime.now()
        if preset == "week":
            start = today - timedelta(days=6)
        elif preset == "month":
            start = today.replace(day=1)
        else:
            start = today

        for prefix, value in (("start", start), ("end", today)):
            self._set_date_fields(
                getattr(self, f"{prefix}_year_var"),
                getattr(self, f"{prefix}_month_var"),
                getattr(self, f"{prefix}_day_var"),
                value,
            )
        self.set_status(f"Range set to {start:%Y-%m-%d} → {today:%Y-%m-%d}")

    def clear_dates(self):
        """Reset the range to today."""
        now = datetime.now()
        self._set_date_fields(
            self.start_year_var, self.start_month_var, self.start_day_var, now
        )
        self._set_date_fields(
            self.end_year_var, self.end_month_var, self.end_day_var, now
        )
        self.set_status("Dates reset to today")

    def clear_all(self):
        """Clear all selections and preview."""
        self.file_tree.selection_remove(self.file_tree.selection())
        self.clear_preview()
        self.selected_files.clear()
        self.merged_data = None
        self.export_btn.configure(state="disabled")
        self.merge_info_label.configure(text="")
        self.file_count_label.configure(text="0 files")
        self.set_status("Cleared")

    def set_status(self, message: str):
        """Update status bar."""
        self.status_bar.configure(text=message)

    # ── Updates and dialogs ───────────────────────────────────────────────────

    def check_for_updates(self, silent: bool = False):
        """Check GitHub for updates. silent=True = no dialog if already current."""

        def _check():
            checker = UpdateChecker(APP_VERSION)
            result, error = checker.check()
            self.root.after(0, self._handle_update_result, result, error, silent)

        threading.Thread(target=_check, daemon=True).start()

    def _handle_update_result(
        self, result: UpdateInfo | None, error: str | None, silent: bool
    ):
        if result is None:
            if not silent:
                if error and "Private repository" in error:
                    self._show_private_repo_dialog()
                else:
                    msg = "Could not check for updates."
                    if error:
                        msg += f"\n\nError: {error}"
                    messagebox.showinfo("Update Check", msg)
            return
        if result["update_available"]:
            self._show_update_dialog(result)
        elif not silent:
            messagebox.showinfo(
                "Up to Date", f"You're running the latest version ({APP_VERSION})."
            )

    def _show_private_repo_dialog(self):
        """Show dialog for private repo — let user open releases page manually."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Update Check")
        dialog.geometry("480x200")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Update Check",
            font=Typography.CARD_TITLE,
        ).pack(pady=(0, 10))

        ttk.Label(
            frame,
            text="This repository is private. GitHub requires you to be\n"
            "signed in to check for updates.\n\n"
            "Open the releases page in your browser to see available versions.",
            justify=tk.LEFT,
        ).pack(pady=(0, 15))

        btn_frame = ttk.Frame(frame)
        btn_frame.pack()

        ttk.Button(
            btn_frame,
            text="Open Releases Page",
            command=lambda: (
                webbrowser.open(UpdateChecker.GITHUB_RELEASES_PAGE),
                dialog.destroy(),
            ),
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="OK", command=dialog.destroy).pack(
            side=tk.LEFT, padx=5
        )

    def _show_update_dialog(self, info: UpdateInfo):
        """Show a custom update-available dialog with download button."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Update Available")
        dialog.geometry("480x280")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # UI
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame, text="A new version is available!", font=Typography.CARD_TITLE
        ).pack(pady=(0, 10))

        versions_frame = ttk.Frame(frame)
        versions_frame.pack(fill=tk.X, pady=5)
        ttk.Label(versions_frame, text=f"Current: {APP_VERSION}").pack(side=tk.LEFT)
        ttk.Label(versions_frame, text=f"Latest: {info['latest_version']}").pack(
            side=tk.RIGHT
        )

        if info["release_notes"]:
            notes_text = tk.Text(frame, height=6, width=50, wrap=tk.WORD)
            notes_text.configure(state=tk.DISABLED)
            notes_text.pack(pady=10)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)

        def open_download():
            webbrowser.open(info["release_url"])
            dialog.destroy()

        ttk.Button(btn_frame, text="Download", command=open_download).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(btn_frame, text="Later", command=dialog.destroy).pack(
            side=tk.LEFT, padx=5
        )

    def show_about(self):
        messagebox.showinfo(
            "About SAP CSV Merger",
            f"SAP CSV Merger v{APP_VERSION}\n\n"
            "Merge daily SAP CSV files from shared folder.\n\n"
            "© ITSyndicate25",
        )


# ─── Update Check ─────────────────────────────────────────────────────────────


class UpdateChecker:
    """Checks GitHub for newer releases and reports availability."""

    GITHUB_RELEASES_PAGE = "https://github.com/ITSyndicate25/SAP-CSV-Merger/releases"

    def __init__(self, current_version: str):
        self.current_version = current_version

    def check(self) -> tuple[UpdateInfo | None, str | None]:
        """Check GitHub releases using the releases/latest redirect.

        GET /releases/latest follows the redirect to the actual release page.
        For private repos this returns 404, which we detect and guide the user.

        Returns:
            Tuple of (result_dict, error_message). result_dict is None on failure.
        """
        import re
        import ssl
        import urllib.error
        import urllib.request

        try:
            # Handle SSL certificates in PyInstaller bundles
            ssl_context = ssl.create_default_context()
            try:
                import certifi
            except ImportError:
                certifi = None  # No CA bundle bundled: use the system store.
            if certifi is not None:
                ssl_context.load_verify_locations(certifi.where())

            # Fetch /releases/latest — follows redirect to actual release page
            url = f"{self.GITHUB_RELEASES_PAGE}/latest"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; SAPCSVMerger/1.0)"},
            )
            with urllib.request.urlopen(
                req, timeout=10, context=ssl_context
            ) as response:
                # After following redirects, geturl() gives the final destination
                final_url = response.geturl()

            # Extract tag from the final URL: .../releases/tag/vX.Y.Z
            match = re.search(r"/tag/v(\d+\.\d+\.\d+)", final_url)
            if match:
                latest_version = match.group(1)
                current = tuple(int(x) for x in self.current_version.split("."))
                latest = tuple(int(x) for x in latest_version.split("."))
                return (
                    UpdateInfo(
                        update_available=latest > current,
                        latest_version=latest_version,
                        release_url=final_url,
                        release_notes="",
                    ),
                    None,
                )

            return (None, "Could not determine latest version from GitHub.")

        except urllib.error.HTTPError as e:
            if e.code == 404:
                return (None, "Private repository — open the page in your browser.")
            return (None, f"HTTP Error {e.code}: {e.reason}")
        except Exception as e:
            return (None, str(e))


def main():
    """Main entry point."""
    _enable_dpi_awareness()
    root = tk.Tk()
    SAPMergerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
