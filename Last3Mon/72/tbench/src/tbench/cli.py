"""Command line: `tbench <url> ...` (TUI, or --plain), compare, history, profile, run."""
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from . import profiles, store
from .runner import read_body, run
from .stats import check, fmt, summarize, summary_lines

COMMANDS = ("compare", "history", "profile", "run")


def parse_headers(items):
    headers = {}
    for item in items or []:
        if ":" not in item:
            raise SystemExit(f"bad --header {item!r}, use 'Name: value'")
        k, v = item.split(":", 1)
        headers[k.strip()] = os.path.expandvars(v.strip())
    return headers


def add_run_options(p, url=True):
    if url:
        p.add_argument("url")
    p.add_argument("--body-file", help="JSON file to send as the body")
    p.add_argument("-n", type=int, default=None, help="measured calls (default 10)")
    p.add_argument("--method", default=None, help="HTTP method (default POST)")
    p.add_argument("--timeout", type=float, default=None, help="seconds before a call counts as timeout (default 30)")
    p.add_argument("--header", action="append", default=[], help="'Name: value', may repeat; $VARS are expanded")
    p.add_argument("--warmup", type=int, default=None, help="calls to make and throw away first")
    p.add_argument("--concurrency", type=int, default=None, help="calls in flight at once (default 1)")
    p.add_argument("--plain", action="store_true", help="print lines instead of the TUI")
    p.add_argument("--save", nargs="?", const="", default=None, help="save result JSON (default ~/.tbench/results/)")
    p.add_argument("--log", help="append one JSON line per call to this file")
    p.add_argument("--max-p95", type=float, default=None, help="FAIL (exit 1) if p95 seconds is above this")
    p.add_argument("--max-failures", type=int, default=None, help="FAIL (exit 1) if failures are above this")
    p.add_argument("--pick", metavar="DIR", help="choose the body from *.json in DIR (TUI)")


def settings_from(args, base=None):
    s = dict(base or {})
    for key in ("url", "body_file", "n", "method", "timeout", "warmup", "concurrency", "max_p95", "max_failures"):
        value = getattr(args, key, None)
        if value is not None:
            s[key] = value
    if getattr(args, "header", None):
        s["headers"] = args.header
    s.setdefault("n", 10)
    s.setdefault("method", "POST")
    s.setdefault("timeout", 30.0)
    s.setdefault("warmup", 0)
    s.setdefault("concurrency", 1)
    return s


def execute(s, plain, save_to, log_path, pick=None):
    headers = parse_headers(s.get("headers"))
    started = datetime.now().astimezone().isoformat(timespec="seconds")
    if not plain:
        from .app import BenchApp
        app = BenchApp(s, headers, pick=pick)
        app.run()
        results, body = app.results, app.body
        if not results:
            return 0
    else:
        body = read_body(s.get("body_file"))
        results = []
        log = open(log_path, "a", encoding="utf-8") if log_path else None
        print(f"{s['method']} {s['url']}  n={s['n']} concurrency={s['concurrency']} warmup={s['warmup']}")
        try:
            for r in run(s["url"], body, s["n"], s["method"], headers, s["timeout"], s["warmup"], s["concurrency"]):
                results.append(r)
                if log:
                    store.log_line(log, r)
                label = f"w{r['i']}" if r["warmup"] else f"#{r['i']}"
                status = r["status"] if r["status"] is not None else r["error_kind"]
                note = " ".join(x for x in (r["note"], r["error_kind"] if r["status"] else "") if x)
                print(f"{label:>4} {status!s:>8} {fmt(r['seconds']):>8}s  {note}".rstrip())
        finally:
            if log:
                log.close()
    if log_path and not plain:
        with open(log_path, "a", encoding="utf-8") as log:
            for r in results:
                store.log_line(log, r)
    measured = [r for r in results if not r["warmup"]]
    summary = summarize(measured, s["n"])
    for line in summary_lines(summary):
        print(line)
    if save_to is not None:
        record = store.build_record(s["url"], s["method"], body, headers, s["n"], s["concurrency"],
                                    s["warmup"], started, results)
        print(f"saved {store.save(record, save_to or None)}")
    if s.get("max_p95") is not None or s.get("max_failures") is not None:
        passed, line = check(summary, s.get("max_p95"), s.get("max_failures"))
        print(line)
        return 0 if passed else 1
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] in COMMANDS:
        return sys.exit(sub_main(argv))
    p = argparse.ArgumentParser(prog="tbench", description="Call a URL many times and show how long each call took. "
                                "Also: tbench compare A B | history | profile save/list | run NAME")
    add_run_options(p)
    args = p.parse_args(argv)
    sys.exit(execute(settings_from(args), args.plain, args.save, args.log, args.pick))


def sub_main(argv):
    p = argparse.ArgumentParser(prog="tbench")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compare", help="compare two saved results")
    c.add_argument("a")
    c.add_argument("b")
    sub.add_parser("history", help="list saved results, newest first")
    prof = sub.add_parser("profile", help="save or list named settings")
    psub = prof.add_subparsers(dest="action", required=True)
    ps = psub.add_parser("save")
    ps.add_argument("name")
    add_run_options(ps)
    psub.add_parser("list")
    r = sub.add_parser("run", help="run a saved profile")
    r.add_argument("name")
    add_run_options(r, url=False)
    args = p.parse_args(argv)

    if args.cmd == "compare":
        for line in store.compare(store.load(args.a), store.load(args.b)):
            print(line)
        return 0
    if args.cmd == "history":
        rows = store.history()
        print(f"{'started':19}  {'n':>3}  {'p50':>7}  {'p95':>7}  {'fail':>4}  url")
        for started, url, n, p50, p95, failures, _ in rows:
            print(f"{started:19}  {n:>3}  {p50:>7}  {p95:>7}  {failures:>4}  {url}")
        return 0
    if args.cmd == "profile" and args.action == "list":
        for name, values in profiles.load_all().items():
            print(f"{name:12} {values.get('url')}  body={values.get('body_file', '-')}  n={values.get('n', 10)}")
        return 0
    if args.cmd == "profile":
        s = {k: v for k, v in vars(args).items() if k in profiles.FIELDS and v is not None}
        if s.get("body_file"):
            s["body_file"] = str(Path(s["body_file"]).resolve())
        safe = []
        for h in args.header:
            name, _, value = h.partition(":")
            if store.mask_headers({name: 1})[name] == "***" and "$" not in value:
                print(f"note: {name.strip()} is kept as *** — pass it as an env var, e.g. 'Authorization: Bearer $MY_KEY'")
                value = " ***"
            safe.append(f"{name}:{value}")
        s["headers"] = safe
        print(f"saved {args.name} to {profiles.save(args.name, s)}")
        return 0
    base = profiles.load_all().get(args.name)
    if base is None:
        print(f"no profile {args.name!r} in {profiles.path()}")
        return 2
    return execute(settings_from(args, base), args.plain, args.save, args.log, args.pick)
