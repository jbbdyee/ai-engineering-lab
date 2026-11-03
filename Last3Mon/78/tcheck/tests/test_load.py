import json

import pytest

from tcheck import load
from conftest import DATA


def test_csv_first_line_is_columns():
    rows, meta = load.read_rows(str(DATA / "employees.csv"))
    assert len(rows) == 9 and rows[2]["email"] == "minsu.kang@example" and rows[1]["phone"] == ""
    assert meta["batch"] == "employees"


def test_request_file_with_csv_or_items(tmp_path):
    rows, meta = load.read_rows(str(DATA / "tickets-new.json"))
    assert len(rows) == 9 and meta == {"schema": "ticket", "batch": "TK-1"}
    f = tmp_path / "hr.json"
    f.write_text(json.dumps({"schema": "employee", "batch": "HR-1", "csv": (DATA / "employees.csv").read_text()}))
    assert len(load.read_rows(str(f))[0]) == 9


def test_plain_list(tmp_path):
    f = tmp_path / "rows.json"
    f.write_text("[{\"a\": 1}]")
    assert load.read_rows(str(f)) == ([{"a": 1}], {"batch": "rows"})


def test_missing_or_bad_files(tmp_path):
    with pytest.raises(load.LoadError):
        load.read_rows(str(tmp_path / "nope.csv"))
    bad = tmp_path / "bad.json"
    bad.write_text("{\"x\": 1}")
    with pytest.raises(load.LoadError):
        load.read_rows(str(bad))


def test_schema_from_api_or_file(url):
    assert load.read_schema("employee", url)["key"] == "email"
    assert load.read_schema("", None, str(DATA / "schemas" / "ticket.json"))["name"] == "ticket"
    with pytest.raises(load.LoadError):
        load.read_schema("nothing", url)
    with pytest.raises(load.LoadError):
        load.read_schema("employee", None)
