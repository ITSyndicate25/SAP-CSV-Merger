"""
SAP CSV Merger — design system for the tkinter GUI.

One palette, one type scale, one place for ttk styles. Sizes marked "logical"
are 96-DPI pixels and pass through :func:`px` so the whole layout keeps its
proportions on scaled displays.
"""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

# ─── Color Palette ────────────────────────────────────────────────────────────


class Colors:
    """Palette: dark instrument chrome around a cool, paper-like workspace."""

    # Application chrome
    CHROME = "#0e1b2c"
    CHROME_HOVER = "#182b42"
    CHROME_BORDER = "#3b5471"
    CHROME_TEXT = "#f2f6fb"
    CHROME_MUTED = "#9db0c6"

    # Workspace surfaces
    BACKGROUND = "#eef1f6"
    SURFACE = "#ffffff"
    SURFACE_VARIANT = "#f5f8fb"
    BORDER = "#dde4ec"
    BORDER_STRONG = "#c7d2df"

    # Text
    TEXT_PRIMARY = "#16212e"
    TEXT_SECONDARY = "#5b6b7c"
    TEXT_MUTED = "#8b98a8"
    TEXT_DISABLED = "#b3bdc9"
    TEXT_ON_PRIMARY = "#ffffff"

    # Accent — one blue, used for the main action and selection only
    PRIMARY = "#1b5fd8"
    PRIMARY_DARK = "#1549ad"
    PRIMARY_LIGHT = "#e8effc"
    PRIMARY_DISABLED = "#a9c1ee"

    # Semantic
    SUCCESS = "#157347"
    SUCCESS_DARK = "#11603a"
    SUCCESS_LIGHT = "#e6f4ec"
    WARNING = "#9a6100"
    WARNING_LIGHT = "#fdf3dd"
    ERROR = "#c62828"
    ERROR_DARK = "#a81f1f"
    ERROR_LIGHT = "#fdecec"


# ─── Typography ───────────────────────────────────────────────────────────────


class Typography:
    """Segoe UI for the interface, Consolas for CSV data."""

    FONT_FAMILY = "Segoe UI"
    MONO_FAMILY = "Consolas"

    SIZE_XS = 8
    SIZE_SM = 9
    SIZE_MD = 10
    SIZE_XL = 14

    TITLE = (FONT_FAMILY, SIZE_XL, "bold")
    CARD_TITLE = (FONT_FAMILY, SIZE_MD, "bold")
    UI = (FONT_FAMILY, SIZE_SM)
    UI_BOLD = (FONT_FAMILY, SIZE_SM, "bold")
    CAPTION = (FONT_FAMILY, SIZE_XS)
    CAPTION_BOLD = (FONT_FAMILY, SIZE_XS, "bold")


# ─── Spacing ──────────────────────────────────────────────────────────────────


class Spacing:
    """Logical spacing steps (96-DPI pixels)."""

    XXS = 2
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 24
    XXL = 32


# ─── Scaling ──────────────────────────────────────────────────────────────────

_BASE_SCALING = 96 / 72  # tk scaling at 100% display DPI


def scale(widget: tk.Misc) -> float:
    """Return the display scale factor relative to 96 DPI."""
    return float(widget.tk.call("tk", "scaling")) / _BASE_SCALING


def px(widget: tk.Misc, value: float) -> int:
    """Convert a logical pixel count to device pixels for *widget*'s display."""
    return int(round(value * scale(widget)))


# ─── Theme Configuration ──────────────────────────────────────────────────────


class Theme:
    """Configure ttk styles and the fonts dialogs inherit."""

    @staticmethod
    def configure(root: tk.Tk):
        """Apply the design system to *root*."""
        _configure_fonts()
        style = ttk.Style(root)

        # clam exposes every element we restyle; the native themes ignore most.
        style.theme_use("clam")

        # The combobox drop-down is a classic Tk listbox, not a ttk widget.
        root.option_add("*TCombobox*Listbox.font", Typography.UI)
        root.option_add("*TCombobox*Listbox.background", Colors.SURFACE)
        root.option_add("*TCombobox*Listbox.foreground", Colors.TEXT_PRIMARY)
        root.option_add("*TCombobox*Listbox.selectBackground", Colors.PRIMARY)
        root.option_add("*TCombobox*Listbox.selectForeground", Colors.TEXT_ON_PRIMARY)

        def s(value: float) -> int:
            return px(root, value)

        _configure_frames(style)
        _configure_labels(style)
        _configure_buttons(style, s)
        _configure_inputs(style, s)
        _configure_treeview(style, root, s)
        _configure_scrollbar(style)
        _configure_panedwindow(style, s)


def _configure_fonts():
    """Match the built-in Tk fonts so menus and message boxes fit the app."""
    for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
        tkfont.nametofont(name).configure(
            family=Typography.FONT_FAMILY, size=Typography.SIZE_SM
        )
    tkfont.nametofont("TkFixedFont").configure(
        family=Typography.MONO_FAMILY, size=Typography.SIZE_SM
    )


