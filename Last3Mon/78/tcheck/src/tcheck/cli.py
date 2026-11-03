"""tcheck commands: check · gate · ui. Exit codes (R12): 0 ok · 1 cannot read · 2 usage · 4 batch rejected by the gate."""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

from . import checks, load

EXIT_OK, EXIT_READ, EXIT_USAGE, EXIT_REJECTED = 0, 1, 2, 4


class Parser(argparse.ArgumentParser):
    def error(self, message):  # usage mistakes are exit code 2, with the message on stderr
        self.print_usage(sys.stderr)
        print(f"tcheck: {message}", file=sys.stderr)
        sys.exit(EXIT_USAGE)


def common(p: argparse.ArgumentParser) -> None:
    p.add_argument("file", help="rows: .csv, a JSON list, {\"items\": [...]} or a day 78 request {\"schema\", \"batch\", \"csv\" | \"items\"}")
    p.add_argument("--schema", default="", help="schema name in the data API (faq · employee · ticket); default: the file's \"schema\"")
    p.add_argument("--schema-file", help="read the schema from a JSON file instead of the data API")
    p.add_argument("--url", default=os.environ.get("TCHECK_URL"), help="data API base, e.g. http://localhost:8800 ($TCHECK_URL)")
    p.add_argument("--batch", default="", help="batch name (default: the file's \"batch\" or its file name)")
    p.add_argument("--content", action="append", default=[], metavar="FIELD",
                   help="also apply the content rules (pii · external_link) to this text field (R8), e.g. --content answer")
    p.add_argument("--json", action="store_true", help="print JSON in the shape of n8n my-check (R5)")


def load_all(args) -> tuple[list, dict, dict]:
    rows, meta = load.read_rows(args.file)
    name = args.schema or meta.get("schema", "")
    if not args.schema_file and not name:
        raise SystemExit(usage("which schema? give --schema NAME (or a request file with \"schema\") or --schema-file"))
    schema = load.read_schema(name, args.url, args.schema_file)
    result = checks.check(rows, schema, args.batch or meta.get("batch", ""), tuple(args.content))
    return rows, schema, result


def usage(message: str) -> int:
    print(f"tcheck: {message}", file=sys.stderr)
    return EXIT_USAGE


def write_rows(path: str, rows: list[dict]) -> None:
    """R6: .csv keeps columns in first-seen order, anything else is a JSON list."""
    target = Path(path)
    if target.suffix.lower() == ".csv":
        cols: list[str] = []
        for row in rows:
            cols += [c for c in row if c not in cols]
        with target.open("w", encoding="utf-8", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=cols)
            writer.writeheader()
            writer.writerows([{c: (json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v)
                               for c, v in row.items()} for row in rows])
    else:
        target.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def print_result(r: dict, fixes: dict | None) -> None:
    print(f"{r['schema']} · {r['batch']} · {r['total']} rows · valid {r['valid']} · invalid {r['invalid']} · score {checks.score(r)}")
    for row in r["rows"]:
        if not row["ok"]:
            print(f"  {row['row']:>3}  {row['key'] or '-':<26} {', '.join(row['errors'])}")
    if r["codes"]:
        print("codes: " + " · ".join(f"{k} {v}" for k, v in sorted(r["codes"].items(), key=lambda kv: (-kv[1], kv[0]))))
    if fixes:
        print(fixes["message"])
        for item in fixes["fix_list"]:
            print(f"  {item['row']:>3}  " + " / ".join(item["fix"]))


def main(argv: list[str] | None = None) -> int:
    parser = Parser(prog="tcheck", description="Check CSV · JSON rows against a day 78 data schema, like n8n my-check.")
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("check", help="rows · codes · valid (R1 · R2 · R3 · R5), clean / rejected files (R6)")
    common(p)
    p.add_argument("--out", help="write the clean rows here (.csv or .json)")
    p.add_argument("--rejects", help="write the rejected rows with an 'errors' column here")
    p.add_argument("--fix", action="store_true", help="add the fix list and the one-line message (R9)")
    p.add_argument("--log", action="store_true", help="write one line to the data API quality log (R10)")
    p = commands.add_parser("gate", help="the batch gate: exit code 4 when invalid / total is above --max-invalid (R7)")
    common(p)
    p.add_argument("--max-invalid", type=float, default=0.3, help="limit for invalid / total, equal passes (default 0.3)")
    p = commands.add_parser("ui", help="the TUI: problem rows · by code · clean rows (R11)")
    common(p)
    p.add_argument("--out", help="where [e] writes the clean rows (default: <file>.clean.csv or .json)")
    try:
        args = parser.parse_args(argv)
    except SystemExit as stop:                    # --help is 0, usage mistakes are 2
        return int(stop.code or 0)

    try:
        rows, schema, r = load_all(args)
        if args.command == "ui":
            from .app import CheckApp
            CheckApp(args, rows, schema, r).run()
            return EXIT_OK
        if args.command == "gate":
            g = checks.gate(r, args.max_invalid)
            out = {**{k: r[k] for k in ("schema", "batch", "total", "valid", "invalid", "codes")}, **g}
            if args.json:
                print(json.dumps(out, ensure_ascii=False, indent=2))
            else:
                mark = "✔ accepted" if g["accepted"] else "✘ rejected"
                print(f"{mark} · {r['batch']} · invalid {r['invalid']}/{r['total']} = {g['invalid_ratio']} (limit {args.max_invalid})")
            return EXIT_OK if g["accepted"] else EXIT_REJECTED
        fixes = checks.fix_list(r, schema) if args.fix else None
        if args.out or args.rejects:
            clean, rejects = checks.split(rows, r)
            if args.out:
                write_rows(args.out, clean)
            if args.rejects:
                write_rows(args.rejects, rejects)
        if args.log:
            if not args.url:
                return usage("--log needs --url (or $TCHECK_URL)")
            load.post_log(args.url, checks.quality_entry(r))
        if args.json:
            print(json.dumps({**r, **(fixes or {})}, ensure_ascii=False, indent=2))
        else:
            print_result(r, fixes)
            if args.out:
                print(f"clean rows → {args.out}")
            if args.rejects:
                print(f"rejected rows → {args.rejects}")
            if args.log:
                print(f"quality log ← {r['batch']} · {r['schema']} · score {checks.score(r)}")
        return EXIT_OK
    except load.LoadError as error:
        print(f"tcheck: cannot read: {error}", file=sys.stderr)
        return EXIT_READ
    except SystemExit as stop:
        return int(stop.code or 0)


if __name__ == "__main__":
    sys.exit(main())
