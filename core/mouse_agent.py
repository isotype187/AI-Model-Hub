import os
import subprocess
import sys


MOUSE_TOOL = r"D:\Nexus98\tools\mouse_agent\ai_mouse_mode.py"

_process = None


def start_mouse_mode():

    global _process

    if _process and _process.poll() is None:
        return "AI Mouse Mode already running"

    _process = subprocess.Popen(
        [
            sys.executable,
            MOUSE_TOOL
        ],
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )

    return "AI Mouse Mode started"



def stop_mouse_mode():

    global _process

    if _process and _process.poll() is None:

        _process.terminate()
        _process = None

        return "AI Mouse Mode stopped"

    return "AI Mouse Mode not running"



def mouse_status():

    if _process and _process.poll() is None:
        return "RUNNING"

    return "STOPPED"

