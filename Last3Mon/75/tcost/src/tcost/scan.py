"""Sort a folder into what tcost can read (R11): text files, workflows, test reports, and the rest (skipped)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .usage import is_report
from .workflow import is_workflow

TEXT = {".txt", ".prompt"}


@dataclass
class Found:
    texts: list[Path] = field(default_factory=list)
    workflows: list[Path] = field(default_factory=list)
    reports: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)


def scan(folder: str | Path) -> Found:
    found = Found()
    for path in sorted(Path(folder).rglob("*")):
        if not path.is_file() or any(part.startswith(".") for part in path.relative_to(folder).parts):
            continue
        if path.suffix in TEXT:
            found.texts.append(path)
        elif path.suffix == ".json":
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                found.skipped.append(path)
                continue
            (found.workflows if is_workflow(data) else found.reports if is_report(data) else found.skipped).append(path)
        else:
            found.skipped.append(path)
    return found
