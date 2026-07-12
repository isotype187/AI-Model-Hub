import tkinter as tk
import traceback

from core.catalog import get_catalog, sync_catalog
from core.recommender import recommend
from core.agent_registry import list_agents

app = tk.Tk()
app.title("Full Refresh Test")
app.geometry("700x500")

print("WINDOW CREATED")

try:
    print("SYNC")
    sync_catalog()

    print("GET")
    data = get_catalog()

    print("RECOMMEND")
    models = recommend(data)

    print("AGENTS")
    agents = list_agents()

    print("ALL OK")
    print("Models:", len(models))
    print("Agents:", len(agents))

except Exception:
    traceback.print_exc()

print("ENTERING LOOP")
app.mainloop()

print("LOOP ENDED")
