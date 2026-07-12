from ui.main_window import launch_ui
import ui.main_window
import traceback

print("MODULE:", ui.main_window.__file__)

try:
    print("CALLING LAUNCH_UI")
    launch_ui()
    print("LAUNCH_UI RETURNED")

except Exception:
    traceback.print_exc()
    input("ERROR - press enter")