def _configure_frames(style: ttk.Style):
    style.configure(".", font=Typography.UI)
    style.configure("TFrame", background=Colors.BACKGROUND)
    style.configure("App.TFrame", background=Colors.BACKGROUND)
    style.configure("Card.TFrame", background=Colors.SURFACE, relief="flat")


def _configure_labels(style: ttk.Style):
    base = dict(background=Colors.BACKGROUND, foreground=Colors.TEXT_PRIMARY)
    style.configure("TLabel", font=Typography.UI, **base)

    style.configure(
        "CardTitle.TLabel",
        font=Typography.CARD_TITLE,
        background=Colors.SURFACE,
        foreground=Colors.TEXT_PRIMARY,
    )
    style.configure(
        "CardMeta.TLabel",
        font=Typography.UI,
        background=Colors.SURFACE,
        foreground=Colors.TEXT_SECONDARY,
    )
    style.configure(
        "CardWarning.TLabel",
        font=Typography.UI,
        background=Colors.SURFACE,
        foreground=Colors.WARNING,
    )
    style.configure(
        "FieldLabel.TLabel",
        font=Typography.UI_BOLD,
        background=Colors.SURFACE,
        foreground=Colors.TEXT_PRIMARY,
    )
    style.configure(
        "Pill.TLabel",
        font=Typography.CAPTION_BOLD,
        background=Colors.PRIMARY_LIGHT,
        foreground=Colors.PRIMARY,
        padding=(8, 3),
    )
    style.configure(
        "Body.TLabel",
        font=Typography.UI,
        background=Colors.BACKGROUND,
        foreground=Colors.TEXT_PRIMARY,
    )
    style.configure(
        "Success.TLabel",
        font=Typography.UI_BOLD,
        background=Colors.BACKGROUND,
        foreground=Colors.SUCCESS,
    )


def _configure_buttons(style: ttk.Style, s):
    # clam leaves a -11 character minimum on buttons; 0 sizes them to the label.
    base = dict(font=Typography.UI_BOLD, padding=(s(14), s(7)), width=0, relief="flat")
    style.configure(
        "Primary.TButton",
        foreground=Colors.TEXT_ON_PRIMARY,
        background=Colors.PRIMARY,
        borderwidth=0,
        **base,
    )
    style.map(
        "Primary.TButton",
        background=[
            ("disabled", Colors.PRIMARY_DISABLED),
            ("pressed", Colors.PRIMARY_DARK),
            ("active", Colors.PRIMARY_DARK),
        ],
        foreground=[("disabled", Colors.TEXT_ON_PRIMARY)],
    )

    style.configure(
        "Success.TButton",
        foreground=Colors.TEXT_ON_PRIMARY,
        background=Colors.SUCCESS,
        borderwidth=0,
        **base,
    )
    style.map(
        "Success.TButton",
        background=[
            ("disabled", "#9dc7b2"),
            ("pressed", Colors.SUCCESS_DARK),
            ("active", Colors.SUCCESS_DARK),
        ],
        foreground=[("disabled", Colors.TEXT_ON_PRIMARY)],
    )

    style.configure(
        "Ghost.TButton",
        foreground=Colors.TEXT_SECONDARY,
        background=Colors.SURFACE,
        borderwidth=0,
        padding=(s(8), s(5)),
        width=0,
        font=Typography.UI_BOLD,
        relief="flat",
    )
    style.map(
        "Ghost.TButton",
        background=[("active", Colors.SURFACE_VARIANT)],
        foreground=[("disabled", Colors.TEXT_DISABLED)],
    )

    style.configure(
        "Segment.TButton",
        foreground=Colors.TEXT_PRIMARY,
        background=Colors.SURFACE_VARIANT,
        bordercolor=Colors.BORDER_STRONG,
        lightcolor=Colors.SURFACE_VARIANT,
        darkcolor=Colors.SURFACE_VARIANT,
        borderwidth=1,
        padding=(s(8), s(5)),
        width=0,
        font=Typography.UI,
        relief="flat",
    )
    style.map(
        "Segment.TButton",
        background=[("active", Colors.PRIMARY_LIGHT)],
        foreground=[("active", Colors.PRIMARY)],
    )

    style.configure(
        "DangerOutline.TButton",
        foreground=Colors.ERROR,
        background=Colors.SURFACE,
        bordercolor=Colors.ERROR_LIGHT,
        lightcolor=Colors.SURFACE,
        darkcolor=Colors.SURFACE,
        borderwidth=1,
        **base,
    )
    style.map(
        "DangerOutline.TButton",
        background=[("active", Colors.ERROR_LIGHT)],
        bordercolor=[("active", Colors.ERROR)],
    )

    style.configure(
        "ChromeOutline.TButton",
        foreground=Colors.CHROME_TEXT,
        background=Colors.CHROME,
        bordercolor=Colors.CHROME_BORDER,
        lightcolor=Colors.CHROME,
        darkcolor=Colors.CHROME,
        borderwidth=1,
        **base,
    )
    style.map(
        "ChromeOutline.TButton",
        background=[("disabled", Colors.CHROME), ("active", Colors.CHROME_HOVER)],
        foreground=[("disabled", Colors.CHROME_MUTED)],
        bordercolor=[("disabled", Colors.CHROME_BORDER)],
    )


