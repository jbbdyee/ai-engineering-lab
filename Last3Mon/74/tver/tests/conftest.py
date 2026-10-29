import json
import shutil
from pathlib import Path

import pytest

DATA = Path(__file__).parent / "data"


@pytest.fixture
def v1():
    return json.loads((DATA / "helpdesk-v1.json").read_text(encoding="utf-8"))


@pytest.fixture
def v2():
    return json.loads((DATA / "helpdesk-v2.json").read_text(encoding="utf-8"))


@pytest.fixture
def work(tmp_path):
    """A my-work folder with v1 as helpdesk.json, a note and a cases file (not workflows)."""
    folder = tmp_path / "my-work"
    folder.mkdir()
    shutil.copy(DATA / "helpdesk-v1.json", folder / "helpdesk.json")
    (folder / "PROMPTS.md").write_text("# prompts\n", encoding="utf-8")
    (folder / "cases.json").write_text('{"webhook": "x", "cases": []}', encoding="utf-8")
    return folder


@pytest.fixture
def store_dir(tmp_path):
    return tmp_path / "store"
