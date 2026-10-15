"""Command line entry point: uv run miniflow <command> ..."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from miniflow import memory, tools
from miniflow.engine import WorkflowError, load_workflow, run_workflow


def parse_inputs(pairs: list[str]) -> dict[str, str]:
    inputs = {}
    for pair in pairs:
        if "=" not in pair:
            raise WorkflowError(f"Input must look like name=value, got '{pair}'")
        name, value = pair.split("=", 1)
        inputs[name.strip()] = value
    return inputs


def cmd_run(args: argparse.Namespace) -> int:
    workflow = load_workflow(args.flow)
    print(f"Workflow: {workflow.name}")
    if workflow.description:
        print(f"  {workflow.description}")
    print("-" * 72)
    report = run_workflow(workflow, parse_inputs(args.input))
    print("-" * 72)
    print(f"Status: {report['status']}")
    print("Result:")
    result = report["result"]
    print(result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, indent=2))

    runs = Path("runs")
    runs.mkdir(exist_ok=True)
    log_file = runs / f"{datetime.now():%Y%m%d-%H%M%S}-{Path(args.flow).stem}.json"
    log_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Trace saved: {log_file}")
    return 0 if report["status"] == "completed" else 1


def cmd_validate(args: argparse.Namespace) -> int:
    workflow = load_workflow(args.flow)
    print(f"OK: {workflow.name} ({len(workflow.nodes)} nodes, {len(workflow.edges)} edges)")
    print("Execution order: " + " -> ".join(workflow.order()))
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    print(load_workflow(args.flow).to_mermaid())
    return 0


def cmd_tools(_: argparse.Namespace) -> int:
    for name, doc in tools.describe_tools():
        print(f"{name:<14} {doc}")
    return 0


def cmd_check(_: argparse.Namespace) -> int:
    import os
    import time

    from miniflow import llm

    provider = os.getenv("MINIFLOW_LLM", "mock").lower()
    print(f"MINIFLOW_LLM : {provider}")
    print(f".env         : {llm.envfile.LOADED[0] if llm.envfile.LOADED else '(none)'}")
    if provider == "openai":
        print(f"OPENAI_MODEL : {os.getenv('OPENAI_MODEL', 'gpt-4.1-mini')}")
        print(f"API key      : {'set' if os.getenv('OPENAI_API_KEY') else 'MISSING (put OPENAI_API_KEY in .env)'}")
    if provider == "ollama" or os.getenv("MINIFLOW_LLM_FALLBACK", "").lower() == "ollama":
        print(f"OLLAMA_HOST  : {os.getenv('OLLAMA_HOST', 'http://localhost:11434')}")
        print(f"OLLAMA_MODEL : {os.getenv('OLLAMA_MODEL', 'gemma3:4b')}")
    if os.getenv("MINIFLOW_LLM_FALLBACK"):
        print(f"FALLBACK     : {os.getenv('MINIFLOW_LLM_FALLBACK')}")
    started = time.perf_counter()
    try:
        reply, used = llm.complete({"temperature": 0}, "Reply with exactly one word: ready", "", {})
    except llm.LLMError as error:
        print(f"FAILED: {error}")
        return 1
    print(f"Reply ({used}, {time.perf_counter() - started:.1f}s): {reply[:80]}")
    return 0


def cmd_memory(args: argparse.Namespace) -> int:
    if args.clear:
        memory.clear()
        print("Memory cleared")
        return 0
    path = memory.memory_path()
    print(path.read_text(encoding="utf-8") if path.exists() else "{}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="miniflow", description="Run JSON-defined AI workflows")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run a workflow file")
    run.add_argument("flow")
    run.add_argument("--input", "-i", action="append", default=[], metavar="NAME=VALUE")
    run.set_defaults(func=cmd_run)

    validate = sub.add_parser("validate", help="check a workflow file without running it")
    validate.add_argument("flow")
    validate.set_defaults(func=cmd_validate)

    show = sub.add_parser("show", help="print the workflow as a Mermaid diagram")
    show.add_argument("flow")
    show.set_defaults(func=cmd_show)

    sub.add_parser("tools", help="list available tools").set_defaults(func=cmd_tools)
    sub.add_parser("check", help="check the configured LLM provider").set_defaults(func=cmd_check)

    mem = sub.add_parser("memory", help="show or clear the memory store")
    mem.add_argument("--clear", action="store_true")
    mem.set_defaults(func=cmd_memory)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (WorkflowError, FileNotFoundError, json.JSONDecodeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