def _configure_inputs(style: ttk.Style, s):
    style.configure(
        "TCombobox",
        fieldbackground=Colors.SURFACE,
        background=Colors.SURFACE,
        foreground=Colors.TEXT_PRIMARY,
        arrowcolor=Colors.TEXT_SECONDARY,
        bordercolor=Colors.BORDER_STRONG,
        lightcolor=Colors.BORDER_STRONG,
        darkcolor=Colors.BORDER_STRONG,
        padding=(s(6), s(4)),
        arrowsize=s(11),
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", Colors.SURFACE)],
        bordercolor=[("focus", Colors.PRIMARY)],
        lightcolor=[("focus", Colors.PRIMARY)],
        selectbackground=[("readonly", Colors.SURFACE)],
        selectforeground=[("readonly", Colors.TEXT_PRIMARY)],
    )
    style.configure(
        "Tool.TCheckbutton",
        font=Typography.UI,
        background=Colors.SURFACE,
        foreground=Colors.TEXT_SECONDARY,
        indicatorcolor=Colors.SURFACE,
        padding=(s(2), s(2)),
    )
    style.map(
        "Tool.TCheckbutton",
        background=[("active", Colors.SURFACE)],
        foreground=[("active", Colors.TEXT_PRIMARY)],
        indicatorcolor=[("selected", Colors.PRIMARY), ("!selected", Colors.SURFACE)],
    )


def _configure_treeview(style: ttk.Style, root: tk.Tk, s):
    row_font = tkfont.Font(family=Typography.FONT_FAMILY, size=Typography.SIZE_SM)
    style.configure(
        "Treeview",
        font=Typography.UI,
        background=Colors.SURFACE,
        fieldbackground=Colors.SURFACE,
        foreground=Colors.TEXT_PRIMARY,
        borderwidth=0,
        relief="flat",
        rowheight=row_font.metrics("linespace") + s(10),
    )
    style.configure(
        "Treeview.Heading",
        font=Typography.CAPTION_BOLD,
        background=Colors.SURFACE_VARIANT,
        foreground=Colors.TEXT_SECONDARY,
        borderwidth=0,
        relief="flat",
        padding=(s(8), s(6)),
    )
    style.map(
        "Treeview",
        background=[("selected", Colors.PRIMARY_LIGHT)],
        foreground=[("selected", Colors.TEXT_PRIMARY)],
    )
    style.map("Treeview.Heading", background=[("active", Colors.BORDER)])


def _configure_scrollbar(style: ttk.Style):
    style.configure(
        "Vertical.TScrollbar",
        background=Colors.BORDER_STRONG,
        troughcolor=Colors.SURFACE,
        bordercolor=Colors.SURFACE,
        arrowcolor=Colors.TEXT_MUTED,
        borderwidth=0,
        relief="flat",
    )
    style.configure(
        "Horizontal.TScrollbar",
        background=Colors.BORDER_STRONG,
        troughcolor=Colors.SURFACE,
        bordercolor=Colors.SURFACE,
        arrowcolor=Colors.TEXT_MUTED,
        borderwidth=0,
        relief="flat",
    )
    for orient in ("Vertical", "Horizontal"):
        style.map(
            f"{orient}.TScrollbar",
            background=[("active", Colors.TEXT_MUTED), ("disabled", Colors.BORDER)],
        )


def _configure_panedwindow(style: ttk.Style, s):
    # The sash doubles as the gutter between cards: canvas coloured, no grips.
    style.configure("TPanedwindow", background=Colors.BACKGROUND)
    style.configure(
        "Sash",
        sashthickness=s(10),
        gripcount=3,
        background=Colors.BACKGROUND,
    )


# ─── Card ─────────────────────────────────────────────────────────────────────


class Card(tk.Frame):
    """White panel with a one-pixel hairline border.

    A 1-pixel border is the whole decoration: tkinter cannot round corners, and
    simulated shadows cost widget depth for no legibility gain.
    """

    def __init__(self, parent: tk.Misc, title: str):
        super().__init__(parent, bg=Colors.BORDER)
        self.inner = ttk.Frame(self, style="Card.TFrame")
        self.inner.pack(fill="both", expand=True, padx=1, pady=1)

        self.header = ttk.Frame(self.inner, style="Card.TFrame")
        self.header.pack(
            fill="x",
            padx=px(self, Spacing.LG),
            pady=(px(self, Spacing.MD), px(self, Spacing.SM)),
        )
        ttk.Label(self.header, text=title, style="CardTitle.TLabel").pack(side="left")
        self.actions = ttk.Frame(self.header, style="Card.TFrame")
        self.actions.pack(side="right")

        self.body = ttk.Frame(self.inner, style="Card.TFrame")
        self.body.pack(fill="both", expand=True)


# ─── Shared Widgets ───────────────────────────────────────────────────────────


def style_tree_rows(tree: ttk.Treeview):
    """Alternate row colour so wide CSV rows stay scannable."""
    tree.tag_configure("odd", background=Colors.SURFACE_VARIANT)
