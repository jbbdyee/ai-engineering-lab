"""A JSON-file memory store shared across workflow runs."""

import json
import os
from pathlib import Path
from typing import Any


def memory_path() -> Path:
    return Path(os.getenv("MINIFLOW_MEMORY_FILE", ".miniflow-memory.json"))


def _load() -> dict[str, Any]:
    path = memory_path()
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read(key: str) -> dict[str, Any]:
    return _load().get(key, {})


def write(key: str, value: dict[str, Any]) -> dict[str, Any]:
    store = _load()
    merged = {**store.get(key, {}), **value}
    store[key] = merged
    memory_path().write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")
    return merged


def clear() -> None:
    memory_path().unlink(missing_ok=True)
