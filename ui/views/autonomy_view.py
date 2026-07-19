"""Autonomy view (Phase 9 Step 1): read-only observability dashboard tab.

STRICTLY READ-ONLY. This view calls ONLY ui.autonomy_dashboard.snapshot().
It performs no Governor mutation, no request_level_change(), no
emergency_stop(), and no writes to config/system_config.json or
core/supervisor.py. Behavior is preserved 1:1 from the Phase 8 integration.
"""
import tkinter as tk
from tkinter import ttk

import ui.autonomy_dashboard as autonomy_dashboard


def _format_autonomy_snapshot(snap):
    lvl = snap.get("current_level", {}) or {}
    es = snap.get("emergency_stop_status", {}) or {}
    cp = snap.get("last_checkpoint")
    lines = []
    lines.append("=== NEXUS98 AUTONOMY DASHBOARD (READ-ONLY) ===")
    lines.append("")
    lines.append("Current Level: L%s - %s" % (lvl.get("level"), lvl.get("name")))
    lines.append("  auto_execute: %s | config_intent: %s"
                 % (lvl.get("auto_execute"), lvl.get("config_intent")))
    lines.append("")
    lines.append("Active Workflows: %s"
                 % (", ".join(snap.get("active_workflows", [])) or "(none)"))
    lines.append("")
    pending = snap.get("pending_requests", [])
    lines.append("Pending Requests: %d" % len(pending))
    for e in pending:
        lines.append("  - id=%s target=L%s (%s)"
                     % (e.get("request_id"), e.get("target_level"), e.get("ts")))
    lines.append("")
    history = snap.get("approval_history", [])
    lines.append("Approval History: %d" % len(history))
    for e in history[-5:]:
        lines.append("  - %s id=%s target=L%s decision=%s"
                     % (e.get("ts"), e.get("request_id"),
                        e.get("target_level"), e.get("decision")))
    lines.append("")
    audit = snap.get("audit_events", [])
    lines.append("Recent Audit Events: %d (newest first)" % len(audit))
    for e in audit[:8]:
        lines.append("  - %s %s" % (e.get("ts"), e.get("event")))
    lines.append("")
    if cp:
        lines.append("Last Checkpoint: %s" % cp.get("name"))
    else:
        lines.append("Last Checkpoint: (none)")
    lines.append("Rollback Available: %s" % snap.get("rollback_available"))
    lines.append("")
    lines.append("Emergency Stop:")
    lines.append("  engaged: %s | auto_execute_on: %s"
                 % (es.get("engaged"), es.get("auto_execute_on")))
    lines.append("  level_zero_consistent: %s" % es.get("level_zero_consistent"))
    last_es = es.get("last_event")
    lines.append("  last_event: %s"
                 % (last_es.get("ts") if last_es else "(never)"))
    return "\n".join(lines)


class AutonomyView:
    """Owns the read-only autonomy dashboard notebook tab."""

    def __init__(self, right):
        # ------------------------------------------------------------------
        # Phase 8 - Autonomy Observability (STRICTLY READ-ONLY).
        # This view ONLY calls ui.autonomy_dashboard.snapshot(). It performs no
        # Governor mutation, no request_level_change(), no emergency_stop(),
        # and no writes to config/system_config.json or core/supervisor.py.
        # ------------------------------------------------------------------
        self.autonomy_notebook = ttk.Notebook(right)
        self.autonomy_notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.autonomy_tab = tk.Frame(self.autonomy_notebook)
        self.autonomy_notebook.add(self.autonomy_tab, text="Autonomy Dashboard")

        self.autonomy_view = tk.Text(
            self.autonomy_tab, height=20, state="disabled"
        )
        self.autonomy_view.pack(fill="both", expand=True)

        tk.Button(
            self.autonomy_tab,
            text="Refresh Autonomy Dashboard",
            command=self.refresh,
        ).pack(pady=5)

        self.refresh()

    def refresh(self):
        # Read-only: assemble the snapshot and render it. No mutation calls.
        try:
            snap = autonomy_dashboard.snapshot()
            text = _format_autonomy_snapshot(snap)
        except Exception as exc:  # display errors without crashing the UI
            text = "Autonomy dashboard unavailable (read-only): %s" % exc
        self.autonomy_view.config(state="normal")
        self.autonomy_view.delete("1.0", tk.END)
        self.autonomy_view.insert(tk.END, text)
        self.autonomy_view.config(state="disabled")


def build(right):
    """Build the read-only autonomy view; returns the AutonomyView instance."""
    return AutonomyView(right)
