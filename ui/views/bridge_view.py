"""Bridge view (Phase 9 Step 1): bridge control toggle + status.

Behavior-preserving extraction of the right-column Bridge Control. The custom
vertical canvas toggle, threaded enable/disable, and app.after(500, ...) status
refresh are preserved exactly. Backend calls (core.bridge_controller) unchanged.
"""
import threading
import tkinter as tk

from core.bridge_controller import get_status, enable_bridge, disable_bridge


class BridgeView:
    """Owns the bridge control widgets and toggle state."""

    def __init__(self, app, right):
        self.app = app
        self.bridge_enabled = False

        self.bridge_frame = tk.LabelFrame(right, text="Bridge Control")
        self.bridge_frame.pack(fill="x", padx=10, pady=10)

        self.switch_canvas = tk.Canvas(
            self.bridge_frame, width=90, height=150, highlightthickness=0
        )
        self.switch_canvas.pack(pady=10)

        self.bridge_status = tk.Label(self.bridge_frame, text="Bridge: OFF")
        self.bridge_status.pack()

        self.switch_canvas.bind("<Button-1>", lambda event: self.toggle_bridge())

        self.refresh_bridge_status()

    def draw_toggle(self):
        self.switch_canvas.delete("all")
        # vertical rectangular switch body
        if self.bridge_enabled:
            self.switch_canvas.create_rectangle(
                25, 5, 65, 115, fill="green", outline="green"
            )
            # slider at top = ON
            self.switch_canvas.create_rectangle(
                30, 15, 60, 45, fill="white", outline="white"
            )
        else:
            self.switch_canvas.create_rectangle(
                25, 5, 65, 115, fill="red", outline="red"
            )
            # slider at bottom = OFF
            self.switch_canvas.create_rectangle(
                30, 75, 60, 105, fill="white", outline="white"
            )
        self.switch_canvas.create_text(
            45, 125, text="ON" if self.bridge_enabled else "OFF"
        )

    def refresh_bridge_status(self):
        state = get_status()
        self.bridge_enabled = bool(state.get("enabled"))
        self.bridge_status.config(
            text="Online: "
            + str(state.get("online"))
            + " | Enabled: "
            + str(state.get("enabled"))
        )
        self.draw_toggle()

    def bridge_toggle_worker(self, target_state):
        if target_state:
            enable_bridge()
        else:
            disable_bridge()
        self.app.after(500, self.refresh_bridge_status)

    def toggle_bridge(self):
        target = not self.bridge_enabled
        self.bridge_enabled = target
        self.draw_toggle()
        threading.Thread(
            target=self.bridge_toggle_worker, args=(target,), daemon=True
        ).start()


def build(app, right):
    """Build the bridge view; returns the BridgeView instance."""
    return BridgeView(app, right)
