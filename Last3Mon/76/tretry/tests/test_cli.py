"""R1 · R3 · R4 · R5 · R7 · R8 · R9 · R10 through the command line (real commands, local fake server, temp log)."""
import json
import sys

from tretry import cli, log

PY = sys.executable


def run(capsys, *argv):
    code = cli.main(list(argv))
    out = capsys.readouterr()
    return code, out.out, out.err


def test_command_fails_then_fallback(tmp_path, capsys):
    logfile = tmp_path / "log.jsonl"
    code, out, err = run(capsys, "--tries", "2", "--backoff", "0", "--log", str(logfile), "--fallback", "echo cached",
                         "--", PY, "-c", "import sys; sys.exit(3)")
    assert code == 0 and out.strip() == "cached" and "by the fallback" in err
    rows = log.read(logfile)
    assert [r["fallback"] for r in rows] == [False, False, True] and rows[0]["error"].startswith("exit 3")


def test_command_timeout(tmp_path, capsys):
    code, _, err = run(capsys, "--tries", "1", "--timeout", "0.3", "--log", str(tmp_path / "l"), "--",
                       PY, "-c", "import time; time.sleep(5)")
    assert code == 1 and "timeout 0.3s" in err


def test_http_5xx_retried_4xx_not(server, tmp_path, capsys):
    base, script, seen = server
    script["/flaky"] = [(500, {"error": "x"}, {}), (201, {"ticket_id": "T-1"}, {})]
    script["/bad"] = [(400, {"error": "title is required"}, {})]
    logfile = str(tmp_path / "log.jsonl")
    code, out, _ = run(capsys, "http", "POST", base + "/flaky", "--body", "{}", "--backoff", "0", "--log", logfile)
    assert code == 0 and "T-1" in out and len(seen) == 2
    code, _, err = run(capsys, "http", "POST", base + "/bad", "--body", "{}", "--backoff", "0", "--log", logfile,
                       "--fallback", "echo cached")
    assert code == 3 and len(seen) == 3 and "not-retryable" in err             # one try, no fallback


def test_http_same_idempotency_key_every_try(server, tmp_path, capsys):
    base, script, seen = server
    script["/tickets"] = [(500, {}, {}), (500, {}, {}), (201, {"ticket_id": "T-1"}, {})]
    code, _, _ = run(capsys, "http", "POST", base + "/tickets", "--body", '{"title": "t"}', "--idem-key", "auto",
                     "--body-key", "key", "--backoff", "0", "--log", str(tmp_path / "l"))
    keys = {s["headers"]["Idempotency-Key"] for s in seen}
    bodies = {json.loads(s["body"])["key"] for s in seen}
    assert code == 0 and len(seen) == 3 and len(keys) == 1 and keys == bodies   # R5


def test_http_timeout_is_retried(server, tmp_path, capsys):
    base, script, seen = server
    script["/slow"] = [("sleep", 1.0, {}), (200, {"ok": True}, {})]
    code, _, err = run(capsys, "http", "GET", base + "/slow", "--timeout", "0.3", "--backoff", "0", "--log", str(tmp_path / "l"))
    assert code == 0 and "timeout" in err and len(seen) == 2


def test_log_never_keeps_a_key(server, tmp_path, capsys):
    base, script, _ = server
    script["/x?api_key=secret123"] = [(503, {}, {})]
    logfile = tmp_path / "log.jsonl"
    run(capsys, "http", "GET", base + "/x?api_key=secret123", "--tries", "1", "--header", "Authorization: Bearer sk-abcdefghijklmnop",
        "--log", str(logfile))
    text = logfile.read_text()
    assert "secret123" not in text and "sk-abcdefghijklmnop" not in text and "***" in text    # R7


def test_json_output_and_exit_code(tmp_path, capsys):
    code, out, _ = run(capsys, "--tries", "2", "--backoff", "0", "--json", "--log", str(tmp_path / "l"), "--", PY, "-c", "raise SystemExit(1)")
    data = json.loads(out)
    assert code == 1 and data["exit_code"] == 1 and data["stopped"] == "tries" and len(data["attempts"]) == 2   # R8


def test_stats_and_breaker(tmp_path, capsys):
    logfile = str(tmp_path / "log.jsonl")
    fail = ["--backoff", "0", "--log", logfile, "--", PY, "-c", "raise SystemExit(1)"]
    run(capsys, "--tries", "3", *fail)
    run(capsys, "--tries", "2", *fail)                       # 5 failed tries in a row → breaker opens
    code, out, err = run(capsys, "--tries", "3", "--fallback", "echo cached", *fail)
    assert code == 0 and out.strip() == "cached" and "breaker open" in err      # R10: no try, straight to fallback
    code, out, _ = run(capsys, "stats", "--log", logfile, "--json")
    row = json.loads(out)[0]
    assert row["runs"] == 3 and row["failed_attempts"] == 5 and row["fallbacks"] == 1 and row["success_rate"] == 0.333   # R9


def test_usage_errors(capsys):
    assert run(capsys, "echo", "hi")[0] == 2                  # no --
    assert run(capsys, "http", "POST", "http://x", "--body", "{bad")[0] == 2
    assert run(capsys, "--tries", "0", "--", "true")[0] == 2
