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


    bridge_state = tk.BooleanVar(
        value=False
    )


    bridge_status = tk.Label(
        bridge_frame,
        text="Bridge: Unknown"
    )

    bridge_status.pack(
        pady=5
    )


    def refresh_bridge_status():

        state = get_status()

        online = state.get(
            "online",
            False
        )

        enabled = state.get(
            "enabled",
            False
        )

        bridge_state.set(
            enabled
        )

        bridge_status.config(
            text=
            "Online: "
            + str(online)
            + " | Enabled: "
            + str(enabled)
        )


    def toggle_bridge():

        if bridge_state.get():

            disable_bridge()

        else:

            enable_bridge()


        app.after(
            1500,
            refresh_bridge_status
        )


    bridge_toggle = tk.Checkbutton(
        bridge_frame,
        text="Bridge Enabled",
        variable=bridge_state,
        command=toggle_bridge,
        indicatoron=True
    )

    bridge_toggle.pack(
        pady=5
    )


    tk.Button(
        bridge_frame,
        text="Refresh Bridge",
        command=refresh_bridge_status
    ).pack(
        fill="x"
    )


'''

text = text[:start] + replacement + text[end:]


path.write_text(
    text,
    encoding="utf-8"
)

print("Bridge toggle UI applied")
