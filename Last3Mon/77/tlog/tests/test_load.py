"""R1 · R9: files, the data API, inclusive dates, and day 76 tretry logs in the same run shape."""
import json

import pytest

from tlog import load

from conftest import run


def test_dates_are_inclusive_and_filters(tmp_path):
    rows = [run("2026-10-26T09:00:00"), run("2026-10-30T17:00:00"), run("2026-10-31T10:00:00", tag="after", source="live")]
    path = tmp_path / "logs.json"
    path.write_text(json.dumps(rows))
    assert len(load.read(str(path), date_from="2026-10-26", date_to="2026-10-30")) == 2
    assert len(load.read(str(path), date_from="2026-10-30", date_to="2026-10-30")) == 1
    assert len(load.read(str(path), source="live")) == 1 and len(load.read(str(path), source="seed")) == 2
    assert len(load.read(str(path), tag="after")) == 1


def test_json_lines_with_a_half_line(tmp_path):
    path = tmp_path / "logs.jsonl"
    path.write_text(json.dumps(run("2026-10-26T09:00:00")) + "\n" + '{"started_at": "2026-10-2')
    assert len(load.read(str(path))) == 1


def test_missing_file():
    with pytest.raises(load.LoadError):
        load.read("/no/such/file.json")


def test_data_api(api):
    rows = load.read(url=api, date_from="2026-10-26", date_to="2026-10-26")
    assert len(rows) == 70
    assert len(load.read(url=api, tag="after", source="live")) == 1


def test_tretry_log_becomes_runs(tmp_path):
    rows = [
        {"at": 100.0, "kind": "http", "target": "POST http://x/tickets", "attempt": 1, "started": 0, "seconds": 3, "ok": False,
         "error": "timeout", "final": False, "result": "failed"},
        {"at": 103.5, "kind": "http", "target": "POST http://x/tickets", "attempt": 2, "started": 3.5, "seconds": 3, "ok": False,
         "error": "timeout", "final": True, "result": "failed"},
        {"at": 110.0, "kind": "command", "target": "curl ok", "attempt": 1, "started": 0, "seconds": 0.1, "ok": True,
         "error": "", "final": True, "result": "ok"},
    ]
    path = tmp_path / "log.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in rows))
    out = load.read(str(path))
    assert [r["status"] for r in out] == ["error", "success"]
    assert out[0]["duration_ms"] == 6500 and out[0]["error_message"] == "timeout" and out[1]["route"] == "성공"
