import os
import subprocess

HF_DIR = r'D:\Nexus98\data\models\hf'
_installed = set()

def is_installed(model):
    try:
        if model.get('type') == 'ollama':
            out = subprocess.check_output('ollama list', shell=True).decode()
            return model['id'] in out
        if model.get('type') == 'hf':
            path = os.path.join(HF_DIR, model['id'].replace('/', '_'))
            return os.path.exists(path)
        return False
    except:
        return False

def mark_installed(model):
    try:
        _installed.add(model.get('id'))
    except:
        pass

