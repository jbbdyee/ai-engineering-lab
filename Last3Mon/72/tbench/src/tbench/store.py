"""Save, compare and list results; per-call log lines; header masking. Everything lives under ~/.tbench."""
import hashlib
import json
import os
import time
from datetime import datetime
from pathlib import Path

from .stats import fmt, summarize

SECRET_WORDS = ("authorization", "key", "token", "secret", "cookie", "password")


def home():
    return Path(os.environ.get("TBENCH_HOME", Path.home() / ".tbench"))


def mask_headers(headers):
    return {k: ("***" if any(w in k.lower() for w in SECRET_WORDS) else v) for k, v in (headers or {}).items()}


def body_sha256(body):
    return hashlib.sha256((body or "").encode()).hexdigest()


def build_record(url, method, body, headers, n, concurrency, warmup, started, results):
    measured = sorted((r for r in results if not r["warmup"]), key=lambda r: r["i"])
    return {
        "url": url, "method": method, "headers": mask_headers(headers),
        "body_sha256": body_sha256(body), "n": n, "concurrency": concurrency, "warmup": warmup,
        "started": started,
        "seconds": [r["seconds"] for r in measured if r["error_kind"] is None],
        "statuses": [r["status"] for r in measured],
        "errors": [r["error_kind"] for r in measured],
        "calls": [{k: r[k] for k in ("i", "status", "seconds", "error_kind", "note")} for r in measured],
        "summary": summarize(measured, n),
    }


def save(record, path=None):
    if path is None:
        folder = home() / "results"
        folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.fromisoformat(record["started"]).strftime("%Y%m%d-%H%M%S")
        path = folder / f"{stamp}.json"
        k = 1
        while path.exists():
            k += 1
            path = folder / f"{stamp}-{k}.json"
    path = Path(path)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def log_line(fh, result):
    row = {"t": time.time(), "i": result["i"], "status": result["status"],
           "seconds": result["seconds"], "error_kind": result["error_kind"]}
    if result["warmup"]:
        row["warmup"] = True
    fh.write(json.dumps(row) + "\n")
    fh.flush()


def _change(a, b):
    if a is None or b is None:
        return "-"
    if a == 0:
        return "-" if b == 0 else "new"
    return f"{(b - a) / a * 100:+.1f}%"


def compare(a, b):
    """Return lines: warnings first, then a table of p50 · p95 · max · failures."""
    lines = []
    for key in ("url", "method", "body_sha256", "n", "concurrency", "warmup"):
        if a.get(key) != b.get(key):
            lines.append(f"WARNING: different {key}: {a.get(key)} vs {b.get(key)}")
    sa, sb = a["summary"], b["summary"]
    lines.append(f"{'':10}{'A':>10}{'B':>10}{'change':>10}")
    for key in ("p50", "p95", "max"):
        lines.append(f"{key:10}{fmt(sa[key]):>10}{fmt(sb[key]):>10}{_change(sa[key], sb[key]):>10}")
    lines.append(f"{'failures':10}{sa['failures']:>10}{sb['failures']:>10}{_change(sa['failures'], sb['failures']):>10}")
    return lines


def history():
    folder = home() / "results"
    rows = []
    for path in sorted(folder.glob("*.json"), reverse=True) if folder.exists() else []:
        try:
            r = load(path)
        except (ValueError, OSError):
            continue
        s = r["summary"]
        rows.append((r["started"][:19].replace("T", " "), r["url"], r["n"], fmt(s["p50"]), fmt(s["p95"]), s["failures"], path.name))
    rows.sort(key=lambda row: row[0], reverse=True)
    return rows
