import os
import sys

APP_NAME = 'AI_Model_Hub'

STARTUP_PATH = os.path.join(
    os.environ['APPDATA'],
    r'Microsoft\Windows\Start Menu\Programs\Startup',
    f'{APP_NAME}.bat'
)


def enable_autostart():
    python_path = sys.executable
    script = os.path.join(os.path.dirname(__file__), '..', 'main.py')

    content = f'@echo off\n\"{python_path}\" \"{script}\"\n'

    with open(STARTUP_PATH, 'w') as f:
        f.write(content)


def disable_autostart():
    if os.path.exists(STARTUP_PATH):
        os.remove(STARTUP_PATH)
