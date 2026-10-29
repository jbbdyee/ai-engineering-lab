"""R5 save · R6 log/diff of versions · R7 no secrets · R10 restore · R13 folder."""
import json

import pytest

from tver.cli import main
from tver.store import Store, StoreError

FAKE_KEY = "sk-" + "test-" + "a" * 24   # made here, never stored in a file of this repository


def test_save_twice_makes_one_commit(work, store_dir):
    store = Store(store_dir)
    assert store.save(work / "helpdesk.json")[0][1] == "saved"
    assert store.save(work / "helpdesk.json")[0][1] == "no change"
    assert len(store.log("helpdesk.json")) == 1


def test_versions_and_diff_between_them(work, store_dir, v2, capsys):
    store = Store(store_dir)
    store.save(work / "helpdesk.json")
    (work / "helpdesk.json").write_text(json.dumps(v2), encoding="utf-8")
    name, status, message = store.save(work / "helpdesk.json")[0]
    assert status == "saved" and "model 1 · prompt 1 · flow 5" in message
    versions = store.log("helpdesk.json")
    assert [v.message.split(": ")[0] for v in versions] == ["helpdesk.json", "helpdesk.json"]
    assert main(["--repo", str(store_dir), "diff", versions[1].rev, versions[0].rev, "helpdesk.json", "--short"]) == 1
    assert "7 change(s) · model 1 · prompt 1 · flow 5" in capsys.readouterr().out


def test_secret_is_not_saved(work, store_dir):
    data = json.loads((work / "helpdesk.json").read_text(encoding="utf-8"))
    data["nodes"][0]["parameters"]["note"] = FAKE_KEY
    (work / "helpdesk.json").write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(StoreError) as error:
        Store(store_dir).save(work / "helpdesk.json")
    assert FAKE_KEY not in str(error.value)
    assert not (store_dir / "helpdesk.json").exists()


def test_restore_writes_a_file_and_keeps_the_store(work, store_dir, v2, tmp_path):
    store = Store(store_dir)
    store.save(work / "helpdesk.json")
    (work / "helpdesk.json").write_text(json.dumps(v2), encoding="utf-8")
    store.save(work / "helpdesk.json")
    oldest = store.log("helpdesk.json")[-1].rev
    out = store.restore(oldest, "helpdesk.json", tmp_path / "back.json")
    restored = json.loads(out.read_text(encoding="utf-8"))
    model = next(n for n in restored["nodes"] if n["name"] == "Answer model")
    assert model["parameters"]["model"]["value"] == "gpt-4.1-mini"
    assert len(store.log("helpdesk.json")) == 2


def test_folder_save_skips_files_that_are_not_workflows(work, store_dir):
    rows = Store(store_dir).save(work)
    assert ("cases.json", "skipped", "not a workflow") in rows
    assert [r[0] for r in rows if r[1] == "saved"] == ["helpdesk.json"]
