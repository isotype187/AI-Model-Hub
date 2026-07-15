from pathlib import Path

path = Path(r"D:\AI_Model_Hub\ui\main_window.py")

text = path.read_text(encoding="utf-8")


text = text.replace(
    "from core.agent_registry import list_agents",
    "from core.agent_registry import list_agents\nfrom core.bridge_controller import get_status, enable_bridge, disable_bridge",
    1
)


marker = """    agents.pack(
        fill="both",
        expand=True
    )
"""


insert = """

    bridge_frame = tk.LabelFrame(
        right,
        text="Bridge Control"
    )

    bridge_frame.pack(
        fill="x",
        padx=10,
        pady=10
    )


    bridge_status = tk.Label(
        bridge_frame,
        text="Bridge: Unknown"
    )

    bridge_status.pack()


    def refresh_bridge_status():

        state = get_status()

        bridge_status.config(
            text="Online: " + str(state.get("online")) +
                 " | Enabled: " + str(state.get("enabled"))
        )


    tk.Button(
        bridge_frame,
        text="Enable Bridge",
        command=lambda: (
            enable_bridge(),
            refresh_bridge_status()
        )
    ).pack(fill="x")


    tk.Button(
        bridge_frame,
        text="Disable Bridge",
        command=lambda: (
            disable_bridge(),
            refresh_bridge_status()
        )
    ).pack(fill="x")


    tk.Button(
        bridge_frame,
        text="Refresh Bridge",
        command=refresh_bridge_status
    ).pack(fill="x")

"""


if "Bridge Control" not in text:

    if marker not in text:
        raise Exception("UI insertion point missing")

    text = text.replace(
        marker,
        marker + insert,
        1
    )


path.write_text(
    text,
    encoding="utf-8"
)

print("Bridge UI patch applied")
