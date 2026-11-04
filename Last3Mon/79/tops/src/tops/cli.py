"""tops commands (R3): status · ask · brief · eval · audit · tools · ui. Exit codes: 0 ok · 1 cannot read · 2 usage · 4 red / eval gate fail."""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import client, view

EXIT_OK, EXIT_READ, EXIT_USAGE, EXIT_ALARM = 0, 1, 2, 4


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"tops: {message}", file=sys.stderr)
        sys.exit(EXIT_USAGE)


def common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--n8n", default=os.environ.get("TOPS_N8N"), help="n8n base, e.g. http://localhost:5678 ($TOPS_N8N)")
    p.add_argument("--json", action="store_true", help="print the n8n answer as JSON, unchanged")


def need_n8n(args) -> str:
    if not args.n8n:
        raise SystemExit(usage("give --n8n (or set $TOPS_N8N)"))
    return args.n8n


def usage(message: str) -> int:
    print(f"tops: {message}", file=sys.stderr)
    return EXIT_USAGE


def show(args, data, lines) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else "\n".join(lines))


def main(argv: list[str] | None = None) -> int:
    parser = Parser(prog="tops", description="The day 79 operations assistant in the terminal. It reads n8n my-ops-* and never changes anything.")
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("status", help="areas · colors · numbers from my-ops-facts (R1 · R2 · R7), exit code 4 when overall is red")
    common(p)
    p.add_argument("--file", help="read the facts from a file instead of n8n")
    p.add_argument("--from", dest="date_from", default="")
    p.add_argument("--to", dest="date_to", default="")
    p = commands.add_parser("ask", help="one question to my-ops-ask (R4)")
    common(p)
    p.add_argument("question")
    p = commands.add_parser("brief", help="the markdown of my-ops-brief (R6)")
    common(p)
    p.add_argument("--from", dest="date_from", default="")
    p.add_argument("--to", dest="date_to", default="")
    p = commands.add_parser("eval", help="golden questions to my-ops-eval, exit code 4 when the gate fails (R9)")
    common(p)
    p.add_argument("file", help='{"cases": [...]} like requests/ops-golden.json')
    p.add_argument("--min-score", type=float)
    p = commands.add_parser("audit", help="the questions the assistant was asked (data API /audit) (R10)")
    p.add_argument("--api", default=os.environ.get("TOPS_API", "http://localhost:8800"))
    p.add_argument("--json", action="store_true")
    p = commands.add_parser("tools", help="earlier course tools as parts: tlog · tcheck (R8)")
    p.add_argument("--api", default=os.environ.get("TOPS_API", "http://localhost:8800"))
    p.add_argument("--from", dest="date_from", default="2026-10-26")
    p.add_argument("--to", dest="date_to", default="2026-10-30")
    p.add_argument("--json", action="store_true")
    p = commands.add_parser("ui", help="the TUI (R11)")
    common(p)
    p.add_argument("--file")
    p.add_argument("--api", default=os.environ.get("TOPS_API", "http://localhost:8800"))
    try:
        args = parser.parse_args(argv)
    except SystemExit as stop:
        return int(stop.code or 0)

    try:
        if args.command == "status":
            if not args.file and not args.n8n:
                return usage("give --n8n (or set $TOPS_N8N) or --file")
            f = client.facts(args.n8n, args.file, args.date_from, args.date_to)
            show(args, f, view.status_lines(f))
            return EXIT_ALARM if f.get("overall") == "red" else EXIT_OK
        if args.command == "ask":
            a = client.ask(need_n8n(args), args.question)
            show(args, a, view.answer_lines(a))
            return EXIT_OK
        if args.command == "brief":
            b = client.brief(need_n8n(args), args.date_from, args.date_to)
            show(args, b, [b.get("markdown", "")])
            return EXIT_OK
        if args.command == "eval":
            cases = client.read_json(args.file)
            cases = cases.get("cases", []) if isinstance(cases, dict) else cases
            e = client.evaluate(need_n8n(args), cases, args.min_score)
            if "error" in e:
                print(f"tops: {e['error']}", file=sys.stderr)
                return EXIT_USAGE
            lines = [f"{e['passed']}/{e['total']} · score {e['score']}" + (f" · gate {e['gate']} (min {e['min_score']})" if "gate" in e else "")]
            lines += [f"  ✘ {x['question']} · area {x.get('area')} · " + " ".join(k for k in ("area_ok", "refused_ok", "number_ok", "grounded") if not x.get(k))
                      for x in e.get("failed", [])]
            show(args, e, lines)
            return EXIT_ALARM if e.get("gate") == "fail" else EXIT_OK
        if args.command == "audit":
            events = client.audit(args.api).get("events", [])
            lines = [f"{len(events)} question(s)"] + [
                f"  {e.get('area', '-'):<8} {e.get('router', '-'):<8} {'refused ' + str(e.get('reason')) if e.get('refused') else 'answered'}  {e.get('question')}"
                for e in events]
            show(args, {"events": events}, lines)
            return EXIT_OK
        if args.command == "tools":
            parts = [view.tool("tlog", ["slo", "--url", args.api, "--from", args.date_from, "--to", args.date_to, "--json"]),
                     view.tool("tcheck", ["--help"])]
            show(args, parts, [view.tool_line(p) for p in parts])
            return EXIT_OK
        from .app import OpsApp
        if not args.file and not args.n8n:
            return usage("give --n8n (or set $TOPS_N8N) or --file")
        OpsApp(args).run()
        return EXIT_OK
    except client.ReadError as error:
        print(f"tops: cannot read: {error}", file=sys.stderr)
        return EXIT_READ
    except SystemExit as stop:
        return int(stop.code or 0)


if __name__ == "__main__":
    sys.exit(main())
