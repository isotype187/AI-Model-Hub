import subprocess
import os

BASE = os.path.dirname(__file__)

subprocess.call([
    "python","-m","PyInstaller",
    "--noconfirm","--onefile","--windowed",
    os.path.join(BASE,"main.py")
])
