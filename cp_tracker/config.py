"""Configuration and disk cache handling."""

import json
import time
from pathlib import Path

CONFIG_DIR = Path.home() / ".cp_tracker"
CONFIG_FILE = CONFIG_DIR / "config.json"
CACHE_FILE = CONFIG_DIR / "cache.json"

DEFAULT_HANDLES = {"codeforces": "", "leetcode": "", "codechef": ""}

CACHE_TTL = {  # seconds before we consider a cached block stale
    "codeforces": 15 * 60,
    "leetcode": 30 * 60,
    "codechef": 60 * 60,
    "contests": 10 * 60,
}

PLATFORM_LABEL = {
    "codeforces": "Codeforces",
    "leetcode": "LeetCode",
    "codechef": "CodeChef",
}

LABEL_TO_KEY = {v.lower(): k for k, v in PLATFORM_LABEL.items()}


def _read_json(path: Path, default):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        pass
    return default


def _write_json(path: Path, data):
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, default=str))
    except OSError:
        pass


def load_config() -> dict:
    cfg = _read_json(CONFIG_FILE, {})
    cfg = {**DEFAULT_HANDLES, **cfg}
    if not CONFIG_FILE.exists():
        _write_json(CONFIG_FILE, cfg)
    return cfg


def save_config(cfg: dict) -> dict:
    cfg = {**DEFAULT_HANDLES, **{k: (v or "") for k, v in cfg.items()}}
    _write_json(CONFIG_FILE, cfg)
    return cfg


def load_cache() -> dict:
    return _read_json(CACHE_FILE, {})


def save_cache_block(key: str, payload):
    cache = load_cache()
    cache[key] = {"fetched_at": time.time(), "data": payload}
    _write_json(CACHE_FILE, cache)


def cached_block(key: str):
    cache = load_cache()
    entry = cache.get(key) or {}
    fetched = entry.get("fetched_at") or 0
    if time.time() - fetched > CACHE_TTL.get(key, 600):
        return None
    return entry.get("data")