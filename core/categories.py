def categorize(model):
    name = model.get('name', '').lower()

    if any(x in name for x in ['code', 'coder', 'deepseek', 'starcoder']):
        return 'CODE'

    if any(x in name for x in ['vision', 'llava', 'clip']):
        return 'VISION'

    if any(x in name for x in ['embed', 'embedding']):
        return 'EMBEDDING'

    return 'CHAT'
