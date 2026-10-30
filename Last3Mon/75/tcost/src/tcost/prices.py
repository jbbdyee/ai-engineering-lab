"""Price table: USD per 1M tokens, with the date it was checked and where it came from."""
from __future__ import annotations

import datetime as dt
import json
import os
from dataclasses import dataclass
from pathlib import Path

BUNDLED = Path(__file__).with_name("prices.json")
STALE_DAYS = 30


class UnknownModel(KeyError):
    """A model name that is not in the price table (never priced as 0)."""

    def __init__(self, model: str, known: list[str]):
        super().__init__(model)
        self.model, self.known = model, known

    def __str__(self) -> str:
        return f"unknown model {self.model!r} (known: {', '.join(self.known)})"


@dataclass
class Prices:
    models: dict[str, dict[str, float]]
    checked: str = ""
    source: str = ""
    path: str = ""

    def rate(self, model: str) -> dict[str, float]:
        if model not in self.models:
            raise UnknownModel(model, sorted(self.models))
        return self.models[model]

    def cost(self, model: str, tokens_in: int, tokens_out: int = 0) -> float:
        """(in × input + out × output) / 1,000,000, rounded to 8 places (the day 75 contract)."""
        rate = self.rate(model)
        return round((tokens_in * rate["input"] + tokens_out * rate["output"]) / 1_000_000, 8)

    def age_days(self, today: dt.date | None = None) -> int | None:
        try:
            checked = dt.date.fromisoformat(self.checked)
        except ValueError:
            return None
        return ((today or dt.date.today()) - checked).days

    def warning(self, today: dt.date | None = None) -> str:
        age = self.age_days(today)
        if age is None:
            return f"prices in {self.path} have no 'checked' date. Check the price list and add one."
        if age > STALE_DAYS:
            return f"prices were checked {age} days ago ({self.checked}). Prices change: check {self.source or 'the price list'}."
        return ""


def default_path() -> Path:
    """--prices, else $TCOST_PRICES, else ~/.tcost/prices.json, else the file shipped with tcost."""
    for candidate in (os.getenv("TCOST_PRICES"), Path.home() / ".tcost" / "prices.json"):
        if candidate and Path(candidate).expanduser().exists():
            return Path(candidate).expanduser()
    return BUNDLED


def load(path: str | Path | None = None) -> Prices:
    path = Path(path).expanduser() if path else default_path()
    data = json.loads(path.read_text(encoding="utf-8"))
    models = data.get("models") or {}
    if not models:
        raise ValueError(f"{path}: no 'models' in the price table")
    return Prices({name: {"input": float(v["input"]), "output": float(v["output"])} for name, v in models.items()},
                  str(data.get("checked", "")), str(data.get("source", "")), str(path))
