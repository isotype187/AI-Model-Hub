import threading
import pystray
from PIL import Image, ImageDraw
import sys


def create_image():
    img = Image.new('RGB', (64, 64), color=(20, 20, 20))
    d = ImageDraw.Draw(img)
    d.rectangle([16, 16, 48, 48], fill=(80, 160, 255))
    return img


def run_tray(on_exit=None):
    def quit_app(icon, item):
        icon.stop()
        if on_exit:
            on_exit()
        sys.exit()

    icon = pystray.Icon(
        'AI_Model_Hub',
        create_image(),
        'AI Model Hub',
        menu=pystray.Menu(
            pystray.MenuItem('Exit', quit_app)
        )
    )

    icon.run()
