"""Load settings from the nearest .env file (KEY=VALUE lines, no extra package needed).

Search order: the current folder and its parents, then the folders above this package
(so one Last3Mon/.env serves every day). Only the nearest file is read, and variables
already set in the shell win. Set MINIFLOW_DOTENV=0 to skip (the tests do this).
The .env file holds API keys: it is listed in .gitignore and must never be committed.
"""

import os
from pathlib import Path

LOADED: list[str] = []  # the .env file that was read, if any


def parse(text: str) -> dict[str, str]:
    values = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.removeprefix("export ").strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        elif " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        values[key] = value
    return values


def candidates() -> list[Path]:
    paths: list[Path] = []
    for start in (Path.cwd(), Path(__file__).resolve().parent):
        for folder in (start, *start.parents):
            if folder / ".env" not in paths:
                paths.append(folder / ".env")
    return paths


def load() -> Path | None:
    if os.getenv("MINIFLOW_DOTENV", "1") == "0":
        return None
    for path in candidates():
        if path.is_file():
            for key, value in parse(path.read_text(encoding="utf-8")).items():
                os.environ.setdefault(key, value)
            LOADED.append(str(path))
            return path
    return None
