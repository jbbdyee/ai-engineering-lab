"""Read run logs (R1) from a file or the data API, and other log shapes into the same run shape (R9)."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path


class LoadError(Exception):
    """The logs could not be read (exit code 1)."""


def keep(row: dict, date_from: str = "", date_to: str = "", tag: str = "", source: str = "all") -> bool:
    """Dates are inclusive: from <= started_at[:10] <= to. Empty means no limit (AGENTS.md 3)."""
    day = str(row.get("started_at", ""))[:10]
    if date_from and day < date_from:
        return False
    if date_to and day > date_to:
        return False
    if tag and row.get("tag") != tag:
        return False
    if source != "all" and row.get("source", "seed") != source:
        return False
    return True


def from_tretry(rows: list[dict]) -> list[dict]:
    """R9: day 76 tretry attempt rows -> one run row per tretry call, in the run shape of AGENTS.md 2."""
    import datetime

    runs, current = [], []
    for row in rows:
        current.append(row)
        if row.get("final"):
            runs.append(current)
            current = []
    out = []
    for group in runs:
        last = group[-1]
        ok = last.get("result") == "ok"
        failed = next((r for r in reversed(group) if not r.get("ok")), None)
        out.append({
            "execution_id": len(out) + 1, "workflow": "tretry",
            "started_at": datetime.datetime.fromtimestamp(group[0]["at"]).isoformat(timespec="seconds"),
            "user": "", "topic": last.get("target", ""), "question": last.get("target", ""), "release": "", "channel": "",
            "status": "success" if ok else "error",
            "error_node": None if ok else last.get("kind"), "error_message": None if ok else (failed or last).get("error"),
            "route": ("대체" if any(r.get("fallback") for r in group) else "성공") if ok else None,
            "duration_ms": round((last["started"] + last["seconds"]) * 1000), "steps": {}, "llm_calls": 0, "cost_usd": 0,
            "repeat": False, "tag": "tretry", "source": "live",
        })
    return out


def shape(data) -> list[dict]:
    """A JSON list, {"logs": [...]} (the data API), or tretry attempt rows."""
    rows = data.get("logs", []) if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise LoadError("expected a JSON list of runs or {\"logs\": [...]}")
    if rows and "attempt" in rows[0] and "kind" in rows[0]:
        return from_tretry(rows)
    return rows


def read_file(path: Path) -> list[dict]:
    if not path.exists():
        raise LoadError(f"no such file: {path}")
    text = path.read_text(encoding="utf-8")
    try:
        return shape(json.loads(text))
    except json.JSONDecodeError:
        rows = []
        for line in text.splitlines():
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue  # a half-written line
        if not rows:
            raise LoadError(f"not JSON or JSON Lines: {path}")
        return shape(rows)


def read_url(base: str, date_from: str = "", date_to: str = "", tag: str = "", source: str = "all", timeout: float = 20) -> list[dict]:
    """The data API filters (POST /logs/query), so the definition of a period lives in one place."""
    body = json.dumps({"from": date_from, "to": date_to, "tag": tag, "source": source}).encode()
    request = urllib.request.Request(base.rstrip("/") + "/logs/query", data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as answer:
            return shape(json.loads(answer.read()))
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as error:
        raise LoadError(f"data API {base}: {error}") from error


def read(file: str | None = None, url: str | None = None, date_from: str = "", date_to: str = "", tag: str = "",
         source: str = "all") -> list[dict]:
    """--file wins over --url ($TLOG_URL may be set for every call)."""
    if file:
        return [r for r in read_file(Path(file)) if keep(r, date_from, date_to, tag, source)]
    if url:
        return read_url(url, date_from, date_to, tag, source)
    return []
