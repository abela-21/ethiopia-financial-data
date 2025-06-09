from flask import current_app
from flask_caching import Cache

# Initialize cache instance that will be configured in app.py
cache = Cache()

def get_cache():
    """Get the cache instance from current app"""
    return current_app.extensions.get('cache', cache)
