import hashlib
import json
import time
from pathlib import Path
from typing import Any

CACHE_DIR = Path(".cache")
TTL = 3600  # 1 hour


def _path(url: str) -> Path:
    key = hashlib.md5(url.encode()).hexdigest()
    return CACHE_DIR / f"{key}.json"


def get(url: str) -> Any | None:
    path = _path(url)
    if not path.exists():
        return None
    entry = json.loads(path.read_text())
    if time.time() - entry["timestamp"] > TTL:
        return None
    return entry["data"]


def set(url: str, data: Any) -> None:
    CACHE_DIR.mkdir(exist_ok=True)
    _path(url).write_text(json.dumps({"timestamp": time.time(), "data": data}))
