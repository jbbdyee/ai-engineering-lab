import json
import shutil
from pathlib import Path

import pytest

from tcost import prices

DATA = Path(__file__).parent / "data"


@pytest.fixture
def table():
    return prices.load(prices.BUNDLED)


@pytest.fixture
def folder(tmp_path):
    """A day folder: two prompt files, two workflows, one test report, and a test case file (skipped)."""
    (tmp_path / "prompts").mkdir()
    (tmp_path / "prompts" / "short.txt").write_text("Answer in Korean in at most 3 sentences.", encoding="utf-8")
    (tmp_path / "prompts" / "long.prompt").write_text("규정 " * 400, encoding="utf-8")
    (tmp_path / "reference").mkdir()
    for name in ("baseline-cost.json", "lab02-example1-lean.json"):
        shutil.copy(DATA / name, tmp_path / "reference" / name)
    (tmp_path / "runs").mkdir()
    shutil.copy(DATA / "report-20261028-153000.json", tmp_path / "runs")
    (tmp_path / "cases").mkdir()
    (tmp_path / "cases" / "lab01.json").write_text(json.dumps({"webhook": "my-cost", "cases": []}), encoding="utf-8")
    return tmp_path
