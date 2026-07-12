import time
import threading
import math

from pynput import mouse, keyboard
from pynput.keyboard import Key, Controller

import pystray
from PIL import Image, ImageDraw


# =========================
# SETTINGS
# =========================

HOLD_TIME = 0.30
MOVE_DISTANCE = 10
PASTE_DELAY = 0.15


enabled = True

kb = Controller()

mouse_down_time = 0
mouse_start = None


# =========================
# TRAY
# =========================

tray_icon = None


def make_icon(color):

    image = Image.new(
        "RGB",
        (64, 64),
        "black"
    )

    draw = ImageDraw.Draw(image)

    draw.ellipse(
        (16, 16, 48, 48),
        fill=color
    )

    return image



def update_icon():

    if tray_icon:

        tray_icon.icon = make_icon(
            "green" if enabled else "red"
        )



def toggle():

    global enabled

    enabled = not enabled

    update_icon()



def tray():

    global tray_icon

    tray_icon = pystray.Icon(
        "AI Mouse Mode",
        make_icon("green"),
        "AI Mouse Mode",
        pystray.Menu(
            pystray.MenuItem(
                "Toggle",
                lambda: toggle()
            ),
            pystray.MenuItem(
                "Exit",
                lambda: tray_icon.stop()
            )
        )
    )

    tray_icon.run()



# =========================
# HOTKEY
# =========================

def hotkey_listener():

    with keyboard.GlobalHotKeys(
        {
            "<ctrl>+<alt>+<space>": toggle
        }
    ) as h:

        h.join()



# =========================
# ACTIONS
# =========================

def moved_enough(a,b):

    if not a or not b:
        return False

    return math.sqrt(
        (b[0]-a[0]) ** 2 +
        (b[1]-a[1]) ** 2
    ) >= MOVE_DISTANCE



def copy_selection():

    kb.press(Key.ctrl)
    kb.press("c")

    kb.release("c")
    kb.release(Key.ctrl)



def paste_execute():

    kb.press(Key.ctrl)
    kb.press("v")

    kb.release("v")
    kb.release(Key.ctrl)


    time.sleep(
        PASTE_DELAY
    )


    kb.press(Key.enter)
    kb.release(Key.enter)



# =========================
# MOUSE HOOK
# =========================

def on_click(x,y,button,pressed):

    global mouse_down_time
    global mouse_start


    if button == mouse.Button.left:

        if pressed:

            mouse_down_time = time.time()
            mouse_start = (x,y)


        else:

            if not enabled:
                return


            held = time.time() - mouse_down_time


            if (
                held >= HOLD_TIME
                and moved_enough(
                    mouse_start,
                    (x,y)
                )
            ):

                time.sleep(0.1)

                copy_selection()



    elif button == mouse.Button.middle:

        if enabled and pressed:

            paste_execute()

            # suppress middle click
            return False



# =========================
# START
# =========================

if __name__ == "__main__":


    threading.Thread(
        target=tray,
        daemon=True
    ).start()


    threading.Thread(
        target=hotkey_listener,
        daemon=True
    ).start()


    with mouse.Listener(
        on_click=on_click,
        suppress=False
    ) as listener:

        listener.join()

