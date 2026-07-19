"""Models view (Phase 9 Step 1): search + model listbox + inspector.

Behavior-preserving extraction of the original left-column browser and the
center inspector Text. No backend behavior changes: uses the same
core.recommender / core.catalog / core.inspector / core.display calls.
"""
import tkinter as tk

from core.catalog import get_catalog, sync_catalog
from core.inspector import inspect_model
from core.recommender import recommend
from core.display import format_model


class ModelsView:
    """Owns the model browser widgets and selection state."""

    def __init__(self, left, center):
        self.catalog_cache = []
        self.selected_model = None

        # --- left column: search + listbox ---
        self.search_label = tk.Label(left, text="Search Models:")
        self.search_label.pack(padx=10, pady=(10, 0))

        self.search_var = tk.StringVar()
        self.search = tk.Entry(left, textvariable=self.search_var)
        self.search.pack(padx=10, pady=5, fill="x")

        self.listbox = tk.Listbox(left)
        self.listbox.pack(padx=10, pady=10, fill="both", expand=True)

        # --- center column: status + inspector ---
        self.status = tk.Label(center, text="Ready")
        self.status.pack()

        self.inspector = tk.Text(center, height=25)
        self.inspector.pack(fill="both", expand=True)

        self.listbox.bind("<<ListboxSelect>>", self.on_select)

    def refresh(self):
        """Sync catalog, recommend, and repopulate the listbox."""
        sync_catalog()
        self.catalog_cache = recommend(get_catalog())
        self.listbox.delete(0, tk.END)
        for model in self.catalog_cache:
            self.listbox.insert(tk.END, model.get("name", "unknown"))

    def on_select(self, event):
        index = self.listbox.curselection()
        if not index:
            return
        name = self.listbox.get(index[0])
        for model in self.catalog_cache:
            if model["name"] == name:
                self.selected_model = model
                break
        if self.selected_model:
            self.inspector.delete("1.0", tk.END)
            self.inspector.insert(
                tk.END,
                format_model(
                    {
                        **self.selected_model,
                        **inspect_model(self.selected_model),
                    }
                ),
            )


def build(left, center):
    """Build the models view; returns the ModelsView instance."""
    return ModelsView(left, center)
