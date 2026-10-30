"""Sum the usage of flow.py test reports (runs/*.json) (R5) and project a month from it (R6)."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

STAMP = re.compile(r"-(\d{8})-(\d{2})\d{4}\.json$")


def _row() -> dict:
    return {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0}


def _add(row: dict, calls: int, tokens_in: int, tokens_out: int, cost: float) -> None:
    row["calls"] += calls
    row["prompt_tokens"] += tokens_in
    row["completion_tokens"] += tokens_out
    row["cost_usd"] = round(row["cost_usd"] + cost, 8)


@dataclass
class Usage:
    reports: int = 0
    requests: int = 0
    skipped: int = 0
    total: dict = field(default_factory=_row)
    by_model: dict = field(default_factory=dict)
    by_user: dict = field(default_factory=dict)
    by_hour: dict = field(default_factory=dict)

    @property
    def avg_usd(self) -> float:
        return self.total["cost_usd"] / self.requests if self.requests else 0.0

    def month(self, per_day: int, days: int = 22) -> float:
        """avg cost per request × requests a day × working days (rounded to 6 places, like the day 75 report)."""
        return round(self.avg_usd * per_day * days, 6)

    def to_dict(self) -> dict:
        return {"reports": self.reports, "requests": self.requests, "skipped": self.skipped, **self.total,
                "avg_usd": round(self.avg_usd, 8), "by_model": self.by_model, "by_user": self.by_user, "by_hour": self.by_hour}


def is_report(data: object) -> bool:
    return isinstance(data, dict) and isinstance(data.get("results"), list) and "cases" in data


def report_files(paths: list[str | Path]) -> list[Path]:
    files: list[Path] = []
    for path in map(Path, paths):
        files += sorted(path.glob("*.json")) if path.is_dir() else [path]
    return files


def collect(paths: list[str | Path]) -> Usage:
    usage = Usage()
    for path in report_files(paths):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not is_report(data):
            continue
        usage.reports += 1
        stamp = STAMP.search(path.name)
        hour = f"{stamp.group(2)}h" if stamp else "?"
        for result in data["results"]:
            response = result.get("response")
            steps = (response or {}).get("usage", {}).get("by_step") if isinstance(response, dict) else None
            if not isinstance(steps, dict):
                usage.skipped += 1          # a 400 / 429 answer, a summary case, or a report from another day
                continue
            usage.requests += 1
            user = str((result.get("request") or {}).get("user") or "?")
            for step in steps.values():
                tokens_in, tokens_out = int(step.get("prompt_tokens") or 0), int(step.get("completion_tokens") or 0)
                cost = float(step.get("cost_usd") or 0)
                _add(usage.total, 1, tokens_in, tokens_out, cost)
                for table, key in ((usage.by_model, str(step.get("model", "?"))), (usage.by_user, user), (usage.by_hour, hour)):
                    _add(table.setdefault(key, _row()), 1, tokens_in, tokens_out, cost)
    return usage
