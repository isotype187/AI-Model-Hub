import traceback
from datetime import datetime
from pathlib import Path


LOG = Path(r"D:\Nexus98\logs\startup_crash.log")


def write_log(message):

    LOG.parent.mkdir(
        exist_ok=True
    )

    with open(
        LOG,
        "a",
        encoding="utf-8"
    ) as f:

        f.write(
            "\n\n============================\n"
        )

        f.write(
            datetime.now().isoformat()
        )

        f.write(
            "\n"
        )

        f.write(
            message
        )



def main():

    try:

        print("Starting AI Model Hub...")

        from ui.main_window import launch_ui

        launch_ui()


    except Exception:

        error = traceback.format_exc()

        print(error)

        write_log(error)

        input(
            "\nCRASH DETECTED. Press Enter to close..."
        )



if __name__ == "__main__":

    main()

