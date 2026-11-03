import json

import pytest

from tcheck import checks, load
from conftest import DATA

FILES = {"employee": "employees.csv", "ticket": "tickets-new.json", "faq": "faq-batch-3.json"}


def schema(name):
    return json.loads((DATA / "schemas" / f"{name}.json").read_text(encoding="utf-8"))


def run(name, batch="X", content=()):
    rows, _ = load.read_rows(str(DATA / FILES[name]))
    return checks.check(rows, schema(name), batch, content)


@pytest.mark.parametrize("name", ["employee", "ticket", "faq"])
def test_same_rows_and_codes_as_n8n(name, n8n):
    """R4: the same file gives the same rows · codes · valid as n8n my-check."""
    r = run(name, n8n[name]["batch"])
    for key in ("schema", "batch", "total", "valid", "invalid", "rows", "codes"):
        assert r[key] == n8n[name][key], key


def test_employee_reasons():
    r = run("employee")
    assert [row["errors"] for row in r["rows"]] == [[], [], ["bad_format:email"], ["not_allowed:dept"], ["bad_format:joined"],
                                                    ["missing:name"], [], ["duplicate_in_batch"], []]


def test_ticket_optional_field_and_impossible_date():
    r = run("ticket")
    assert r["rows"][3]["errors"] == ["bad_format:opened"]          # 2026-02-30
    assert r["rows"][5]["errors"] == ["bad_format:contact"]         # present but wrong
    assert r["rows"][8]["ok"]                                       # contact missing is fine


def test_string_list_and_blank_edges():
    s = {"name": "t", "key": "id", "fields": {"id": {"type": "string", "required": True, "min": 2, "max": 3},
                                              "tags": {"type": "list", "required": False, "min_items": 1, "max_items": 2}}}
    r = checks.check([{"id": "ab"}, {"id": "abcd"}, {"id": "   "}, {"id": "abc", "tags": "x"}, {"id": "ab2", "tags": [1, 2, 3]}], s)
    assert [row["errors"] for row in r["rows"]] == [[], ["too_long:id"], ["missing:id"], ["bad_format:tags"], ["too_many:tags"]]


def test_content_rules_on_a_field():
    """R8: Lab 01 rules — phone without dashes, exact intra host."""
    s = {"name": "faq", "key": "id", "fields": {}}
    rows = [{"id": "1", "answer": "당직 01012345678"}, {"id": "2", "answer": "02-123-4567"},
            {"id": "3", "answer": "https://intra.example.com/help"}, {"id": "4", "answer": "http://intra.example.com.evil.io/x"},
            {"id": "5", "answer": "a@b.com"}]
    r = checks.check(rows, s, content=("answer",))
    assert [row["errors"] for row in r["rows"]] == [["pii"], [], [], ["external_link"], ["pii"]]


def test_gate_equal_passes():
    r = run("employee")                                             # 5 / 9 = 0.5556
    assert checks.gate(r, 0.3) == {"accepted": False, "invalid_ratio": 0.5556, "max_invalid_ratio": 0.3}
    assert checks.gate({"invalid": 1, "total": 10}, 0.1)["accepted"] is True
    assert checks.gate({"invalid": 0, "total": 0}, 0.3)["accepted"] is True


def test_fix_list_and_message():
    r = run("ticket", "TK-1")
    f = checks.fix_list(r, schema("ticket"))
    assert f["message"] == "TK-1: 9줄 중 2줄 통과, 7줄 고칠 것"
    assert [i["row"] for i in f["fix_list"]] == [2, 3, 4, 5, 6, 7, 8]
    assert f["fix_list"][1]["fix"] == ["priority은(는) low · normal · high 중 하나로"]
    assert "ticket_id" in f["fix_list"][5]["fix"][0]


def test_quality_entry_and_round():
    e = checks.quality_entry(run("employee", "HR-1"))
    assert e == {"batch": "HR-1", "dataset": "employee", "total": 9, "valid": 4, "quarantined": 5, "rejected": False,
                 "score": 0.4444, "codes": e["codes"]}
    assert checks.js_round(0.00005) == 0.0001 and checks.js_round(2 / 3) == 0.6667
