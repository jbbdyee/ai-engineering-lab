"""tlog commands (R12): summary · problems · slo · compare · weekly · ui. Exit codes: 0 ok · 1 cannot read · 2 usage · 4 SLO breach."""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import load, metrics

EXIT_OK, EXIT_READ, EXIT_USAGE, EXIT_BREACH = 0, 1, 2, 4


class Parser(argparse.ArgumentParser):
    def error(self, message):  # usage mistakes are exit code 2, with the message on stderr
        self.print_usage(sys.stderr)
        print(f"tlog: {message}", file=sys.stderr)
        sys.exit(EXIT_USAGE)


def source_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--file", help="run logs: a JSON list, {\"logs\": [...]} or JSON Lines (also tretry's ~/.tretry/log.jsonl)")
    p.add_argument("--url", default=os.environ.get("TLOG_URL"), help="data API base, e.g. http://localhost:8800 ($TLOG_URL)")
    p.add_argument("--from", dest="date_from", default="", help="first day, inclusive (2026-10-26)")
    p.add_argument("--to", dest="date_to", default="", help="last day, inclusive")
    p.add_argument("--tag", default="")
    p.add_argument("--source", default="all", choices=["all", "seed", "live"])
    p.add_argument("--json", action="store_true", help="print JSON with the names of AGENTS.md 3 (same as my-log-report)")


def rows_for(args, date_from=None, date_to=None) -> list[dict]:
    if not args.file and not args.url:
        raise SystemExit(usage("give --file or --url (or set $TLOG_URL)"))
    return load.read(args.file, args.url, args.date_from if date_from is None else date_from,
                     args.date_to if date_to is None else date_to, args.tag, args.source)


def usage(message: str) -> int:
    print(f"tlog: {message}", file=sys.stderr)
    return EXIT_USAGE


def limits_of(args) -> dict:
    out = {}
    for key, value in (("error_rate", args.error_rate), ("p95_ms", args.p95), ("unanswered_rate", args.unanswered)):
        if value is not None:
            out[key] = value
    return out


def print_summary(r: dict) -> None:
    print(f"{r['total']} runs · errors {r['errors']} ({metrics.percent(r['error_rate'])}) · p50 {r['p50_ms']}ms · p95 {r['p95_ms']}ms")
    print("route: " + " · ".join(f"{k} {v}" for k, v in sorted(r["by_route"].items(), key=lambda kv: -kv[1])))
    for day, d in r["by_day"].items():
        print(f"  {day}  {d['total']:>4} runs  errors {d['errors']:>3}  {metrics.percent(d['error_rate'])}")
    s = r["steps"]
    print(f"steps p95: faq {s['faq_ms']['p95']}ms ({s['faq_ms']['runs']}) · answer {s['answer_ms']['p95']}ms ({s['answer_ms']['runs']})"
          f" · cost ${r['cost_usd']} (${r['cost_per_run']}/run) · LLM calls {r['llm_calls']}")


def print_problems(r: dict) -> None:
    print("failures:")
    for f in r["failures"] or [{"count": 0, "node": "-", "message": "-"}]:
        print(f"  {f['count']:>4}  {f['node']}  {f['message']}")
    print("unanswered topics:")
    for u in r["unanswered_topics"]:
        print(f"  {u['count']:>4}  {u['topic']}")
    print("anomalies (>= 5 runs, >= 3 × error rate, >= 1 error):")
    for a in r["anomalies"]:
        print(f"  {a['hour']}  {a['errors']}/{a['total']}  {metrics.percent(a['error_rate'])}")
    print("asked again after an answer:")
    for t in r["repeat_topics"]:
        print(f"  {metrics.percent(t['repeat_rate']):>7}  {t['repeats']}/{t['answers']}  {t['topic']}")


def main(argv: list[str] | None = None) -> int:
    parser = Parser(prog="tlog", description="Run log analysis with the day 77 metric definitions.")
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("summary", help="runs · error rate · p50 · p95 · routes · days · steps · cost (R2 · R6)")
    source_args(p)
    p = commands.add_parser("problems", help="failure groups · unanswered topics · anomalies · repeat topics (R3 · R4)")
    source_args(p)
    p = commands.add_parser("slo", help="judge the SLO; exit code 4 when a metric is above its limit (R7)")
    source_args(p)
    p.add_argument("--error-rate", type=float)
    p.add_argument("--p95", type=float, help="ms")
    p.add_argument("--unanswered", type=float)
    p = commands.add_parser("compare", help="this period next to the previous one (R8)")
    source_args(p)
    p.add_argument("--prev-from", required=True)
    p.add_argument("--prev-to", required=True)
    p = commands.add_parser("weekly", help="the weekly report as Markdown, no LLM (R10)")
    source_args(p)
    p.add_argument("--prev-from", required=True)
    p.add_argument("--prev-to", required=True)
    p = commands.add_parser("ui", help="the TUI (R11)")
    source_args(p)
    args = parser.parse_args(argv)

    try:
        if args.command == "ui":
            if not args.file and not args.url:
                return usage("give --file or --url (or set $TLOG_URL)")
            from .app import LogApp
            LogApp(args).run()
            return EXIT_OK
        rows = rows_for(args)
        limits = limits_of(args) if args.command == "slo" else None
        r = metrics.report(rows, limits)
        if args.command in ("compare", "weekly"):
            prev = metrics.report(rows_for(args, args.prev_from, args.prev_to))
            if args.command == "compare":
                table = metrics.compare(r, prev)
                if args.json:
                    print(json.dumps(table, ensure_ascii=False, indent=2))
                else:
                    for row in table:
                        print(f"{row['metric']:<16} {row['prev']:>10} → {row['now']:>10}  ({row['change']:+g})")
                return EXIT_OK
            text = metrics.weekly_markdown(r, prev, args.date_from, args.date_to)
            print(json.dumps({"markdown": text}, ensure_ascii=False, indent=2) if args.json else text, end="" if not args.json else "\n")
            return EXIT_OK
    except load.LoadError as error:
        print(f"tlog: cannot read the logs: {error}", file=sys.stderr)
        return EXIT_READ
    except SystemExit as stop:
        return int(stop.code or 0)

    if args.command == "slo":
        out = {"ok": r["slo"]["ok"], "breaches": r["slo"]["breaches"], "limits": r["slo"]["limits"],
               "values": {k: r[k] for k in ("error_rate", "p95_ms", "unanswered_rate")}, "total": r["total"]}
        if args.json:
            print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            for key in ("error_rate", "p95_ms", "unanswered_rate"):
                mark = "✘" if key in out["breaches"] else "✔"
                print(f"{mark} {key:<16} {r[key]:>8} (limit {out['limits'][key]})")
            print("SLO ok" if out["ok"] else "SLO breach: " + ", ".join(out["breaches"]))
        return EXIT_OK if out["ok"] else EXIT_BREACH
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif args.command == "summary":
        print_summary(r)
    else:
        print_problems(r)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
