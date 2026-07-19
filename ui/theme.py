"""Nexus98 Command Center - consistent ttk styling (Phase 9 Step 2).

Pure presentation. No backend calls, no autonomy access, no dependencies
beyond the standard library tkinter/ttk. Applying the theme never changes
behavior; it only sets fonts, padding, and colors.
"""
from tkinter import ttk

# Nexus98 palette (dark command-center aesthetic).
BG = "#1e1e2e"
BG_ALT = "#26263a"
FG = "#e6e6f0"
ACCENT = "#5b8def"
MUTED = "#9aa0b5"
OK = "#3ecf8e"
WARN = "#e5c07b"
ERR = "#e06c75"

FONT = ("Segoe UI", 10)
FONT_TITLE = ("Segoe UI Semibold", 18)
FONT_HEADER = ("Segoe UI Semibold", 12)
FONT_MONO = ("Consolas", 10)


def apply_theme(root):
    """Apply the Command Center ttk theme to the given root window.

    Returns the ttk.Style instance. Safe to call once at startup.
    """
    style = ttk.Style(root)
    try:
        style.theme_use("clam")  # clam allows full color control cross-platform
    except Exception:
        pass  # fall back to platform default if unavailable

    root.configure(bg=BG)

    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=BG_ALT)
    style.configure("TLabel", background=BG, foreground=FG, font=FONT)
    style.configure("Title.TLabel", background=BG, foreground=FG, font=FONT_TITLE)
    style.configure("Header.TLabel", background=BG, foreground=ACCENT, font=FONT_HEADER)
    style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=FONT)
    style.configure("TButton", font=FONT, padding=6)
    style.configure("Accent.TButton", font=FONT, padding=6)
    style.map("Accent.TButton",
              foreground=[("!disabled", "#ffffff")],
              background=[("!disabled", ACCENT), ("active", "#4a7ad8")])

    style.configure("TNotebook", background=BG, borderwidth=0, tabmargins=(8, 6, 8, 0))
    style.configure("TNotebook.Tab", font=FONT, padding=(16, 8),
                    background=BG_ALT, foreground=MUTED)
    style.map("TNotebook.Tab",
              background=[("selected", BG)],
              foreground=[("selected", FG)])

    style.configure("TLabelframe", background=BG, foreground=FG)
    style.configure("TLabelframe.Label", background=BG, foreground=ACCENT, font=FONT_HEADER)

    return style
