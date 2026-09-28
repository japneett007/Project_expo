"""Utility helpers for JSON data file operations and validation."""
import json
import os
import uuid
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'data')
DATA_DIR = os.path.abspath(DATA_DIR)


def _safe_path(filename):
    """Resolve filepath and verify it stays within DATA_DIR (path traversal prevention)."""
    filepath = os.path.normpath(os.path.join(DATA_DIR, filename))
    if not filepath.startswith(DATA_DIR):
        raise ValueError(f"Path traversal blocked: {filename}")
    return filepath


def read_json(filename):
    """Read a JSON data file and return its contents."""
    filepath = _safe_path(filename)
    if not os.path.exists(filepath):
        return [] if filename.endswith('.json') else {}
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json(filename, data):
    """Write data to a JSON file."""
    filepath = _safe_path(filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def generate_id():
    """Generate a unique UUID4 identifier."""
    return str(uuid.uuid4())


def now_iso():
    """Return current UTC timestamp in ISO format."""
    return datetime.utcnow().isoformat() + 'Z'


def sanitize_string(value):
    """Basic input sanitization — strip HTML tags and trim whitespace."""
    if not isinstance(value, str):
        return value
    import re
    clean = re.sub(r'<[^>]+>', '', value)  # Strip HTML tags
    return clean.strip()


def validate_email(email):
    """Basic email format validation."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def get_user_level(xp, xp_rules=None):
    """Calculate user level from XP based on xp_rules.json."""
    if xp_rules is None:
        xp_rules = read_json('xp_rules.json')
    levels = xp_rules.get('levels', [])
    current_level = levels[0] if levels else {"level": 1, "name": "Explorer"}
    for lvl in levels:
        if xp >= lvl['minXP']:
            current_level = lvl
    return current_level
