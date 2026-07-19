############################################################
# Model Installer
#
# Responsibility:
# Installs approved AI models and components.
#
# Inputs:
# Installation requests.
#
# Outputs:
# Installed model state.
#
# Dependencies:
# Provider download systems.
#
# Never:
# Makes autonomous installation decisions.
############################################################

import os
import threading
import subprocess
from huggingface_hub import snapshot_download

HF_DIR = r'D:\Nexus98\data\models\hf'

def install_ollama(model_id, callback=None):
    subprocess.Popen(f'ollama pull {model_id}', shell=True)
    if callback: callback(f'Ollama started: {model_id}')

def install_hf(model_id, callback=None):
    def run():
        try:
            target = os.path.join(HF_DIR, model_id.replace('/', '_'))
            snapshot_download(repo_id=model_id, local_dir=target, local_dir_use_symlinks=False)
            if callback: callback(f'Installed HF: {model_id}')
        except Exception as e:
            if callback: callback(str(e))
    threading.Thread(target=run, daemon=True).start()

def install_model(model, callback=None):
    if model.get('type') == 'ollama':
        install_ollama(model['id'], callback)
    elif model.get('type') == 'hf':
        install_hf(model['id'], callback)


