_search_index = {}


def build_index(models):
    global _search_index
    _search_index = {}

    for m in models:
        name = m.get('name', '').lower()

        for word in name.split():
            _search_index.setdefault(word, []).append(m)


def search(query, models):
    if not query:
        return models

    q = query.lower()

    results = []

    for m in models:
        if q in m.get('name', '').lower():
            results.append(m)

    return results
