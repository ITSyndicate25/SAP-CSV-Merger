#!/usr/bin/env python3
"""
SAP CSV Merger — Merge daily SAP CSV files from shared folder.

Usage: python sap_merge.py
Requirements: Python 3.6+ (tkinter included by default)
"""

import os
import re
import csv
import subprocess
import threading
import tkinter as tk
import webbrowser
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple, Optional, Dict

# Import theme
from theme import Colors, Typography, Spacing, Theme


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
APP_VERSION = "1.0.9"


# ─── Network Drive Management ─────────────────────────────────────────────────


class NetworkDriveManager:
    """Manages network drive mapping for SAP shared folder."""

    def __init__(self):
        self.is_connected = False

    def connect(self) -> Tuple[bool, str]:
        """Map network drive. Returns (success, message)."""
        try:
            # First disconnect if already connected
            self.disconnect()

            # Map the drive
            cmd = f'net use {MAPPED_DRIVE} "{SHARED_FOLDER_PATH}" /user:iSAP_log_user SPX8TD7bWd /persistent:no'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                self.is_connected = True
                return True, f"Connected to {MAPPED_DRIVE}"
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                return False, f"Connection failed: {error_msg}"

        except Exception as e:
            return False, f"Error: {str(e)}"

    def disconnect(self) -> Tuple[bool, str]:
        """Disconnect network drive. Returns (success, message)."""
        try:
            cmd = f"net use {MAPPED_DRIVE} /delete"
            subprocess.run(cmd, shell=True, capture_output=True, text=True)
            self.is_connected = False
            return True, "Disconnected"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def check_connection(self) -> bool:
        """Check if mapped drive exists and is accessible."""
        return os.path.exists(MAPPED_FOLDER)


# ─── File Operations ──────────────────────────────────────────────────────────


class SAPFileHandler:
    """Handles SAP CSV file detection and operations."""

    def __init__(self):
        self.files: Dict[str, Path] = {}  # date_string -> file_path

    def scan_folder(self) -> Tuple[bool, str, List[str]]:
        """Scan folder for SAP CSV files. Returns (success, message, file_dates)."""
        if not os.path.exists(MAPPED_FOLDER):
            return False, f"Folder not found: {MAPPED_FOLDER}", []

        self.files.clear()
        found_dates = []

        try:
            for item in os.listdir(MAPPED_FOLDER):
                match = FILE_PATTERN.match(item)
                if match:
                    date_str = match.group(1)
                    file_path = Path(MAPPED_FOLDER) / item
                    if file_path.is_file():
                        self.files[date_str] = file_path
                        found_dates.append(date_str)

            found_dates.sort()
            return True, f"Found {len(found_dates)} files", found_dates

        except Exception as e:
            return False, f"Scan error: {str(e)}", []

    def get_files_in_range(
        self, start_date: str, end_date: str
    ) -> List[Tuple[str, Path, bool]]:
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
    ) -> Tuple[bool, str]:
        """
        Validate that Column L in CSV matches expected date.
        Returns (valid, message).
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
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
                        f"Date mismatch: file has {file_date}, expected {expected_date}",
                    )

        except Exception as e:
            return False, f"Read error: {str(e)}"

    def read_csv_preview(
        self, file_path: Path, max_rows: int = 10
    ) -> Tuple[List[str], List[List[str]]]:
        """
        Read CSV for preview. Returns (headers, rows).
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
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

    def merge_files(self, file_paths: List[Path]) -> Tuple[bool, str, List[List[str]]]:
        """
        Merge multiple CSV files in order.
        Returns (success, message, all_rows).
        """
        all_rows = []
        total_rows = 0
        errors = []

        for file_path in file_paths:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
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

        return True, f"Merged {total_rows} rows from {len(file_paths)} files", all_rows


# ─── Main Application ─────────────────────────────────────────────────────────


