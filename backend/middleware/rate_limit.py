"""Rate limiting middleware — in-memory sliding window for V1."""
import time
from functools import wraps
from flask import request, jsonify

# In-memory store: { ip_key: [timestamp, timestamp, ...] }
_store = {}

# Config: endpoint_prefix -> (max_requests, window_seconds)
LIMITS = {
    'auth': (10, 60),       # 10 requests per 60 seconds on auth endpoints
    'copilot': (20, 60),    # 20 requests per 60 seconds on AI endpoints
    'default': (60, 60),    # 60 requests per 60 seconds for everything else
}


def _get_key(prefix):
    """Generate a rate limit key from IP + endpoint prefix."""
    ip = request.remote_addr or '0.0.0.0'
    return f"{ip}:{prefix}"


def _clean_old(timestamps, window):
    """Remove timestamps outside the sliding window."""
    cutoff = time.time() - window
    return [t for t in timestamps if t > cutoff]


def rate_limit(prefix='default'):
    """Decorator to apply rate limiting to a route."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            max_req, window = LIMITS.get(prefix, LIMITS['default'])
            key = _get_key(prefix)

            now = time.time()
            timestamps = _store.get(key, [])
            timestamps = _clean_old(timestamps, window)

            if len(timestamps) >= max_req:
                retry_after = int(window - (now - timestamps[0]))
                return jsonify({
                    'error': 'Too many requests. Please slow down.',
                    'retryAfter': max(retry_after, 1)
                }), 429

            timestamps.append(now)
            _store[key] = timestamps

            return f(*args, **kwargs)
        return wrapper
    return decorator
