import os
from pathlib import Path


ROOT = Path(r"D:\Nexus98")


IGNORED_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "backups",
    "backup",
    "data",
    "logs",
    "snapshots",
    "archive",
    "archives",
    "rollback",
    "old",
    "temp",
    "tmp",
    "node_modules",
    "site-packages",
    "Packages",
    "models",
    "ollama",
}


INCLUDED_EXTENSIONS = {
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".env",
    ".ps1",
    ".py",
    ".md",
    ".txt",
}


MAX_RESULTS = 100


def list_files() -> str:
    """
    List important project files inside AI_Model_Hub.
    Returns a limited workspace inventory.
    """

    files = []

    for root, dirs, filenames in os.walk(ROOT, topdown=True):
        dirs[:] = [
            d for d in dirs
            if d not in IGNORED_DIRS
        ]

        root_path = Path(root)
        rel_root = root_path.relative_to(ROOT)

        for filename in sorted(filenames):
            target = rel_root / filename

            if any(
                part in IGNORED_DIRS
                for part in target.parts
            ):
                continue

            if target.suffix.lower() not in INCLUDED_EXTENSIONS:
                continue

            files.append(str(target))

            if len(files) >= MAX_RESULTS:
                return "\n".join(files)

    return "\n".join(files)


def read_file(path: str) -> str:
    """
    Read a text file from the AI_Model_Hub workspace.

    Args:
        path:
            Relative path from D:\\AI_Model_Hub
    """

    target = ROOT / path

    if any(
        part in IGNORED_DIRS
        for part in target.parts
    ):
        return f"Path ignored: {path}"

    if not target.exists():
        return f"File not found: {path}"

    if not target.is_file():
        return f"Not a file: {path}"

    size = target.stat().st_size

    if size > 50000:
        return f"File too large: {size} bytes"

    try:
        return target.read_text(
            encoding="utf-8",
            errors="ignore"
        )
    except Exception as e:
        return f"Read error: {e}"


