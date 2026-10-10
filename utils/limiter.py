import os

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Single limiter shared by the app and all route modules (initialised in app.py).
# Pages fire several API calls each, so the default must allow normal browsing.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[os.environ.get("RATELIMIT_DEFAULT", "1000 per hour")],
    storage_uri=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"),
)
