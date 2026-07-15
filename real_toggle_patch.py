from pathlib import Path

path = Path(r"D:\AI_Model_Hub\ui\main_window.py")

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
    raise Exception("Bridge UI block not found")


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


    bridge_enabled = False


    switch_canvas = tk.Canvas(
        bridge_frame,
        width=90,
        height=50,
        highlightthickness=0
    )

    switch_canvas.pack(
        pady=10
    )


    bridge_status = tk.Label(
        bridge_frame,
        text="Bridge: OFF"
    )

    bridge_status.pack()



    def draw_toggle():

        switch_canvas.delete(
            "all"
        )


        if bridge_enabled:

            switch_canvas.create_rectangle(
                10,
                10,
                80,
                40,
                fill="green",
                outline="green"
            )

            knob_x = 65


        else:

            switch_canvas.create_rectangle(
                10,
                10,
                80,
                40,
                fill="red",
                outline="red"
            )

            knob_x = 25



        switch_canvas.create_oval(
            knob_x-12,
            13,
            knob_x+12,
            37,
            fill="white",
            outline="white"
        )



    def refresh_bridge_status():

        nonlocal bridge_enabled

        state = get_status()

        bridge_enabled = bool(
            state.get("enabled")
        )


        bridge_status.config(
            text=
            "Online: "
            + str(state.get("online"))
            + " | Enabled: "
            + str(state.get("enabled"))
        )


        draw_toggle()



    def bridge_toggle_worker(target_state):

        if target_state:

            enable_bridge()

        else:

            disable_bridge()


        app.after(
            500,
            refresh_bridge_status
        )



    def toggle_bridge():

        nonlocal bridge_enabled

        target = not bridge_enabled

        bridge_enabled = target

        draw_toggle()


        threading.Thread(
            target=bridge_toggle_worker,
            args=(target,),
            daemon=True
        ).start()



    switch_canvas.bind(
        "<Button-1>",
        lambda event: toggle_bridge()
    )


    refresh_bridge_status()


'''

text = text[:start] + replacement + text[end:]


path.write_text(
    text,
    encoding="utf-8"
)

print("Real toggle switch applied")
