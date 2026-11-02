"""R5 · R7 · R8 · R10 · R12: JSON names, exit codes 0 · 1 · 2 · 4."""
import json

from tlog import cli

DATA = "tests/data/run-logs.json"


def test_summary_json_has_the_report_names(capsys):
    assert cli.main(["summary", "--file", DATA, "--from", "2026-10-26", "--to", "2026-10-30", "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert {"total", "errors", "error_rate", "p50_ms", "p95_ms", "by_route", "failures", "anomalies", "slo"} <= set(out)
    assert (out["total"], out["error_rate"]) == (357, 0.0588)


def test_plain_summary(capsys):
    assert cli.main(["summary", "--file", DATA, "--from", "2026-10-19", "--to", "2026-10-30"]) == 0
    assert capsys.readouterr().out.startswith("666 runs · errors 21 (3.15%) · p50 1205ms · p95 2537ms")


def test_exit_codes(capsys):
    assert cli.main(["summary"]) == 2                                   # no source
    assert cli.main(["summary", "--file", "/no/such.json"]) == 1         # cannot read
    assert cli.main(["slo", "--file", DATA, "--from", "2026-10-26", "--to", "2026-10-30"]) == 4
    assert cli.main(["slo", "--file", DATA, "--from", "2026-10-19", "--to", "2026-10-23", "--unanswered", "0.06"]) == 0
    assert "SLO ok" in capsys.readouterr().out


def test_slo_json(capsys):
    cli.main(["slo", "--file", DATA, "--from", "2026-10-26", "--to", "2026-10-30", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert out["breaches"] == ["error_rate", "unanswered_rate"] and out["values"]["p95_ms"] == 2598


def test_usage_mistake_is_2():
    try:
        cli.main(["nope"])
    except SystemExit as stop:
        assert stop.code == 2


def test_compare_and_weekly(capsys):
    args = ["--file", DATA, "--from", "2026-10-26", "--to", "2026-10-30", "--prev-from", "2026-10-19", "--prev-to", "2026-10-23"]
    assert cli.main(["compare", *args, "--json"]) == 0
    rows = {r["metric"]: r for r in json.loads(capsys.readouterr().out)}
    assert rows["total"]["prev"] == 309 and rows["total"]["now"] == 357 and rows["total"]["change"] == 48
    assert cli.main(["weekly", *args]) == 0
    assert "| 요청 | 309 | 357 |" in capsys.readouterr().out


def test_data_api(api, capsys):
    assert cli.main(["summary", "--url", api, "--from", "2026-10-26", "--to", "2026-10-26", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["errors"] == 16


def test_file_wins_over_tlog_url(monkeypatch, capsys):
    monkeypatch.setenv("TLOG_URL", "http://127.0.0.1:9")      # nothing listens there
    assert cli.main(["summary", "--file", DATA, "--from", "2026-10-26", "--to", "2026-10-26", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["total"] == 70
