import subprocess
import time
from pathlib import Path

import requests
import psutil


BRIDGE_URL = "http://127.0.0.1:8765"

BRIDGE_PYTHON = r"D:\AI\Nexus98_Bridge\.venv\Scripts\python.exe"

BRIDGE_SCRIPT = r"D:\AI\Nexus98_Bridge\bridge_server.py"


_bridge_process = None



def get_status():

    try:

        response = requests.get(
            f"{BRIDGE_URL}/status",
            timeout=3
        )

        return response.json()

    except Exception:

        return {
            "online": False,
            "enabled": False
        }



def find_bridge_processes():

    processes = []

    for proc in psutil.process_iter(
        ["pid", "cmdline"]
    ):

        try:

            cmd = " ".join(
                proc.info["cmdline"] or []
            )

            if "bridge_server.py" in cmd:

                processes.append(
                    proc
                )

        except Exception:

            pass

    return processes



def start_bridge():

    if get_status().get("online"):

        return get_status()


    subprocess.Popen(
        [
            BRIDGE_PYTHON,
            BRIDGE_SCRIPT
        ],
        cwd=str(Path(BRIDGE_SCRIPT).parent)
    )


    for _ in range(10):

        time.sleep(1)

        if get_status().get("online"):

            return get_status()


    return get_status()



def enable_bridge():

    start_bridge()

    try:

        response = requests.post(
            f"{BRIDGE_URL}/enable",
            timeout=3
        )

        time.sleep(1)

        return response.json()


    except Exception as e:

        return {
            "error": str(e)
        }



def disable_bridge():

    try:

        requests.post(
            f"{BRIDGE_URL}/disable",
            timeout=3
        )

    except Exception:

        pass


    time.sleep(1)


    for proc in find_bridge_processes():

        try:

            proc.terminate()

            proc.wait(
                timeout=5
            )

        except Exception:

            try:

                proc.kill()

            except Exception:

                pass


    time.sleep(1)

    return get_status()
