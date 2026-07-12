import time

_catalog_cache = None
_last_sync = 0
CACHE_TTL = 30  # seconds


def get_cache():
    global _catalog_cache
    return _catalog_cache


def set_cache(data):
    global _catalog_cache, _last_sync
    _catalog_cache = data
    _last_sync = time.time()


def is_stale():
    return (time.time() - _last_sync) > CACHE_TTL
