"""Nexus98 Command Center - UI shell (Phase 9 Step 2).

Composition/entry point only. Builds a themed ttk.Notebook navigation shell and
hosts the existing view builders (behavior unchanged). No backend/autonomy
logic here: autonomy remains read-only via ui.autonomy_dashboard.snapshot()
inside its view. Preserves the launch_ui() entry contract and Tkinter.
"""
import tkinter as tk
from tkinter import ttk

from ui import theme
from ui.views import (
    dashboard_view,
    models_view,
    supervisor_view,
    agents_view,
    bridge_view,
    autonomy_view,
    system_view,
    operations_view,
)


def launch_ui():

    app = tk.Tk()
    app.title("Nexus98 Command Center")
    app.geometry("1600x950")

    theme.apply_theme(app)

    # Phase C: run first-run environment verification + expected-store seeding
    # (idempotent; best-effort so a setup issue never blocks the UI).
    try:
        from core.boot import verify_environment
        verify_environment()
    except Exception:
        pass

    # --- Title bar ---
    header = ttk.Frame(app)
    header.pack(fill="x", padx=16, pady=(14, 6))
    ttk.Label(header, text="Nexus98 Command Center", style="Title.TLabel").pack(
        side="left"
    )
    ttk.Label(
        header, text="Autonomy-governed workstation", style="Muted.TLabel"
    ).pack(side="left", padx=(14, 0))

    # --- Navigation (tabbed shell) ---
    nav = ttk.Notebook(app)
    nav.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def add_tab(title):
        frame = ttk.Frame(nav)
        nav.add(frame, text=title)
        return frame

    dashboard_tab = add_tab("Dashboard")
    models_tab = add_tab("Models")
    supervisor_tab = add_tab("Supervisor")
    agents_tab = add_tab("Agents")
    bridge_tab = add_tab("Bridge")
    autonomy_tab = add_tab("Autonomy")
    operations_tab = add_tab("Operations")
    system_tab = add_tab("Logs/System")

    # --- Dashboard (read-only overview) ---
    dashboard_view.build(dashboard_tab)

    # --- Models (left search/list + center inspector) ---
    models_left = tk.Frame(models_tab, width=320)
    models_left.pack(side="left", fill="y")
    models_center = tk.Frame(models_tab)
    models_center.pack(side="left", fill="both", expand=True)
    models = models_view.build(models_left, models_center)

    # --- Supervisor (task console; footer buttons drive shared refresh) ---
    supervisor = supervisor_view.build(app, supervisor_tab)

    # --- Agents ---
    agents = agents_view.build(agents_tab)

    # --- Bridge ---
    bridge_view.build(app, bridge_tab)

    # --- Autonomy (STRICTLY READ-ONLY; snapshot() only) ---
    autonomy_view.build(autonomy_tab)

    # --- Operations (Phase C; read-only live pipeline visibility) ---
    operations = operations_view.build(operations_tab)

    # --- Logs / System (read-only) ---
    system_view.build(system_tab)

    def refresh():
        # Preserve original coordinated refresh: models list + agents panel.
        models.refresh()
        agents.refresh()

    models.search_var.trace_add("write", lambda *_: refresh())
    supervisor.add_footer_buttons(refresh)

    refresh()

    app.mainloop()
