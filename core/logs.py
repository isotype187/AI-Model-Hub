import os
from datetime import datetime

LOG_DIR = r'D:\Nexus98\logs'
os.makedirs(LOG_DIR, exist_ok=True)


def write_log(msg):
    path = os.path.join(LOG_DIR, 'install.log')

    with open(path, 'a', encoding='utf-8') as f:
        f.write(f'[{datetime.now()}] {msg}\n')


def read_logs():
    path = os.path.join(LOG_DIR, 'install.log')

    if not os.path.exists(path):
        return []

    with open(path, 'r', encoding='utf-8') as f:
        return f.readlines()

