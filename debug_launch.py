from ui.main_window import launch_ui
import traceback

print("TEST START")

try:
    launch_ui()

except Exception:
    traceback.print_exc()
    input("ERROR SHOWN - press enter")
