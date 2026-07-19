from pathlib import Path

path = Path(r"D:\Nexus98\ui\main_window.py")

text = path.read_text(encoding="utf-8")

old = """
    def switch_worker():

        if bridge_on:

            disable_bridge()

        else:

            enable_bridge()


        app.after(
            100,
            update_status
        )



    def toggle_switch(event=None):

        nonlocal bridge_on


        bridge_on = not bridge_on

        draw_switch()


        threading.Thread(
            target=switch_worker,
            daemon=True
        ).start()
"""

new = """
    def switch_worker(turn_on):

        if turn_on:

            enable_bridge()

        else:

            disable_bridge()


        app.after(
            500,
            update_status
        )



    def toggle_switch(event=None):

        nonlocal bridge_on

        requested_state = not bridge_on

        bridge_on = requested_state

        draw_switch()


        threading.Thread(
            target=switch_worker,
            args=(requested_state,),
            daemon=True
        ).start()
"""


if old not in text:
    raise Exception("Switch function block not found")

text = text.replace(
    old,
    new,
    1
)

path.write_text(
    text,
    encoding="utf-8"
)

print("Switch logic fixed")

