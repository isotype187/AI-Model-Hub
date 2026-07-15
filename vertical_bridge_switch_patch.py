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


    bridge_canvas = tk.Canvas(
        bridge_frame,
        width=80,
        height=180
    )

    bridge_canvas.pack(
        pady=10
    )


    bridge_on = False


    bridge_status = tk.Label(
        bridge_frame,
        text="Bridge: OFF"
    )

    bridge_status.pack()


    def draw_bridge_switch():

        bridge_canvas.delete(
            "all"
        )

        bridge_canvas.create_rectangle(
            25,
            20,
            55,
            160,
            width=2
        )

        if bridge_on:

            bridge_canvas.create_oval(
                20,
                30,
                60,
                70,
                width=2
            )

            bridge_canvas.create_text(
                40,
                10,
                text="ON"
            )

        else:

            bridge_canvas.create_oval(
                20,
                110,
                60,
                150,
                width=2
            )

            bridge_canvas.create_text(
                40,
                170,
                text="OFF"
            )


    def refresh_bridge_status():

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

        draw_bridge_switch()



    def toggle_bridge(event=None):

        nonlocal bridge_on


        if bridge_on:

            disable_bridge()

        else:

            enable_bridge()


        app.after(
            1500,
            refresh_bridge_status
        )



    bridge_canvas.bind(
        "<Button-1>",
        toggle_bridge
    )


    refresh_bridge_status()


'''

text = text[:start] + replacement + text[end:]


path.write_text(
    text,
    encoding="utf-8"
)

print("Vertical bridge switch applied")
