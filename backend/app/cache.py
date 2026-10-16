"""Tiny on-disk JSON cache keyed by image hash + model + prompt version."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .config import settings
from .prompts import PROMPT_VERSION


def image_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _path(key: str):
    safe = hashlib.sha256(f"{key}|{settings.model}|{PROMPT_VERSION}".encode()).hexdigest()
    return settings.cache_dir / f"{safe}.json"


def get(key: str) -> dict[str, Any] | None:
    p = _path(key)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def put(key: str, value: dict[str, Any]) -> None:
    settings.cache_dir.mkdir(parents=True, exist_ok=True)
    _path(key).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
