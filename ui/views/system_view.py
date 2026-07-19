"""Logs / System view (Phase 9 Step 2): read-only diagnostics.

Displays a read-only tail of the startup log and a small environment summary.
No writes of any kind. Files are opened read-only; missing files degrade
gracefully. No autonomy access, no backend mutation.
"""
import os
import sys
import platform
import tkinter as tk

STARTUP_LOG = os.path.join("logs", "startup_crash.log")


class SystemView:
    """Read-only logs + environment panel."""

    def __init__(self, parent):
        self.parent = parent

        self.header = tk.Label(parent, text="Logs / System (read-only)", anchor="w")
        self.header.pack(fill="x", padx=16, pady=(16, 8))

        self.view = tk.Text(parent, height=22, state="disabled")
        self.view.pack(fill="both", expand=True, padx=16, pady=8)

        tk.Button(parent, text="Refresh", command=self.refresh).pack(pady=(0, 12))

        self.refresh()

    def _tail(self, path, max_lines=60):
        if not os.path.isfile(path):
            return "(no log file at %s)" % path
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                data = fh.readlines()
        except OSError as exc:
            return "(could not read %s: %s)" % (path, exc)
        return "".join(data[-max_lines:]) or "(log is empty)"

    def refresh(self):
        lines = []
        lines.append("=== ENVIRONMENT ===")
        lines.append("python: %s" % sys.version.split()[0])
        lines.append("platform: %s" % platform.platform())
        lines.append("cwd: %s" % os.getcwd())
        lines.append("")
        lines.append("=== STARTUP LOG (tail) ===")
        lines.append(self._tail(STARTUP_LOG))

        text = "\n".join(lines)
        self.view.config(state="normal")
        self.view.delete("1.0", tk.END)
        self.view.insert(tk.END, text)
        self.view.config(state="disabled")


def build(parent):
    """Build the logs/system view; returns the SystemView instance."""
    return SystemView(parent)
