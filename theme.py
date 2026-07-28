"""
SAP CSV Merger — Theme and Styling
Modern, professional theme for the GUI application.
"""

import tkinter as tk
from tkinter import ttk

# ─── Color Palette ────────────────────────────────────────────────────────────


class Colors:
    """Modern color palette for data utility tool."""

    # Primary colors
    PRIMARY = "#1a73e8"  # Google Blue - actions, links
    PRIMARY_DARK = "#1557b0"  # Darker blue for hover
    PRIMARY_LIGHT = "#e8f0fe"  # Light blue for backgrounds

    # Secondary colors
    SECONDARY = "#00897b"  # Teal - accents, secondary actions
    SECONDARY_DARK = "#00695c"  # Darker teal for hover

    # Neutral colors
    BACKGROUND = "#f5f7fa"  # Light gray background
    SURFACE = "#ffffff"  # White surface
    SURFACE_VARIANT = "#f8f9fa"  # Slightly darker surface
    BORDER = "#e0e0e0"  # Subtle borders
    BORDER_LIGHT = "#f0f0f0"  # Very subtle borders

    # Text colors
    TEXT_PRIMARY = "#1a1a2e"  # Dark text
    TEXT_SECONDARY = "#5f6368"  # Gray text
    TEXT_DISABLED = "#9aa0a6"  # Light gray for disabled
    TEXT_ON_PRIMARY = "#ffffff"  # White text on primary

    # Status colors
    SUCCESS = "#34a853"  # Green
    SUCCESS_LIGHT = "#e6f4ea"  # Light green background
    WARNING = "#fbbc04"  # Orange/amber
    WARNING_LIGHT = "#fef7e0"  # Light orange background
    ERROR = "#ea4335"  # Red
    ERROR_LIGHT = "#fce8e6"  # Light red background
    INFO = "#4285f4"  # Blue info
    INFO_LIGHT = "#e8f0fe"  # Light blue background

    # Connection status
    CONNECTED = "#34a853"  # Green
    DISCONNECTED = "#ea4335"  # Red

    # Shadows (simulated with background colors for tkinter)
    SHADOW_LIGHT = "#e8eaed"
    SHADOW_MEDIUM = "#d2d5d9"


# ─── Typography ───────────────────────────────────────────────────────────────


class Typography:
    """Font definitions for the application."""

    # Font families
    FONT_FAMILY = "Segoe UI"  # Clean, modern Windows font
    MONO_FAMILY = "Consolas"  # Monospace for data/codes

    # Font sizes
    SIZE_XS = 9
    SIZE_SM = 10
    SIZE_MD = 11
    SIZE_LG = 13
    SIZE_XL = 16
    SIZE_XXL = 20

    # Font weights (tkinter only supports normal and bold)
    WEIGHT_NORMAL = "normal"
    WEIGHT_BOLD = "bold"

    # Predefined font tuples (family, size, weight)
    HEADER_XL = (FONT_FAMILY, SIZE_XXL, WEIGHT_BOLD)
    HEADER_LG = (FONT_FAMILY, SIZE_XL, WEIGHT_BOLD)
    HEADER_MD = (FONT_FAMILY, SIZE_LG, WEIGHT_BOLD)
    HEADER_SM = (FONT_FAMILY, SIZE_MD, WEIGHT_BOLD)

    BODY_LG = (FONT_FAMILY, SIZE_MD, WEIGHT_NORMAL)
    BODY_MD = (FONT_FAMILY, SIZE_SM, WEIGHT_NORMAL)
    BODY_SM = (FONT_FAMILY, SIZE_XS, WEIGHT_NORMAL)

    LABEL = (FONT_FAMILY, SIZE_SM, WEIGHT_BOLD)
    LABEL_SM = (FONT_FAMILY, SIZE_XS, WEIGHT_NORMAL)

    BUTTON = (FONT_FAMILY, SIZE_SM, WEIGHT_BOLD)
    BUTTON_LARGE = (FONT_FAMILY, SIZE_MD, WEIGHT_BOLD)

    MONO = (MONO_FAMILY, SIZE_SM, WEIGHT_NORMAL)
    MONO_BOLD = (MONO_FAMILY, SIZE_SM, WEIGHT_BOLD)
    MONO_LARGE = (MONO_FAMILY, SIZE_MD, WEIGHT_NORMAL)

    STATUS = (FONT_FAMILY, SIZE_XS, WEIGHT_NORMAL)


# ─── Spacing ──────────────────────────────────────────────────────────────────


class Spacing:
    """Consistent spacing values."""

    XXS = 2
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 24
    XXL = 32
    XXXL = 48


# ─── Border Radius ────────────────────────────────────────────────────────────


class BorderRadius:
    """Border radius values (simulated in tkinter)."""

    SM = 4
    MD = 6
    LG = 8
    XL = 12


# ─── Theme Configuration ─────────────────────────────────────────────────────