class SAPMergerApp:
    """Main GUI application for SAP CSV merging."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("SAP CSV Merger")
        self.root.geometry("950x680")
        self.root.minsize(800, 550)

        # Configure background
        self.root.configure(bg=Colors.BACKGROUND)

        # Apply theme
        Theme.configure(root)

        # Core components
        self.network_manager = NetworkDriveManager()
        self.file_handler = SAPFileHandler()
        self.found_dates: List[str] = []
        self.selected_files: List[Path] = []
        self.merged_data: Optional[List[List[str]]] = None

        # Setup UI
        self.create_widgets()
        self.update_connection_status()

        # Check for updates after UI renders
        self.root.after(2000, self.check_for_updates)

    def create_widgets(self):
        """Create all GUI widgets with modern styling."""
        # Menu bar
        menubar = tk.Menu(self.root)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Check for Updates", command=self.check_for_updates)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=menubar)

        # Main container with padding
        main_frame = ttk.Frame(self.root, padding=(Spacing.LG, Spacing.SM))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)  # csv preview — stretches
        main_frame.grid(row=0, column=0, sticky="nsew")

        # ── Title Section ──
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, Spacing.SM))

        title_label = ttk.Label(
            title_frame, text="SAP CSV Merger", style="Title.TLabel"
        )
        title_label.grid(row=0, column=0, sticky="w")

        subtitle_label = ttk.Label(
            title_frame,
            text="Merge daily SAP CSV files from shared folder",
            style="Caption.TLabel",
        )
        subtitle_label.grid(row=1, column=0, sticky="w", pady=(Spacing.XXS, 0))

        # ── Network Connection Card ──
        net_card = ttk.Frame(main_frame, style="Card.TFrame")
        net_card.grid(row=1, column=0, sticky="ew", pady=(0, Spacing.SM))

        net_header = ttk.Label(
            net_card, text="Network Connection", style="Subheader.TLabel"
        )
        net_header.grid(
            row=0,
            column=0,
            columnspan=3,
            sticky="w",
            padx=Spacing.LG,
            pady=(Spacing.SM, Spacing.XS),
        )

        # Separator
        ttk.Separator(net_card, orient="horizontal").grid(
            row=1, column=0, columnspan=3, sticky="ew", padx=Spacing.LG
        )

        # Connection controls
        net_content = ttk.Frame(net_card, style="Card.TFrame")
        net_content.grid(
            row=2,
            column=0,
            columnspan=3,
            sticky="ew",
            padx=Spacing.LG,
            pady=(Spacing.SM, Spacing.SM),
        )

        # Status indicator
        self.status_indicator = tk.Canvas(
            net_content,
            width=12,
            height=12,
            highlightthickness=0,
            bg=Colors.DISCONNECTED,
        )
        self.status_indicator.grid(row=0, column=0, padx=(0, Spacing.SM))

        self.status_label = ttk.Label(
            net_content, text="Disconnected", style="Label.TLabel"
        )
        self.status_label.grid(row=0, column=1, padx=(0, Spacing.XL))

        # Action buttons
        btn_frame = ttk.Frame(net_content, style="Card.TFrame")
        btn_frame.grid(row=0, column=2, sticky="e")

        self.connect_btn = ttk.Button(
            btn_frame,
            text="Connect",
            style="Primary.TButton",
            command=self.connect_drive,
        )
        self.connect_btn.grid(row=0, column=0, padx=(0, Spacing.SM))

        self.disconnect_btn = ttk.Button(
            btn_frame,
            text="Disconnect",
            style="Danger.TButton",
            command=self.disconnect_drive,
            state="disabled",
        )
        self.disconnect_btn.grid(row=0, column=1, padx=(0, Spacing.SM))

        self.scan_btn = ttk.Button(
            btn_frame,
            text="Scan Folder",
            style="Secondary.TButton",
            command=self.scan_folder,
        )
        self.scan_btn.grid(row=0, column=2)

        # ── Mid Section: Date Range + Available Files (two-column) ──
        mid_row = ttk.Frame(main_frame)
        mid_row.grid(row=2, column=0, sticky="ew", pady=(0, Spacing.SM))
        mid_row.columnconfigure(0, weight=1)
        mid_row.columnconfigure(1, weight=1)

        # ═══ Date Range Card (left column) ═══
        date_card = ttk.Frame(mid_row, style="Card.TFrame")
        date_card.grid(row=0, column=0, sticky="ew", padx=(0, Spacing.SM))
        # Card header
        date_header = ttk.Label(date_card, text="Date Range", style="Subheader.TLabel")
        date_header.grid(
            row=0,
            column=0,
            columnspan=5,
            sticky="w",
            padx=Spacing.LG,
            pady=(Spacing.SM, Spacing.XS),
        )
        # Separator
        ttk.Separator(date_card, orient="horizontal").grid(
            row=1, column=0, columnspan=5, sticky="ew", padx=Spacing.LG
        )

        date_content = ttk.Frame(date_card, style="Card.TFrame")
        date_content.grid(
            row=2,
            column=0,
            columnspan=5,
            sticky="ew",
            padx=Spacing.LG,
            pady=(Spacing.SM, Spacing.XS),
        )

        # Current date for defaults
        now = datetime.now()

        # From date
        from_frame = ttk.Frame(date_content, style="Card.TFrame")
        from_frame.grid(row=0, column=0, sticky="w")

        ttk.Label(from_frame, text="From", style="Label.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w"
        )

        # Year dropdown
        self.start_year_var = tk.StringVar(value=str(now.year))
        self.start_year_cb = ttk.Combobox(
            from_frame,
            textvariable=self.start_year_var,
            values=[str(y) for y in range(2020, 2030)],
            width=6,
            state="readonly",
        )
        self.start_year_cb.grid(row=1, column=0, padx=(0, Spacing.XS))

        # Month dropdown
        self.start_month_var = tk.StringVar(value=f"{now.month:02d}")
        self.start_month_cb = ttk.Combobox(
            from_frame,
            textvariable=self.start_month_var,
            values=[f"{m:02d}" for m in range(1, 13)],
            width=4,
            state="readonly",
        )
        self.start_month_cb.grid(row=1, column=1, padx=(0, Spacing.XS))

        # Day dropdown
        self.start_day_var = tk.StringVar(value=f"{now.day:02d}")
        self.start_day_cb = ttk.Combobox(
            from_frame,
            textvariable=self.start_day_var,
            values=[f"{d:02d}" for d in range(1, 32)],
            width=4,
            state="readonly",
        )
        self.start_day_cb.grid(row=1, column=2)

        ttk.Label(from_frame, text="YYYY  MM  DD", style="LabelSm.TLabel").grid(
            row=2, column=0, columnspan=3, sticky="w"
        )

        # Arrow separator
        ttk.Label(date_content, text="→", style="Header.TLabel").grid(
            row=0, column=1, padx=Spacing.XL
        )

        # To date
        to_frame = ttk.Frame(date_content, style="Card.TFrame")
        to_frame.grid(row=0, column=2, sticky="w")

        ttk.Label(to_frame, text="To", style="Label.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w"
        )

        # Year dropdown
        self.end_year_var = tk.StringVar(value=str(now.year))
        self.end_year_cb = ttk.Combobox(
            to_frame,
            textvariable=self.end_year_var,
            values=[str(y) for y in range(2020, 2030)],
            width=6,
            state="readonly",
        )
        self.end_year_cb.grid(row=1, column=0, padx=(0, Spacing.XS))

        # Month dropdown
        self.end_month_var = tk.StringVar(value=f"{now.month:02d}")
        self.end_month_cb = ttk.Combobox(
            to_frame,
            textvariable=self.end_month_var,
            values=[f"{m:02d}" for m in range(1, 13)],
            width=4,
            state="readonly",
        )
        self.end_month_cb.grid(row=1, column=1, padx=(0, Spacing.XS))

        # Day dropdown
        self.end_day_var = tk.StringVar(value=f"{now.day:02d}")
        self.end_day_cb = ttk.Combobox(
            to_frame,
            textvariable=self.end_day_var,
            values=[f"{d:02d}" for d in range(1, 32)],
            width=4,
            state="readonly",
        )
        self.end_day_cb.grid(row=1, column=2)

        ttk.Label(to_frame, text="YYYY  MM  DD", style="LabelSm.TLabel").grid(
            row=2, column=0, columnspan=3, sticky="w"
        )

        # Detect and Clear buttons
        detect_frame = ttk.Frame(date_content)
        detect_frame.grid(row=0, column=3, padx=(Spacing.XL, 0))

        self.detect_btn = ttk.Button(
            detect_frame,
            text="Detect Files",
            style="Primary.TButton",
            command=self.detect_files,
        )
        self.detect_btn.grid(row=0, column=0, padx=(0, Spacing.SM))

        self.clear_date_btn = ttk.Button(
            detect_frame,
            text="Clear Dates",
            style="Secondary.TButton",
            command=self.clear_dates,
        )
        self.clear_date_btn.grid(row=0, column=1)

        # ═══ Available Files Card (right column) ═══
        file_card = ttk.Frame(mid_row, style="Card.TFrame")
        file_card.grid(row=0, column=1, sticky="ew", padx=(Spacing.SM, 0))
        file_card.columnconfigure(0, weight=1)

        # Card header
        file_header = ttk.Label(
            file_card, text="Available Files", style="CardHeader.TLabel"
        )
        file_header.grid(
            row=0, column=0, sticky="w", padx=Spacing.MD, pady=(Spacing.MD, Spacing.XS)
        )

        # Separator
        ttk.Separator(file_card, orient="horizontal").grid(
            row=1, column=0, sticky="ew", padx=Spacing.LG
        )

        # File listbox with scrollbar
        list_container = ttk.Frame(file_card)
        list_container.grid(
            row=2, column=0, sticky="ew", padx=Spacing.MD, pady=Spacing.SM
        )
        list_container.columnconfigure(0, weight=1)

        self.file_listbox = tk.Listbox(
            list_container,
            font=Typography.BODY_SM,
            selectmode=tk.EXTENDED,
            bg=Colors.SURFACE,
            fg=Colors.TEXT_PRIMARY,
            selectbackground=Colors.PRIMARY_LIGHT,
            selectforeground=Colors.PRIMARY,
            highlightthickness=0,
            borderwidth=0,
            relief="flat",
            height=4,
        )
        self.file_listbox.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            list_container, orient="vertical", command=self.file_listbox.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.file_listbox.configure(yscrollcommand=scrollbar.set)

        self.file_listbox.bind("<<ListboxSelect>>", self.on_file_select)

        # File count label
        self.file_count_label = ttk.Label(
            file_card, text="0 files", style="Caption.TLabel"
        )
        self.file_count_label.grid(
            row=3, column=0, sticky="w", padx=Spacing.MD, pady=(Spacing.XS, Spacing.SM)
        )

        # ── CSV Preview Section (full-width below) ──
        preview_card = ttk.Frame(main_frame, style="Card.TFrame")
        preview_card.grid(row=3, column=0, sticky="nsew", pady=(0, Spacing.SM))
        preview_card.columnconfigure(0, weight=1)
        preview_card.rowconfigure(2, weight=1)

        # Card header
        preview_header = ttk.Label(
            preview_card, text="CSV Preview", style="CardHeader.TLabel"
        )
        preview_header.grid(
            row=0, column=0, sticky="w", padx=Spacing.MD, pady=(Spacing.MD, Spacing.SM)
        )

        # Separator
        ttk.Separator(preview_card, orient="horizontal").grid(
            row=1, column=0, sticky="ew", padx=Spacing.LG
        )

        # Treeview for preview
        tree_container = ttk.Frame(preview_card)
        tree_container.grid(
            row=2, column=0, sticky="nsew", padx=Spacing.MD, pady=Spacing.MD
        )
        tree_container.columnconfigure(0, weight=1)
        tree_container.rowconfigure(0, weight=1)

        self.preview_tree = ttk.Treeview(
            tree_container, columns=SYNTHETIC_HEADERS, show="headings", height=6
        )

        for header in SYNTHETIC_HEADERS:
            self.preview_tree.heading(header, text=header)
            self.preview_tree.column(header, width=70, minwidth=50)

        self.preview_tree.grid(row=0, column=0, sticky="nsew")

        tree_scrollbar_y = ttk.Scrollbar(
            tree_container, orient="vertical", command=self.preview_tree.yview
        )
        tree_scrollbar_y.grid(row=0, column=1, sticky="ns")
        self.preview_tree.configure(yscrollcommand=tree_scrollbar_y.set)

        tree_scrollbar_x = ttk.Scrollbar(
            tree_container, orient="horizontal", command=self.preview_tree.xview
        )
        tree_scrollbar_x.grid(row=1, column=0, sticky="ew")

        # Preview info label
        self.preview_info_label = ttk.Label(
            preview_card, text="Select a file to preview", style="Caption.TLabel"
        )
        self.preview_info_label.grid(
            row=3, column=0, sticky="w", padx=Spacing.MD, pady=(Spacing.XS, Spacing.SM)
        )

        # ── Action Buttons Section ──
        action_frame = ttk.Frame(main_frame, style="Surface.TFrame")
        action_frame.grid(row=4, column=0, sticky="ew", pady=(Spacing.MD, 0))

        # Left side - merge info
        self.merge_info_label = ttk.Label(action_frame, text="", style="Body.TLabel")
        self.merge_info_label.grid(row=0, column=0, sticky="w")

        # Right side - action buttons
        btn_container = ttk.Frame(action_frame)
        btn_container.grid(row=0, column=1, sticky="e")

        self.merge_btn = ttk.Button(
            btn_container,
            text="Merge Selected Files",
            style="Success.TButton",
            command=self.merge_files,
        )
        self.merge_btn.grid(row=0, column=0, padx=(0, Spacing.SM))

        self.export_btn = ttk.Button(
            btn_container,
            text="Export Merged File",
            style="Primary.TButton",
            command=self.export_file,
            state="disabled",
        )
        self.export_btn.grid(row=0, column=1, padx=(0, Spacing.SM))

        self.clear_btn = ttk.Button(
            btn_container,
            text="Clear All",
            style="Secondary.TButton",
            command=self.clear_all,
        )
        self.clear_btn.grid(row=0, column=2)
        # ── Status Bar ──
        status_frame = ttk.Frame(main_frame, style="Card.TFrame")
        status_frame.grid(row=5, column=0, sticky="ew", pady=(Spacing.MD, 0))

        self.status_bar = ttk.Label(status_frame, text="Ready", style="Status.TLabel")
        self.status_bar.grid(
            row=0, column=0, sticky="ew", padx=Spacing.SM, pady=Spacing.XS
        )

    def update_connection_status(self):
        """Update connection status display with visual indicator."""
        if self.network_manager.check_connection():
            self.status_indicator.configure(bg=Colors.CONNECTED)
            self.status_label.configure(text="Connected", style="Success.TLabel")
            self.connect_btn.configure(state="disabled")
            self.disconnect_btn.configure(state="normal")
        else:
            self.status_indicator.configure(bg=Colors.DISCONNECTED)
            self.status_label.configure(text="Disconnected", style="Error.TLabel")
            self.connect_btn.configure(state="normal")
            self.disconnect_btn.configure(state="disabled")

    def connect_drive(self):
        """Connect to network drive."""
        self.set_status("Connecting...")
        self.connect_btn.configure(state="disabled")

        # Update UI to show connecting state
        self.status_indicator.configure(bg=Colors.WARNING)
        self.status_label.configure(text="Connecting...", style="Warning.TLabel")

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

        success, message = self.network_manager.disconnect()
        self.update_connection_status()
        self.set_status(message)
        self.clear_all()

    def scan_folder(self):
        """Scan folder for SAP CSV files."""
        self.set_status("Scanning folder...")
        success, message, dates = self.file_handler.scan_folder()
        self.found_dates = dates

        if success:
            self.set_status(message)
            self.populate_file_list()
            self.file_count_label.configure(text=f"{len(dates)} files found")
        else:
            self.set_status(message)
            messagebox.showerror("Scan Error", message)

    def populate_file_list(self):
        """Populate file listbox with detected files."""
        self.file_listbox.delete(0, tk.END)
        self.selected_files.clear()

        for date_str in self.found_dates:
            display_date = datetime.strptime(date_str, DATE_FORMAT).strftime(
                DATE_DISPLAY_FORMAT
            )
            self.file_listbox.insert(
                tk.END, f"{display_date}  •  {date_str}_FYBPL004.csv"
            )
            file_path = self.file_handler.files.get(date_str)
            if file_path:
                self.selected_files.append(file_path)

    def detect_files(self):
        """Detect files in selected date range."""
        # Build date strings from dropdowns
        start_date = f"{self.start_year_var.get()}-{self.start_month_var.get()}-{self.start_day_var.get()}"
        end_date = f"{self.end_year_var.get()}-{self.end_month_var.get()}-{self.end_day_var.get()}"

        # Validate date format
        try:
            datetime.strptime(start_date, DATE_DISPLAY_FORMAT)
            datetime.strptime(end_date, DATE_DISPLAY_FORMAT)
        except ValueError:
            messagebox.showerror("Invalid Date", "Please select valid dates.")
            return

        # Get files in range
        files_in_range = self.file_handler.get_files_in_range(start_date, end_date)

        # Update file listbox
        self.file_listbox.delete(0, tk.END)
        self.selected_files.clear()

        found_count = 0
        for date_str, file_path, exists in files_in_range:
            display_date = datetime.strptime(date_str, DATE_FORMAT).strftime(
                DATE_DISPLAY_FORMAT
            )
            if exists:
                status = "✓"
                self.file_listbox.insert(
                    tk.END, f"{status}  {display_date}  •  {file_path.name}"
                )
                self.selected_files.append(file_path)
                found_count += 1
            else:
                status = "✗"
                self.file_listbox.insert(
                    tk.END, f"{status}  {display_date}  •  {file_path.name}  (missing)"
                )
                self.selected_files.append(None)

        self.file_count_label.configure(
            text=f"{found_count} of {len(files_in_range)} files available"
        )
        self.set_status(f"Found {found_count} files in range")

    def on_file_select(self, event):
        """Handle file selection in listbox."""
        selection = self.file_listbox.curselection()
        if not selection:
            return

        # Get selected index
        index = selection[0]

        # Check if file exists and show preview
        if index < len(self.selected_files):
            file_path = self.selected_files[index]
            if file_path is None or not file_path.exists():
                self.clear_preview()
                self.preview_info_label.configure(text="File not available")
            else:
                self.show_preview(file_path)
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
        for row in rows:
            self.preview_tree.insert("", "end", values=row)

        # Update info label
        if valid:
            self.preview_info_label.configure(
                text=f"{file_path.name}  •  {len(rows)} rows shown", style="Body.TLabel"
            )
        else:
            self.preview_info_label.configure(
                text=f"{file_path.name}  •  {message}", style="Warning.TLabel"
            )

    def clear_preview(self):
        """Clear preview treeview."""
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        self.preview_info_label.configure(
            text="Select a file to preview", style="Caption.TLabel"
        )

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

    def clear_dates(self):
        """Clear date range selections to current date."""
        now = datetime.now()
        self.start_year_var.set(str(now.year))
        self.start_month_var.set(f"{now.month:02d}")
        self.start_day_var.set(f"{now.day:02d}")
        self.end_year_var.set(str(now.year))
        self.end_month_var.set(f"{now.month:02d}")
        self.end_day_var.set(f"{now.day:02d}")
        self.set_status("Dates reset to today")

    def clear_all(self):
        """Clear all selections and preview."""
        self.file_listbox.delete(0, tk.END)
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

    def check_for_updates(self, silent: bool = False):
        """Check GitHub for updates. silent=True = no dialog if already current."""

        def _check():
            checker = UpdateChecker(APP_VERSION)
            result, error = checker.check()
            self.root.after(0, self._handle_update_result, result, error, silent)

        threading.Thread(target=_check, daemon=True).start()

    def _handle_update_result(
        self, result: dict | None, error: str | None, silent: bool
    ):
        if result is None:
            if not silent:
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

    def _show_update_dialog(self, info: dict):
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
            frame, text="A new version is available!", font=("Segoe UI", 12, "bold")
        ).pack(pady=(0, 10))

        versions_frame = ttk.Frame(frame)
        versions_frame.pack(fill=tk.X, pady=5)
        ttk.Label(versions_frame, text=f"Current: {APP_VERSION}").pack(side=tk.LEFT)
        ttk.Label(versions_frame, text=f"Latest: {info['latest_version']}").pack(
            side=tk.RIGHT
        )

        if info.get("release_notes"):
            notes_text = tk.Text(frame, height=6, width=50, wrap=tk.WORD)
            notes_text.insert(tk.END, info["release_notes"])
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


class UpdateChecker:
    """Checks GitHub for newer releases and reports availability."""

    GITHUB_RELEASES_PAGE = "https://github.com/ITSyndicate25/SAP-CSV-Merger/releases"

    def __init__(self, current_version: str):
        self.current_version = current_version

    def check(self) -> tuple[dict | None, str | None]:
        """Fetch latest release from GitHub releases page.

        Uses the HTML page (no auth required) instead of the GitHub REST API,
        which returns 404 for unauthenticated requests on this repo.

        Returns:
            Tuple of (result_dict, error_message). result_dict is None on failure.
        """
        import urllib.request
        import ssl
        import re

        try:
            # Handle SSL certificates in PyInstaller bundles
            ssl_context = ssl.create_default_context()
            try:
                import certifi

                ssl_context.load_verify_locations(certifi.where())
            except ImportError:
                pass  # Use system certs if certifi not available

            req = urllib.request.Request(
                self.GITHUB_RELEASES_PAGE,
                headers={"User-Agent": "Mozilla/5.0 (compatible; SAPCSVMerger/1.0)"},
            )
            with urllib.request.urlopen(
                req, timeout=10, context=ssl_context
            ) as response:
                html = response.read().decode("utf-8", errors="replace")

            # Parse latest release tag from HTML
            # Looks for: /ITSyndicate25/SAP-CSV-Merger/releases/tag/v1.X.X
            match = re.search(
                r"/ITSyndicate25/SAP-CSV-Merger/releases/tag/v(\d+\.\d+\.\d+)",
                html,
            )
            if not match:
                return (None, "No release found on GitHub.")

            latest_version = match.group(1)
            release_url = f"{self.GITHUB_RELEASES_PAGE}/tag/v{latest_version}"

            current = tuple(int(x) for x in self.current_version.split("."))
            latest = tuple(int(x) for x in latest_version.split("."))

            update_available = latest > current

            return (
                {
                    "update_available": update_available,
                    "latest_version": latest_version,
                    "release_url": release_url,
                    "release_notes": "",
                },
                None,
            )
        except Exception as e:
            return (None, str(e))


def main():
    """Main entry point."""
    root = tk.Tk()
    SAPMergerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
