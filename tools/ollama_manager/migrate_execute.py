from pathlib import Path
import subprocess
import time
from datetime import datetime


SOURCE = Path(r"C:\Users\isoty\.ollama\models")
TARGET = Path(r"D:\AI\Models\ollama")
BACKUP_LOG = Path(r"D:\AI_Model_Hub\tools\ollama_manager\migration_log.txt")


def run(cmd):
    print(" ".join(cmd))
    return subprocess.run(cmd, text=True)


def stop_ollama():
    print("[*] Stopping Ollama...")
    subprocess.run(
        [
            "powershell",
            "-Command",
            "Stop-Process -Name ollama -Force -ErrorAction SilentlyContinue"
        ]
    )
    time.sleep(3)


def start_ollama():
    print("[*] Starting Ollama...")
    subprocess.Popen(
        ["ollama", "serve"],
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    time.sleep(8)


def write_log(text):
    BACKUP_LOG.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(BACKUP_LOG, "a", encoding="utf-8") as f:
        f.write(
            f"\n{datetime.now()}\n{text}\n"
        )


def migrate():

    print("=== OLLAMA ROBUST MIGRATION ===")
    print()

    print("SOURCE:")
    print(SOURCE)

    print()
    print("TARGET:")
    print(TARGET)

    print()

    confirm = input(
        "Type MIGRATE to continue: "
    )

    if confirm != "MIGRATE":
        print("Cancelled")
        return


    if not SOURCE.exists():
        print("[ERROR] Source missing")
        return


    TARGET.mkdir(
        parents=True,
        exist_ok=True
    )


    stop_ollama()


    print("[*] Copying models with robocopy...")

    result = run(
        [
            "robocopy",
            str(SOURCE),
            str(TARGET),
            "/E",
            "/COPY:DAT",
            "/DCOPY:DAT",
            "/R:3",
            "/W:5",
            "/MT:16"
        ]
    )


    if result.returncode > 7:
        print("[ERROR] Robocopy failed")
        write_log(
            "FAILED robocopy"
        )
        return


    print("[*] Copy completed")


    print("[*] Creating junction backup link")

    old_parent = SOURCE.parent

    subprocess.run(
        [
            "cmd",
            "/c",
            "rmdir",
            str(SOURCE)
        ]
    )


    subprocess.run(
        [
            "cmd",
            "/c",
            "mklink",
            "/J",
            str(SOURCE),
            str(TARGET)
        ]
    )


    start_ollama()


    print()
    print("[*] Testing Ollama")

    test = subprocess.run(
        [
            "ollama",
            "list"
        ],
        capture_output=True,
        text=True
    )


    print(test.stdout)


    write_log(
        "Migration successful"
    )

    print("[DONE]")


if __name__ == "__main__":
    migrate()
