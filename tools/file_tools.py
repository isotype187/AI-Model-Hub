from pathlib import Path


ROOT = Path(r"D:\AI_Model_Hub")


IGNORED = {
    ".git",
    ".venv",
    "__pycache__",
    "backups",
    "data",
    "logs"
}



def list_files() -> str:
    """
    List important project files inside AI_Model_Hub.
    Returns a limited workspace inventory.
    """

    files = []


    for path in ROOT.rglob("*"):

        if any(
            part in IGNORED
            for part in path.parts
        ):
            continue


        if path.is_file():

            files.append(
                str(
                    path.relative_to(ROOT)
                )
            )


        if len(files) >= 100:

            break


    return "\n".join(files)



def read_file(path: str) -> str:
    """
    Read a text file from the AI_Model_Hub workspace.

    Args:
        path:
            Relative path from D:\\AI_Model_Hub
    """

    target = ROOT / path


    if not target.exists():

        return (
            f"File not found: {path}"
        )


    if not target.is_file():

        return (
            f"Not a file: {path}"
        )


    size = target.stat().st_size


    if size > 50000:

        return (
            f"File too large: {size} bytes"
        )


    try:

        return target.read_text(
            encoding="utf-8",
            errors="ignore"
        )

    except Exception as e:

        return (
            f"Read error: {e}"
        )

