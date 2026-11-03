import csv
import json

from tcheck import cli
from conftest import DATA

EMP = str(DATA / "employees.csv")
EMP_SCHEMA = str(DATA / "schemas" / "employee.json")


def test_check_plain(capsys):
    assert cli.main(["check", EMP, "--schema-file", EMP_SCHEMA]) == 0
    out = capsys.readouterr().out
    assert "9 rows · valid 4 · invalid 5 · score 0.4444" in out and "bad_format:email" in out


def test_check_json_like_my_check(capsys, url, n8n):
    assert cli.main(["check", str(DATA / "tickets-new.json"), "--url", url, "--json"]) == 0   # schema from the file
    out = json.loads(capsys.readouterr().out)
    assert {k: out[k] for k in ("schema", "batch", "valid", "rows", "codes")} == {k: n8n["ticket"][k] for k in ("schema", "batch", "valid", "rows", "codes")}


def test_out_and_rejects_files(tmp_path):
    clean, rejects = tmp_path / "clean.csv", tmp_path / "rejects.csv"
    assert cli.main(["check", EMP, "--schema-file", EMP_SCHEMA, "--out", str(clean), "--rejects", str(rejects)]) == 0
    assert len(list(csv.DictReader(clean.open()))) == 4
    bad = list(csv.DictReader(rejects.open()))
    assert len(bad) == 5 and bad[0]["errors"] == "bad_format:email"


def test_gate_exit_codes(capsys):
    assert cli.main(["gate", EMP, "--schema-file", EMP_SCHEMA]) == 4
    assert "rejected" in capsys.readouterr().out
    assert cli.main(["gate", EMP, "--schema-file", EMP_SCHEMA, "--max-invalid", "0.6"]) == 0


def test_fix_and_log(capsys, url, api):
    assert cli.main(["check", EMP, "--schema", "employee", "--url", url, "--batch", "HR-1", "--fix", "--log"]) == 0
    out = capsys.readouterr().out
    assert "HR-1: 9줄 중 4줄 통과, 5줄 고칠 것" in out and "email의 형식을 확인해 주세요" in out
    assert api.log == [{"batch": "HR-1", "dataset": "employee", "total": 9, "valid": 4, "quarantined": 5, "rejected": False,
                        "score": 0.4444, "codes": api.log[0]["codes"]}]


def test_exit_codes_read_and_usage(tmp_path, url, capsys):
    assert cli.main(["check", str(tmp_path / "none.csv"), "--schema-file", EMP_SCHEMA]) == 1
    assert cli.main(["check", EMP, "--schema", "nothing", "--url", url]) == 1
    assert cli.main(["check", EMP]) == 2                                        # which schema?
    assert cli.main(["nonsense"]) == 2
