"""R2 · R3 · R4 · R6 · R9 · R10 · R14: commands, --json unchanged, exit codes 0 · 1 · 2 · 4."""
import json

from conftest import DATA, load

from tops.cli import main


def test_status_red_exits_4(fake, capsys):
    assert main(["status", "--n8n", fake.base]) == 4
    assert "🔴 DLQ      3 (parked 2)" in capsys.readouterr().out


def test_status_json_is_the_n8n_answer(fake, capsys):
    main(["status", "--n8n", fake.base, "--json"])
    assert json.loads(capsys.readouterr().out) == load("facts.json")


def test_status_from_env(fake, monkeypatch, capsys):
    monkeypatch.setenv("TOPS_N8N", fake.base)
    assert main(["status", "--from", "2026-10-19", "--to", "2026-10-23"]) == 4
    assert fake.calls[0][1] == {"from": "2026-10-19", "to": "2026-10-23"}


def test_status_without_source_is_usage(monkeypatch, capsys):
    monkeypatch.delenv("TOPS_N8N", raising=False)
    assert main(["status"]) == 2
    assert "--n8n" in capsys.readouterr().err


def test_n8n_off_exits_1(down, capsys):
    assert main(["status", "--n8n", down]) == 1
    assert "cannot read" in capsys.readouterr().err


def test_bad_option_exits_2(capsys):
    assert main(["status", "--nope"]) == 2


def test_ask_refused_action(fake, capsys):
    assert main(["ask", "--n8n", fake.base, "DLQ 1번 다시 돌려 줘"]) == 0
    out = capsys.readouterr().out
    assert "refused (read_only)" in out and "읽기만" in out


def test_ask_llm_router_answer(fake, capsys):
    main(["ask", "--n8n", fake.base, "이번 주에 AI 쓰는 데 얼마나 나갔어?"])
    assert capsys.readouterr().out.startswith("[cost · llm] numbers ✔")


def test_brief_prints_markdown(fake, capsys):
    main(["brief", "--n8n", fake.base])
    assert "| DLQ | 🔴 | 3건 (parked 2) |" in capsys.readouterr().out


def test_eval_gate_pass_and_fail(fake, capsys, tmp_path):
    assert main(["eval", "--n8n", fake.base, str(DATA / "ops-golden.json"), "--min-score", "0.8"]) == 0
    assert "8/8 · score 1 · gate pass (min 0.8)" in capsys.readouterr().out
    one = tmp_path / "one.json"
    one.write_text(json.dumps({"cases": [{"question": "알림이 몇 건 와 있어?", "area": "cost"}]}, ensure_ascii=False))
    assert main(["eval", "--n8n", fake.base, str(one)]) == 4
    assert "✘ 알림이 몇 건 와 있어? · area alerts · area_ok" in capsys.readouterr().out
    assert fake.calls[-1][1] == {"cases": [{"question": "알림이 몇 건 와 있어?", "area": "cost"}]}


def test_eval_empty_is_usage(fake, tmp_path, capsys):
    empty = tmp_path / "empty.json"
    empty.write_text('{"cases": []}')
    assert main(["eval", "--n8n", fake.base, str(empty)]) == 2


def test_audit_lists_questions(fake, capsys):
    main(["audit", "--api", fake.base])
    out = capsys.readouterr().out
    assert out.startswith("3 question(s)") and "refused read_only" in out and "answered" in out


def test_tools_never_fail(capsys):
    assert main(["tools"]) == 0
