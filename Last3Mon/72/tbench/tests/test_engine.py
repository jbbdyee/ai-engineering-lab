import json
import socket
import time

import pytest

from tbench import cli, profiles, store
from tbench.runner import run
from tbench.stats import check, percentile, summarize


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


# R1 · nearest-rank fixed by a test
def test_percentile_nearest_rank():
    values = list(range(1, 11))
    assert percentile(values, 0.5) == 5
    assert percentile(values, 0.95) == 10
    assert percentile([3.0], 0.95) == 3.0
    assert percentile([], 0.5) is None


def test_failures_are_counted_not_timed(server, body_file):
    results = list(run(server.base + "?delay=0.1&fail_every=3", body_file.read_text(), n=6))
    s = summarize(results, 6)
    assert s["failures"] == 2 and s["by_kind"]["http_5xx"] == 2
    assert s["ok"] == 4 and len(results) == 6


def test_body_is_sent(server, body_file):
    list(run(server.base, body_file.read_text(), n=1))
    assert json.loads(server.bodies[0])["question"].startswith("VPN")


# R6
def test_first_call_and_warmup(server):
    results = list(run(server.base + "?first_delay=1&delay=0.05", None, n=4, method="GET"))
    assert results[0]["note"] == "first call"
    s = summarize(results, 4)
    assert s["max"] >= 1 and s["p50_excl_first"] < 0.5
    server.count = 0
    results = list(run(server.base + "?first_delay=1&delay=0.05", None, n=4, method="GET", warmup=1))
    measured = [r for r in results if not r["warmup"]]
    assert len(measured) == 4 and max(r["seconds"] for r in measured) < 0.5
    assert all(r["note"] != "first call" for r in measured)


# R7
def test_error_kinds(server):
    assert list(run(f"http://127.0.0.1:{free_port()}/x", None, n=1))[0]["error_kind"] == "connect"
    assert list(run(server.base + "?delay=3", None, n=1, timeout=1))[0]["error_kind"] == "timeout"
    assert list(run(server.base + "?status=500", None, n=1))[0]["error_kind"] == "http_5xx"
    assert list(run(server.base + "?status=404", None, n=1))[0]["error_kind"] == "http_4xx"


# R8 · R3 · R11 · R13
def test_save_masks_keys_compare_warns_history_and_log(server, body_file, tmp_path, capsys):
    out_a, out_b, log = tmp_path / "a.json", tmp_path / "b.json", tmp_path / "runs.jsonl"
    url = server.base + "?delay=0.05"
    cli.execute(cli.settings_from(type("A", (), {"url": url, "body_file": str(body_file), "n": 3,
                "header": ["Authorization: Bearer sk-test", "X-Api-Key: sk-test2"]})()),
                True, str(out_a), str(log))
    other = tmp_path / "other.json"
    other.write_text('{"question": "점심 메뉴"}')
    cli.execute(cli.settings_from(type("A", (), {"url": url, "body_file": str(other), "n": 3})()), True, str(out_b), None)
    assert "sk-test" not in out_a.read_text() and "sk-test" not in log.read_text()
    assert json.loads(out_a.read_text())["headers"]["Authorization"] == "***"
    assert len(log.read_text().splitlines()) == 3
    lines = store.compare(store.load(out_a), store.load(out_b))
    assert any(line.startswith("WARNING: different body_sha256") for line in lines)
    assert not any("WARNING" in line for line in store.compare(store.load(out_a), store.load(out_a)))

    cli.execute(cli.settings_from(type("A", (), {"url": url, "n": 2})()), True, "", None)
    time.sleep(1.1)
    cli.execute(cli.settings_from(type("A", (), {"url": url, "n": 4})()), True, "", None)
    rows = store.history()
    assert [r[2] for r in rows] == [4, 2]


# R4
def test_concurrency_is_faster(server):
    t = time.perf_counter()
    list(run(server.base + "?delay=0.3", None, n=6, concurrency=1))
    one = time.perf_counter() - t
    t = time.perf_counter()
    results = list(run(server.base + "?delay=0.3", None, n=6, concurrency=3))
    three = time.perf_counter() - t
    assert one > 1.7 and three < 1.0
    assert sorted(r["i"] for r in results) == [1, 2, 3, 4, 5, 6]


# R10
def test_limits_and_exit_code(server):
    s = summarize(list(run(server.base + "?delay=0.2", None, n=3)), 3)
    assert check(s, max_p95=0.1) == (False, f"FAIL p95 {s['p95']:.3f} > 0.1")
    assert check(s, max_p95=5, max_failures=0) == (True, "PASS")
    with pytest.raises(SystemExit) as e:
        cli.main([server.base + "?status=500", "-n", "2", "--plain", "--max-failures", "0"])
    assert e.value.code == 1
    with pytest.raises(SystemExit) as e:
        cli.main([server.base, "-n", "2", "--plain", "--max-p95", "5"])
    assert e.value.code == 0


# R9
def test_timings_average(server):
    s = summarize(list(run(server.base + "?timings=1", None, n=2)), 2)
    assert s["timings"] == {"classify_ms": 150.0, "answer_ms": 300.0, "total_ms": 550.0}
    assert summarize(list(run(server.base, None, n=1)), 1)["timings"] == {}


# R12
def test_profile_save_and_run_from_another_folder(server, body_file, tmp_path, monkeypatch, capsys):
    with pytest.raises(SystemExit):
        cli.main(["profile", "save", "vpn", server.base, "--body-file", str(body_file), "-n", "3",
                  "--header", "Authorization: Bearer sk-live"])
    assert "sk-live" not in profiles.path().read_text()
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as e:
        cli.main(["run", "vpn", "--plain"])
    assert e.value.code == 0
    out = capsys.readouterr().out
    assert "done 3/3" in out and server.bodies
