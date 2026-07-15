from pathlib import Path

path = Path(r"D:\AI_Model_Hub\ui\main_window.py")

text = path.read_text(encoding="utf-8")


start = text.find(
"""    def draw_toggle():"""
)

end = text.find(
"""    def refresh_bridge_status():""",
start
)

if start == -1 or end == -1:
    raise Exception("draw_toggle block not found")


replacement = r'''
    def draw_toggle():

        switch_canvas.delete(
            "all"
        )


        # vertical rectangular switch body

        if bridge_enabled:

            switch_canvas.create_rectangle(
                25,
                5,
                65,
                115,
                fill="green",
                outline="green"
            )

            # slider at top = ON

            switch_canvas.create_rectangle(
                30,
                15,
                60,
                45,
                fill="white",
                outline="white"
            )


        else:

            switch_canvas.create_rectangle(
                25,
                5,
                65,
                115,
                fill="red",
                outline="red"
            )

            # slider at bottom = OFF

            switch_canvas.create_rectangle(
                30,
                75,
                60,
                105,
                fill="white",
                outline="white"
            )


        switch_canvas.create_text(
            45,
            125,
            text="ON" if bridge_enabled else "OFF"
        )


'''

text = text[:start] + replacement + text[end:]


# enlarge canvas for vertical switch

text = text.replace(
"""width=90,
        height=50""",
"""width=90,
        height=150"""
)


path.write_text(
    text,
    encoding="utf-8"
)

print("Vertical rectangular switch applied")
