"""Percentiles and summaries. Nearest-rank: sort, take the ceil(p * n)-th value."""
import math

KINDS = ("connect", "timeout", "http_5xx", "http_4xx")


def percentile(values, p):
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, math.ceil(p * len(ordered) - 1e-9))
    return ordered[rank - 1]


def average_timings(results):
    """Average every numeric field of response `timings` over successful calls."""
    sums, counts = {}, {}
    for r in results:
        for key, value in (r.get("timings") or {}).items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                sums[key] = sums.get(key, 0) + value
                counts[key] = counts.get(key, 0) + 1
    return {k: round(sums[k] / counts[k], 1) for k in sums}


def summarize(results, total=None):
    """results: measured calls (no warmup). Failures are counted, not timed."""
    ok = [r for r in results if r["error_kind"] is None]
    times = [r["seconds"] for r in ok]
    rest = [r["seconds"] for r in ok if r.get("note") != "first call"]
    by_kind = {k: sum(1 for r in results if r["error_kind"] == k) for k in KINDS}
    return {
        "done": len(results),
        "total": total if total is not None else len(results),
        "ok": len(ok),
        "failures": len(results) - len(ok),
        "by_kind": by_kind,
        "p50": percentile(times, 0.5),
        "p95": percentile(times, 0.95),
        "max": max(times) if times else None,
        "p50_excl_first": percentile(rest, 0.5) if len(rest) < len(times) else None,
        "timings": average_timings(ok),
    }


def fmt(seconds):
    return "-" if seconds is None else f"{seconds:.3f}"


def summary_lines(s):
    kinds = " ".join(f"{k}={v}" for k, v in s["by_kind"].items() if v)
    lines = [
        f"done {s['done']}/{s['total']}  failures {s['failures']}" + (f" ({kinds})" if kinds else ""),
        f"p50 {fmt(s['p50'])}s  p95 {fmt(s['p95'])}s  max {fmt(s['max'])}s"
        + (f"  p50 excl. first {fmt(s['p50_excl_first'])}s" if s["p50_excl_first"] is not None else ""),
    ]
    if s["timings"]:
        lines.append("timings avg ms  " + "  ".join(f"{k} {v:g}" for k, v in s["timings"].items()))
    return lines


def check(s, max_p95=None, max_failures=None):
    """Return (passed, line) for the given limits."""
    problems = []
    if max_p95 is not None and (s["p95"] is None or s["p95"] > max_p95):
        problems.append(f"p95 {fmt(s['p95'])} > {max_p95}")
    if max_failures is not None and s["failures"] > max_failures:
        problems.append(f"failures {s['failures']} > {max_failures}")
    return (not problems, "FAIL " + ", ".join(problems) if problems else "PASS")
