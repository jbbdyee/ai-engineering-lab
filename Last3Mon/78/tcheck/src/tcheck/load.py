"""Read rows (R1) from CSV · JSON files, and the schema (R2) from the data API or a file."""
from __future__ import annotations

import csv
import io
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


class LoadError(Exception):
    """The rows or the schema could not be read (exit code 1)."""


def parse_csv(text: str) -> list[dict]:
    """First line = column names, comma separated (AGENTS.md 3: no quotes needed). Values are trimmed."""
    reader = csv.reader(io.StringIO(text.strip()))
    lines = [line for line in reader if line]
    if not lines:
        return []
    cols = [c.strip() for c in lines[0]]
    return [{cols[i]: v.strip() for i, v in enumerate(line) if i < len(cols)} for line in lines[1:]]


def read_rows(path: str) -> tuple[list[dict], dict]:
    """A .csv file, a JSON list, {"items": [...]}, or a day 78 request {"schema", "batch", "csv" | "items"}.
    Returns (rows, meta) where meta may hold "schema" and "batch"."""
    file = Path(path)
    if not file.exists():
        raise LoadError(f"no such file: {path}")
    text = file.read_text(encoding="utf-8")
    if file.suffix.lower() == ".csv":
        return parse_csv(text), {"batch": file.stem}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise LoadError(f"not CSV or JSON: {path} ({error.msg})") from error
    if isinstance(data, list):
        return data, {"batch": file.stem}
    if isinstance(data, dict):
        meta = {k: data[k] for k in ("schema", "batch") if k in data}
        meta.setdefault("batch", file.stem)
        if isinstance(data.get("csv"), str):
            return parse_csv(data["csv"]), meta
        if isinstance(data.get("items"), list):
            return data["items"], meta
    raise LoadError(f"expected a list of rows, {{\"items\": [...]}} or {{\"csv\": \"...\"}}: {path}")


def http_json(url: str, body: dict | None = None, timeout: float = 10) -> object:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as answer:
        return json.loads(answer.read())


def read_schema(name: str = "", url: str | None = None, file: str | None = None) -> dict:
    """--schema-file wins over the data API ($TCHECK_URL may be set for every call)."""
    if file:
        try:
            schema = json.loads(Path(file).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise LoadError(f"cannot read schema file {file}: {error}") from error
    elif url and name:
        try:
            schema = http_json(url.rstrip("/") + "/schemas/" + urllib.parse.quote(name))
        except urllib.error.HTTPError as error:
            raise LoadError(f"unknown schema '{name}' (data API {error.code})") from error
        except (urllib.error.URLError, OSError, json.JSONDecodeError) as error:
            raise LoadError(f"data API {url}: {error}") from error
    else:
        raise LoadError("no schema: give --schema NAME with --url (or $TCHECK_URL), or --schema-file")
    if not isinstance(schema, dict) or not isinstance(schema.get("fields"), dict):
        raise LoadError("the schema has no 'fields'")
    return schema


def post_log(url: str, entry: dict) -> dict:
    """R10: one line in the data API quality log (POST /quality-log)."""
    try:
        return http_json(url.rstrip("/") + "/quality-log", entry)
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as error:
        raise LoadError(f"data API {url}: {error}") from error
