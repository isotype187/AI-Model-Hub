"""Operations view (Phase C): autonomy-visibility for the real task pipeline.

Extends the Command Center with a single, read-only view of the live AI-work
operating state. It surfaces:
  * current goal / active workflow phase
  * active tasks (with owner + routed role)
  * agent state (from the registry)
  * cognitive cycle details (advisory, via FrameworkIntegrator)
  * blockers
  * decisions (routing + assignments + reviews)

STRICTLY READ-ONLY. This view calls only advisory/observability surfaces:
  - core.workflow.default_workflow       (pipeline state, advisory)
  - core.integration.default_integrator  (cognitive cycle, advisory)
  - core.agent_registry.list_agents      (registry read)
  - core.providers.default_registry      (provider status, read-only)
  - core.continuity.default_continuity   (active tasks, read-only)
It performs NO writes and never touches the Governor / auto_execute.
"""
import tkinter as tk

import core.workflow as workflow
from core.integration import default_integrator
from core.agent_registry import list_agents
from core.providers import default_registry
from core.continuity import default_continuity


# Refresh cadence for the live sections (ms).
REFRESH_MS = 4000


class OperationsView:
    """Read-only live operations panel for the AI-work operating system."""

    def __init__(self, parent):
        self.parent = parent

        self.title = tk.Label(parent, text="Nexus98 Operations", anchor="w")
        self.title.pack(fill="x", padx=16, pady=(12, 4))

        self.body = tk.Text(parent, height=30, state="disabled", wrap="word")
        self.body.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        tk.Button(parent, text="Refresh Operations",
                  command=self.refresh).pack(pady=(0, 10))

        self._task = None
        self.refresh()
        self._schedule()

    # ------------------------------------------------------------------
    # Safe readers (degrade gracefully; never crash the app)
    # ------------------------------------------------------------------

    @staticmethod
    def _safe(fn, default):
        try:
            return fn()
        except Exception:
            return default

    def _set(self, text):
        self.body.config(state="normal")
        self.body.delete("1.0", tk.END)
        self.body.insert(tk.END, text)
        self.body.config(state="disabled")

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    def _active_goal(self):
        records = workflow.default_workflow.list_records()
        if not records:
            return "(no active goal - submit one via the Supervisor console)"
        rec = records[-1]
        lines = []
        lines.append("Current Goal:")
        lines.append("  %s" % rec["goal"])
        lines.append("  phase: %s | workflow_id: %s"
                     % (rec["phase"], rec["workflow_id"]))
        intent = rec.get("intent") or {}
        if intent:
            lines.append("  intent: %s (confidence=%.2f, needs_clarification=%s)"
                         % (intent.get("intent_type"),
                            float(intent.get("confidence") or 0),
                            intent.get("needs_clarification")))
        return "\n".join(lines)

    def _active_tasks(self):
        lines = []
        lines.append("Active Tasks:")
        ctx = self._safe(lambda: default_continuity.active_tasks(), [])
        if ctx:
            for t in ctx[-8:]:
                lines.append("  - [%s] %s (%s)"
                             % (t.get("status"), t.get("title"), t.get("owner")))
        else:
            lines.append("  (none tracked)")
        records = workflow.default_workflow.list_records()
        if records:
            rec = records[-1]
            if rec.get("tasks"):
                lines.append("Pipeline tasks:")
                for t in rec["tasks"][-8:]:
                    lines.append("  - %s -> owner=%s role=%s"
                                 % (t.get("title"), t.get("owner"),
                                    t.get("role", "?")))
        return "\n".join(lines)

    def _agent_state(self):
        lines = ["Agent State:"]
        for a in list_agents():
            lines.append("  - %s [%s] %s"
                         % (a["name"], a.get("status"), a.get("type")))
        return "\n".join(lines)

    def _cognitive(self):
        lines = ["Cognitive Cycle (advisory):"]
        cycle = self._safe(
            lambda: default_integrator.cognitive_cycle(
                "Nexus98 Operations live cycle"), None)
        if not cycle:
            lines.append("  (no orchestrator wired)")
            return "\n".join(lines)
        intent = cycle.get("intent") or {}
        decision = cycle.get("decision") or {}
        lines.append("  task: %s" % cycle.get("task"))
        lines.append("  intent: %s (confidence=%.2f)"
                     % (intent.get("intent_type"),
                        float(intent.get("confidence") or 0)))
        lines.append("  decision: recommended=%s" % decision.get("recommended"))
        lines.append("  plan_id: %s | execution_plan_id: %s"
                     % (cycle.get("plan_id"), cycle.get("execution_plan_id")))
        trace = cycle.get("trace") or []
        if trace:
            lines.append("  trace: %d stage(s), last=%s"
                         % (len(trace), trace[-1].get("stage")))
        return "\n".join(lines)

    def _decisions(self):
        lines = ["Decisions:"]
        records = workflow.default_workflow.list_records()
        if records:
            rec = records[-1]
            for d in rec.get("decisions", [])[-6:]:
                if "routed_role" in d:
                    lines.append("  - route '%s' -> %s (%s)"
                                 % (d.get("title"), d.get("assigned_agent"),
                                    d.get("routed_role")))
                elif "note" in d:
                    lines.append("  - %s" % d.get("note"))
                else:
                    lines.append("  - %s" % (d,))
        else:
            lines.append("  (none yet)")
        return "\n".join(lines)

    def _blockers(self):
        lines = ["Blockers:"]
        records = workflow.default_workflow.list_records()
        seen = []
        if records:
            for b in records[-1].get("blockers", []):
                seen.append(b)
        if not seen:
            lines.append("  (none)")
            return "\n".join(lines)
        for b in seen[-6:]:
            lines.append("  - %s" % b)
        return "\n".join(lines)

    def _providers(self):
        lines = ["Providers (boundary):"]
        status = self._safe(lambda: default_registry.status(), {})
        for p in (status.get("model_providers") or []):
            lines.append("  - model:%s available=%s"
                         % (p["name"], p["available"]))
        for p in (status.get("task_providers") or []):
            lines.append("  - task:%s available=%s"
                         % (p["name"], p["available"]))
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def refresh(self):
        sections = [
            self._active_goal(),
            "",
            self._active_tasks(),
            "",
            self._agent_state(),
            "",
            self._cognitive(),
            "",
            self._decisions(),
            "",
            self._blockers(),
            "",
            self._providers(),
        ]
        self._set("\n".join(sections))

    def _schedule(self):
        try:
            self.refresh()
        finally:
            self._task = self.parent.after(REFRESH_MS, self._schedule)

    def __del__(self):
        task = getattr(self, "_task", None)
        if task is not None:
            try:
                self.parent.after_cancel(task)
            except Exception:
                pass


def build(parent):
    """Build the Operations view; returns the OperationsView instance."""
    return OperationsView(parent)