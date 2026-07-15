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


    bridge_on = False


    bridge_status = tk.Label(
        bridge_frame,
        text="Bridge: OFF"
    )

    bridge_status.pack(
        pady=5
    )


    def update_bridge_button():

        if bridge_on:

            bridge_toggle.config(
                text="  ON  ",
                bg="green",
                fg="white"
            )

        else:

            bridge_toggle.config(
                text=" OFF ",
                bg="red",
                fg="white"
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

        update_bridge_button()



    def bridge_action():

        if bridge_on:

            disable_bridge()

        else:

            enable_bridge()


        app.after(
            500,
            refresh_bridge_status
        )



    bridge_toggle = tk.Button(
        bridge_frame,
        text="OFF",
        width=10,
        height=2,
        command=bridge_action,
        relief="raised",
        font=("Segoe UI", 12, "bold")
    )

    bridge_toggle.pack(
        pady=10
    )


    refresh_bridge_status()


'''

text = text[:start] + replacement + text[end:]


path.write_text(
    text,
    encoding="utf-8"
)

print("Clean bridge toggle applied")
