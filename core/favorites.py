import os
import json

FAV_PATH = r'D:\AI_Model_Hub\data\favorites.json'


def load_favorites():
    if not os.path.exists(FAV_PATH):
        return []

    with open(FAV_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_favorites(data):
    os.makedirs(os.path.dirname(FAV_PATH), exist_ok=True)

    with open(FAV_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def toggle_favorite(model):
    favs = load_favorites()

    mid = model.get('id')

    if mid in favs:
        favs.remove(mid)
    else:
        favs.append(mid)

    save_favorites(favs)
    return favs
