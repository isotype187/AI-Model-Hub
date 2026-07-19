from pathlib import Path
import threading

path = Path(r"D:\Nexus98\ui\main_window.py")

text = path.read_text(encoding="utf-8")


start = text.find(
"""    bridge_frame = tk.LabelFrame(
        right,
        text="Bridge Control"
    )"""
)


end = text.find(
"""    def refresh_agents():""",
    start
)


if start == -1 or end == -1:
    raise Exception("Bridge UI section not found")


replacement = r'''
    bridge_frame = tk.LabelFrame(
        right,
        text="Bridge Control"
    )

    bridge_frame.pack(
        fill="x",
        padx=10,
        pady=10
    )


    switch_canvas = tk.Canvas(
        bridge_frame,
        width=100,
        height=220,
        highlightthickness=0
    )

    switch_canvas.pack(
        pady=10
    )


    bridge_on = False


    bridge_status = tk.Label(
        bridge_frame,
        text="Bridge: OFF"
    )

    bridge_status.pack()


    def draw_switch():

        switch_canvas.delete(
            "all"
        )


        # track

        switch_canvas.create_round_rectangle = None


        switch_canvas.create_rectangle(
            35,
            35,
            65,
            185,
            width=3
        )


        if bridge_on:

            knob_y = 60
            label = "ON"

        else:

            knob_y = 160
            label = "OFF"



        switch_canvas.create_oval(
            20,
            knob_y-20,
            80,
            knob_y+20,
            width=3
        )


        switch_canvas.create_text(
            50,
            15,
            text=label
        )


    def update_status():

        nonlocal bridge_on


        state = get_status()

        bridge_on = bool(
            state.get("enabled")
        )

        bridge_status.config(
            text=
            "Online: "
            + str(state.get("online"))
            + " | Enabled: "
            + str(state.get("enabled"))
        )

        draw_switch()



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



    switch_canvas.bind(
        "<Button-1>",
        toggle_switch
    )


    update_status()


'''

text = text[:start] + replacement + text[end:]

path.write_text(
    text,
    encoding="utf-8"
)

print("Fast vertical switch applied")

