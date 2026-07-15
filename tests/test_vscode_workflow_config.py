import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config" / "vscode_workflow.json"


def test_vscode_workflow_config_contains_desktop_and_laptop_roles():
    assert CONFIG_PATH.exists(), "Expected workspace config file for VS Code workflow automation"

    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    assert "roles" in data
    assert "desktop" in data["roles"]
    assert "laptop" in data["roles"]

    desktop = data["roles"]["desktop"]
    laptop = data["roles"]["laptop"]

    assert desktop["extensions"]
    assert laptop["extensions"]
    assert desktop["machineName"]
    assert laptop["machineName"]
