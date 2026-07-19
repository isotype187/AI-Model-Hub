"""Agents view (Phase 9 Step 1): agent registry panel.

Behavior-preserving extraction of the right-column agents Text and its
refresh routine. Uses core.agent_registry.list_agents exactly as before.
"""
import tkinter as tk

from core.agent_registry import list_agents


class AgentsView:
    """Owns the agents Text panel."""

    def __init__(self, right):
        self.agents = tk.Text(right)
        self.agents.pack(fill="both", expand=True)

    def refresh(self):
        self.agents.delete("1.0", tk.END)
        for agent in list_agents():
            self.agents.insert(
                tk.END,
                f"""
{agent['name']}
Type: {agent['type']}
Status: {agent['status']}
Description: {agent['description']}

""",
            )


def build(right):
    """Build the agents view; returns the AgentsView instance."""
    return AgentsView(right)
