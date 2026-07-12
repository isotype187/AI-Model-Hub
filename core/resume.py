import os
import json

PATH = r'D:\AI_Model_Hub\data\resume.json'


def save_state(model_id, progress):
    os.makedirs(os.path.dirname(PATH), exist_ok=True)

    data = load_state()
    data[model_id] = progress

    with open(PATH, 'w') as f:
        json.dump(data, f)


def load_state():
    if not os.path.exists(PATH):
        return {}

    with open(PATH, 'r') as f:
        return json.load(f)