class Theme:
    """Configure ttk styles for the application."""

    @staticmethod
    def configure(root: tk.Tk):
        """Apply theme to the application."""
        style = ttk.Style(root)

        # Use clam theme as base (more customizable)
        style.theme_use("clam")

        # ── Configure General ──
        style.configure(".", font=Typography.BODY_MD)
        style.configure("TFrame", background=Colors.BACKGROUND)
        style.configure(
            "TLabel", background=Colors.BACKGROUND, foreground=Colors.TEXT_PRIMARY
        )
        style.configure(
            "TButton", background=Colors.SURFACE, foreground=Colors.TEXT_PRIMARY
        )

        # ── Configure Frames ──
        style.configure("TFrame", background=Colors.BACKGROUND)
        style.configure(
            "Card.TFrame", background=Colors.SURFACE, relief="flat", borderwidth=0
        )
        style.configure("Surface.TFrame", background=Colors.SURFACE)
        style.configure("Inner.TFrame", background=Colors.SURFACE)

        # ── Configure Labels ──
        style.configure(
            "TLabel", background=Colors.BACKGROUND, foreground=Colors.TEXT_PRIMARY
        )
        style.configure(
            "Title.TLabel",
            font=Typography.HEADER_XL,
            foreground=Colors.TEXT_PRIMARY,
            background=Colors.BACKGROUND,
        )
        style.configure(
            "Header.TLabel",
            font=Typography.HEADER_LG,
            foreground=Colors.TEXT_PRIMARY,
            background=Colors.BACKGROUND,
        )
        style.configure(
            "Subheader.TLabel",
            font=Typography.HEADER_MD,
            foreground=Colors.TEXT_PRIMARY,
            background=Colors.BACKGROUND,
        )
        style.configure(
            "CardHeader.TLabel",
            font=Typography.HEADER_MD,
            foreground=Colors.TEXT_PRIMARY,
            background=Colors.SURFACE,
        )
        style.configure(
            "Body.TLabel",
            font=Typography.BODY_MD,
            foreground=Colors.TEXT_PRIMARY,
            background=Colors.BACKGROUND,
        )
        style.configure(
            "Caption.TLabel",
            font=Typography.BODY_SM,
            foreground=Colors.TEXT_SECONDARY,
            background=Colors.BACKGROUND,
        )
        style.configure(
            "Label.TLabel",
            font=Typography.LABEL,
            foreground=Colors.TEXT_PRIMARY,
            background=Colors.BACKGROUND,
        )
        style.configure(
            "LabelSm.TLabel",
            font=Typography.LABEL_SM,
            foreground=Colors.TEXT_SECONDARY,
            background=Colors.BACKGROUND,
        )
        style.configure(
            "CardTitle.TLabel",
            font=Typography.HEADER_MD,
            foreground=Colors.TEXT_PRIMARY,
            background=Colors.SURFACE,
        )

        # Status labels
        style.configure("Success.TLabel", foreground=Colors.SUCCESS)
        style.configure("Warning.TLabel", foreground=Colors.WARNING)
        style.configure("Error.TLabel", foreground=Colors.ERROR)
        style.configure("Info.TLabel", foreground=Colors.INFO)

        # ── Configure LabelFrames ──
        style.configure(
            "TLabelframe", background=Colors.SURFACE, foreground=Colors.TEXT_PRIMARY
        )
        style.configure(
            "TLabelframe.Label",
            font=Typography.HEADER_SM,
            foreground=Colors.TEXT_PRIMARY,
            background=Colors.SURFACE,
        )

        # Card-style Labelframe
        style.configure(
            "Card.TLabelframe", background=Colors.SURFACE, relief="flat", borderwidth=0
        )
        style.configure(
            "Card.TLabelframe.Label",
            font=Typography.HEADER_MD,
            foreground=Colors.TEXT_PRIMARY,
            background=Colors.SURFACE,
        )

        # ── Configure Buttons ──
        # Primary button
        style.configure(
            "Primary.TButton",
            font=Typography.BUTTON,
            foreground=Colors.TEXT_ON_PRIMARY,
            background=Colors.PRIMARY,
            borderwidth=0,
            padding=[Spacing.LG, Spacing.SM],
            relief="flat",
        )

        style.map(
            "Primary.TButton",
            background=[("active", Colors.PRIMARY_DARK), ("disabled", "#a0c4f0")],
            foreground=[("disabled", Colors.TEXT_ON_PRIMARY)],
        )

        # Secondary button
        style.configure(
            "Secondary.TButton",
            font=Typography.BUTTON,
            foreground=Colors.TEXT_PRIMARY,
            background=Colors.SURFACE,
            borderwidth=1,
            padding=[Spacing.LG, Spacing.SM],
            relief="flat",
        )

        style.map(
            "Secondary.TButton",
            background=[("active", Colors.SURFACE_VARIANT), ("disabled", "#e8eaed")],
            foreground=[("disabled", "#9aa0a6")],
        )

        # Success button
        style.configure(
            "Success.TButton",
            font=Typography.BUTTON,
            foreground=Colors.TEXT_ON_PRIMARY,
            background=Colors.SUCCESS,
            borderwidth=0,
            padding=[Spacing.LG, Spacing.SM],
            relief="flat",
        )

        style.map(
            "Success.TButton",
            background=[("active", "#2d9249"), ("disabled", Colors.TEXT_DISABLED)],
        )

        # Danger button
        style.configure(
            "Danger.TButton",
            font=Typography.BUTTON,
            foreground=Colors.TEXT_ON_PRIMARY,
            background=Colors.ERROR,
            borderwidth=0,
            padding=[Spacing.LG, Spacing.SM],
            relief="flat",
        )

        style.map(
            "Danger.TButton",
            background=[("active", "#d33426"), ("disabled", "#e07070")],
            foreground=[("disabled", Colors.TEXT_ON_PRIMARY)],
        )

        # ── Configure Entries ──
        style.configure(
            "TEntry", font=Typography.BODY_MD, padding=[Spacing.SM, Spacing.SM]
        )

        style.map(
            "TEntry",
            fieldbackground=[
                ("focus", Colors.SURFACE),
                ("disabled", Colors.SURFACE_VARIANT),
            ],
            bordercolor=[("focus", Colors.PRIMARY), ("disabled", Colors.BORDER)],
        )

        # ── Configure Combobox ──
        style.configure(
            "TCombobox", font=Typography.BODY_MD, padding=[Spacing.SM, Spacing.SM]
        )

        style.map(
            "TCombobox",
            fieldbackground=[("readonly", Colors.SURFACE)],
            selectbackground=[("readonly", Colors.PRIMARY_LIGHT)],
            selectforeground=[("readonly", Colors.PRIMARY)],
        )

        # ── Configure Treeview ──
        style.configure(
            "Treeview",
            font=Typography.BODY_SM,
            background=Colors.SURFACE,
            foreground=Colors.TEXT_PRIMARY,
            fieldbackground=Colors.SURFACE,
            borderwidth=0,
            padding=[Spacing.SM, Spacing.XS],
        )

        style.configure(
            "Treeview.Heading",
            font=Typography.LABEL,
            background=Colors.SURFACE_VARIANT,
            foreground=Colors.TEXT_PRIMARY,
            borderwidth=0,
            padding=[Spacing.SM, Spacing.SM],
        )

        style.map(
            "Treeview",
            background=[("selected", Colors.PRIMARY_LIGHT)],
            foreground=[("selected", Colors.PRIMARY)],
        )

        style.map("Treeview.Heading", background=[("active", Colors.BORDER)])

        # ── Configure Listbox ──
        style.configure(
            "TListbox",
            font=Typography.BODY_SM,
            background=Colors.SURFACE,
            foreground=Colors.TEXT_PRIMARY,
            selectbackground=Colors.PRIMARY_LIGHT,
            selectforeground=Colors.PRIMARY,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=Colors.BORDER,
            highlightcolor=Colors.PRIMARY,
        )

        # ── Configure Scrollbar ──
        style.configure(
            "Vertical.TScrollbar",
            background=Colors.SURFACE_VARIANT,
            troughcolor=Colors.BACKGROUND,
            borderwidth=0,
            arrowcolor=Colors.TEXT_SECONDARY,
            relief="flat",
        )

        style.map(
            "Vertical.TScrollbar",
            background=[
                ("active", Colors.BORDER),
                ("disabled", Colors.SURFACE_VARIANT),
            ],
        )

        # ── Configure Separator ──
        style.configure("TSeparator", background=Colors.BORDER)

        # ── Status Bar ──
        style.configure(
            "Status.TLabel",
            font=Typography.STATUS,
            foreground=Colors.TEXT_SECONDARY,
            background=Colors.SURFACE_VARIANT,
            padding=[Spacing.SM, Spacing.XS],
        )


# ─── Helper Functions ─────────────────────────────────────────────────────────


def create_tooltip(widget: tk.Widget, text: str):
    """Create a simple tooltip for a widget."""
    tooltip = None

    def show_tooltip(event):
        nonlocal tooltip
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

        label = tk.Label(
            tooltip,
            text=text,
            font=Typography.BODY_SM,
            background=Colors.TEXT_PRIMARY,
            foreground=Colors.TEXT_ON_PRIMARY,
            padx=Spacing.SM,
            pady=Spacing.XS,
        )
        label.pack()

    def hide_tooltip(event):
        nonlocal tooltip
        if tooltip:
            tooltip.destroy()
            tooltip = None

    widget.bind("<Enter>", show_tooltip)
    widget.bind("<Leave>", hide_tooltip)


def add_hover_effect(widget: tk.Widget, normal_bg: str, hover_bg: str):
    """Add hover effect to a widget."""
    widget.configure(background=normal_bg)

    def on_enter(event):
        widget.configure(background=hover_bg)

    def on_leave(event):
        widget.configure(background=normal_bg)

    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)
