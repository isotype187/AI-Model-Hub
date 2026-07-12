from core.hardware import get_specs


def recommend(models):
    specs = get_specs()

    ram = specs['ram_gb']
    vram = specs['vram_mb']

    scored = []

    for m in models:

        base = {
            'ollama': 4,
            'hf': 8,
            'gguf': 6
        }.get(m.get('type'), 5)

        score = ram / base

        if vram < 2000 and m.get('type') == 'gguf':
            score -= 1

        scored.append((score, m))

    scored.sort(reverse=True, key=lambda x: x[0])

    return [m for _, m in scored]
