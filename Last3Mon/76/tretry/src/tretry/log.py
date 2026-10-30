"""The attempt log as JSON Lines (R7), stats from it (R9) and the circuit breaker that reads it (R10)."""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import asdict
from pathlib import Path

from .retry import Result

SECRET = re.compile(r"(sk-[A-Za-z0-9_-]{8,}|Bearer\s+\S+|(api[_-]?key|token|password)=[^&\s]+)", re.I)


def default_path() -> Path:
    return Path(os.environ.get("TRETRY_LOG") or Path.home() / ".tretry" / "log.jsonl")


def clean(text: str) -> str:
    """Never keep a key or a token in the log, even when it is part of a URL or an error message."""
    return SECRET.sub("***", text)


def write(path: Path, kind: str, target: str, result: Result, now: float | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    at = now if now is not None else time.time()
    with path.open("a", encoding="utf-8") as out:
        first = at - result.seconds  # wall clock time of the first try
        for item in result.attempts:
            row = {"at": round(first + item.started, 3), "kind": kind, "target": clean(target), **asdict(item)}
            row["error"] = clean(row["error"])
            row["final"] = item is result.attempts[-1]
            row["result"] = "ok" if result.ok else "failed"
            row["stopped"] = result.stopped
            out.write(json.dumps(row, ensure_ascii=False) + "\n")


def read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # a half-written line from a killed run
    return rows


def runs(rows: list[dict]) -> list[list[dict]]:
    """Group attempt rows into runs (one tretry call = the rows up to and including its final row)."""
    groups, current = [], []
    for row in rows:
        current.append(row)
        if row.get("final"):
            groups.append(current)
            current = []
    return groups


def p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(0.95 * (len(ordered) - 1)))]


def stats(rows: list[dict]) -> list[dict]:
    """Per target: runs, success rate, attempts per run, failed attempts, fallbacks, p95 run time. Most failures first."""
    table: dict[str, dict] = {}
    for group in runs(rows):
        target = group[-1]["target"]
        row = table.setdefault(target, {"target": target, "kind": group[-1]["kind"], "runs": 0, "ok": 0, "attempts": 0,
                                        "failed_attempts": 0, "fallbacks": 0, "times": []})
        row["runs"] += 1
        row["ok"] += group[-1]["result"] == "ok"
        row["attempts"] += len(group)
        row["failed_attempts"] += sum(1 for r in group if not r["ok"])
        row["fallbacks"] += any(r.get("fallback") for r in group)
        row["times"].append(group[-1]["started"] + group[-1]["seconds"])
    out = []
    for row in table.values():
        times = row.pop("times")
        out.append({**row, "success_rate": round(row["ok"] / row["runs"], 3), "attempts_per_run": round(row["attempts"] / row["runs"], 2),
                    "p95_seconds": round(p95(times), 3)})
    return sorted(out, key=lambda r: (-r["failed_attempts"], r["target"]))


def breaker_open(rows: list[dict], target: str, failures: int = 5, window: float = 60.0, now: float | None = None) -> bool:
    """Open when the last `failures` attempts at this target (not fallbacks) all failed within `window` seconds."""
    now = now if now is not None else time.time()
    recent = [r for r in rows if r.get("target") == clean(target) and not r.get("fallback") and now - r["at"] <= window]
    last = recent[-failures:]
    return len(last) >= failures and not any(r["ok"] for r in last)
