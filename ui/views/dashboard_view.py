"""Dashboard overview (Phase 9 Step 2): read-only landing summary.

Aggregates read-only signals into a single at-a-glance panel:
  - autonomy level + active workflows (via ui.autonomy_dashboard.snapshot())
  - bridge online/enabled status
  - agent count
  - catalog (model) count

STRICTLY READ-ONLY. No Governor imports, no mutation, no config/supervisor
writes. Uses snapshot() only for autonomy data. Network/data calls are wrapped
so a failure degrades gracefully instead of crashing the UI.

Phase 9 Step N: the existing backend cognitive state is now wired in as a live
section. The Dashboard renders:
  - the cognitive boot report (core.integration.default_integrator.boot_report)
  - a live cognitive cycle that refreshes on a timer
    (core.integration.default_integrator.cognitive_cycle)
Both reuse the existing FrameworkIntegrator controller; no new state is created.
"""
import tkinter as tk

import ui.autonomy_dashboard as autonomy_dashboard
from core.integration import default_integrator


# Live cognitive-cycle refresh interval (ms). Kept modest so the cycle visibly
# updates without saturating the UI thread.
COGNITIVE_REFRESH_MS = 5000


def _fmt_boot_report(report):
    """Render the existing BootReport dict as read-only text."""
    if not report:
        return "(boot report unavailable)"
    lines = []
    caps = report.get("capabilities", {}) or {}
    models = caps.get("models", {}) or {}
    lines.append("Cognitive Boot Report:")
    lines.append("  models available: %s (total %s)"
                 % (models.get("available"), models.get("total")))
    lines.append("  categories: %s"
                 % (", ".join(models.get("categories", [])) or "(none)"))
    val = report.get("validation", {}) or {}
    lines.append("  validation: healthy=%s failed=%s"
                 % (val.get("healthy"), val.get("failed", 0)))
    ctx = report.get("context", {}) or {}
    objective = ctx.get("objective") if isinstance(ctx, dict) else None
    if objective:
        lines.append("  startup objective: %s" % objective)
    notes = report.get("notes", []) or []
    if notes:
        lines.append("  notes: %s" % ("; ".join(notes)))
    cyc = report.get("cognitive_cycle")
    if cyc:
        lines.append("  boot cognitive cycle: task='%s' plan=%s"
                     % (cyc.get("task"), cyc.get("plan_id")))
    return "\n".join(lines)


def _fmt_cognitive_cycle(cycle):
    """Render the existing cognitive cycle dict as read-only text."""
    if not cycle:
        return "(cognitive cycle: no orchestrator wired)"
    lines = []
    lines.append("Live Cognitive Cycle:")
    lines.append("  task: %s" % cycle.get("task"))
    intent = cycle.get("intent") or {}
    lines.append("  intent: %s (confidence=%.2f, needs_clarification=%s)"
                 % (intent.get("intent_type"),
                    float(intent.get("confidence") or 0),
                    intent.get("needs_clarification")))
    decision = cycle.get("decision") or {}
    lines.append("  decision: recommended=%s"
                 % decision.get("recommended"))
    lines.append("  plan_id: %s | execution_plan_id: %s"
                 % (cycle.get("plan_id"), cycle.get("execution_plan_id")))
    review = cycle.get("review")
    lines.append("  review: %s" % ("present" if review else "none"))
    trace = cycle.get("trace") or []
    if trace:
        last = trace[-1]
        lines.append("  trace: %d stage(s), last=%s"
                     % (len(trace), last.get("stage")))
    return "\n".join(lines)


class DashboardView:
    """Read-only aggregate overview for the Command Center landing tab."""

    def __init__(self, parent):
        self.parent = parent

        self.title = tk.Label(parent, text="Nexus98 Command Center", anchor="w")
        self.title.pack(fill="x", padx=16, pady=(16, 4))

        self.subtitle = tk.Label(
            parent, text="System overview (read-only)", anchor="w"
        )
        self.subtitle.pack(fill="x", padx=16, pady=(0, 12))

        self.summary = tk.Text(parent, height=12, state="disabled")
        self.summary.pack(fill="both", expand=False, padx=16, pady=8)

        # Live backend state: cognitive boot report + cognitive cycle.
        self.boot = tk.Text(parent, height=6, state="disabled")
        self.boot.pack(fill="both", expand=False, padx=16, pady=(0, 8))

        self.cycle = tk.Text(parent, height=8, state="disabled")
        self.cycle.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        tk.Button(
            parent, text="Refresh Overview", command=self.refresh
        ).pack(pady=(0, 12))

        self._cycle_task = None
        self.refresh()
        # Begin live cognitive-cycle updates.
        self._schedule_cycle()

    def _safe(self, fn, default):
        try:
            return fn()
        except Exception:
            return default

    def _set_text(self, widget, text):
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, text)
        widget.config(state="disabled")

    def refresh(self):
        lines = []
        lines.append("=== NEXUS98 COMMAND CENTER - OVERVIEW ===")
        lines.append("")

        # Autonomy (read-only snapshot only)
        snap = self._safe(autonomy_dashboard.snapshot, {})
        lvl = snap.get("current_level", {}) or {}
        lines.append("Autonomy:")
        lines.append("  level: L%s - %s" % (lvl.get("level"), lvl.get("name")))
        lines.append("  active workflows: %s"
                     % (", ".join(snap.get("active_workflows", [])) or "(none)"))
        es = snap.get("emergency_stop_status", {}) or {}
        lines.append("  emergency stop engaged: %s" % es.get("engaged"))
        lines.append("  pending requests: %d"
                     % len(snap.get("pending_requests", [])))
        lines.append("")

        # Bridge (read-only status)
        def _bridge():
            from core.bridge_controller import get_status
            return get_status()
        state = self._safe(_bridge, {"online": None, "enabled": None})
        lines.append("Bridge:")
        lines.append("  online: %s | enabled: %s"
                     % (state.get("online"), state.get("enabled")))
        lines.append("")

        # Agents (read-only count)
        def _agents():
            from core.agent_registry import list_agents
            return list_agents()
        agents = self._safe(_agents, [])
        lines.append("Agents registered: %d" % len(agents))

        # Catalog (read-only count)
        def _catalog():
            from core.catalog import get_catalog
            return get_catalog()
        catalog = self._safe(_catalog, [])
        lines.append("Models in catalog: %d" % len(catalog))

        self._set_text(self.summary, "\n".join(lines))

        # Cognitive boot report (existing backend state).
        def _boot():
            return default_integrator.boot_report(
                startup_objective="Nexus98 Command Center",
                run_cognitive_cycle=False,
            )
        boot = self._safe(_boot, None)
        self._set_text(self.boot, _fmt_boot_report(boot))

    def _refresh_cycle(self):
        """Refresh the live cognitive cycle from existing backend state."""
        def _cycle():
            return default_integrator.cognitive_cycle(
                "Nexus98 Command Center live cycle"
            )
        cycle = self._safe(_cycle, None)
        self._set_text(self.cycle, _fmt_cognitive_cycle(cycle))

    def _schedule_cycle(self):
        """Periodically refresh the cognitive cycle so it updates live."""
        try:
            self._refresh_cycle()
        finally:
            self._cycle_task = self.parent.after(
                COGNITIVE_REFRESH_MS, self._schedule_cycle
            )

    def __del__(self):
        if self._cycle_task is not None:
            try:
                self.parent.after_cancel(self._cycle_task)
            except Exception:
                pass


def build(parent):
    """Build the dashboard overview; returns the DashboardView instance."""
    return DashboardView(parent)
