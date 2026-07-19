"""Supervisor view (Phase 9 Step 1): task console, output log, action buttons.

Behavior-preserving extraction of the center supervisor console. The threaded
run + app.after(0, ...) marshaling is preserved exactly, including the lazy
`from core.supervisor import run_task` import inside the worker.
"""
import threading
import tkinter as tk

from core.tray import run_tray


class SupervisorView:
    """Owns the supervisor task console and center action buttons."""

    def __init__(self, app, center):
        self.app = app
        self.center = center

        self.task_label = tk.Label(center, text="Supervisor Task Console:")
        self.task_label.pack()

        self.task_box = tk.Text(center, height=5)
        self.task_box.pack(fill="x")

        self.output = tk.Text(center, height=10)
        self.output.pack(fill="both")

        tk.Button(
            center,
            text="Run Supervisor Task",
            command=self.execute_task,
        ).pack()

    def execute_task(self):
        task = self.task_box.get("1.0", tk.END)
        self.output.insert(tk.END, "\nRunning:\n" + task)

        def worker():
            from core.supervisor import run_task

            self.app.after(
                0,
                lambda: self.output.insert(
                    tk.END, "\n[STATUS] Supervisor starting...\n"
                ),
            )

            def status_update(message):
                self.app.after(
                    0,
                    lambda: self.output.insert(
                        tk.END, f"\n[STATUS] {message}\n"
                    ),
                )

            result = run_task(task, status_callback=status_update)

            self.app.after(
                0,
                lambda: self.output.insert(tk.END, "\n\nRESULT:\n" + result),
            )

        threading.Thread(target=worker, daemon=True).start()

    def add_footer_buttons(self, refresh_command):
        """Pack the Refresh + Tray Mode buttons (original center-bottom order)."""
        tk.Button(self.center, text="Refresh", command=refresh_command).pack()
        tk.Button(
            self.center,
            text="Tray Mode",
            command=lambda: threading.Thread(target=run_tray, daemon=True).start(),
        ).pack()


def build(app, center):
    """Build the supervisor view; returns the SupervisorView instance."""
    return SupervisorView(app, center)
