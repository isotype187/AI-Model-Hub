import tkinter as tk
import traceback

from core.agent_registry import list_agents

app = tk.Tk()
app.title("Agent Test")
app.geometry("500x300")

print("BEFORE AGENTS")

try:
    agents = list_agents()
    print("AGENTS RESULT:")
    print(agents)

except Exception:
    traceback.print_exc()

print("START LOOP")
app.mainloop()
