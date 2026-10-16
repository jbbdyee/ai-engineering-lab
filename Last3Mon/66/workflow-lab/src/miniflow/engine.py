"""Load, validate and run a workflow made of nodes and edges.

Day 65 adds branching: `condition` (true/false) and `switch` (one case per value)
nodes, and edges that carry a branch label: ["check", "draft", "true"].
"""

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from miniflow import llm, memory, tools
from miniflow.template import render

NODE_TYPES = {"input", "llm", "tool", "memory_read", "memory_write", "output", "condition", "switch"}
BRANCH_TYPES = {"condition", "switch"}
REQUIRED_FIELDS = {
    "llm": ["prompt"],
    "tool": ["tool"],
    "memory_read": ["key"],
    "memory_write": ["key", "value"],
    "output": ["value"],
    "condition": ["check"],
    "switch": ["value", "cases"],
}
CHECK_OPS = {"equals", "not_equals", "contains", "not_empty", "empty", "in", "gt", "lt"}

Edge = tuple[str, str, str | None]


class WorkflowError(ValueError):
    pass


@dataclass
class Workflow:
    name: str
    nodes: dict[str, dict[str, Any]]
    edges: list[Edge]
    description: str = ""
    inputs: list[str] = field(default_factory=list)

    def order(self) -> list[str]:
        """Topological order of node ids (Kahn's algorithm, file order breaks ties)."""
        indegree = {node_id: 0 for node_id in self.nodes}
        for _, target, _ in self.edges:
            indegree[target] += 1
        ready = [node_id for node_id in self.nodes if indegree[node_id] == 0]
        ordered = []
        while ready:
            current = ready.pop(0)
            ordered.append(current)
            for source, target, _ in self.edges:
                if source == current:
                    indegree[target] -= 1
                    if indegree[target] == 0:
                        ready.append(target)
        if len(ordered) != len(self.nodes):
            raise WorkflowError("Edges contain a cycle. Workflows must flow in one direction.")
        return ordered

    def to_mermaid(self) -> str:
        shapes = {
            "input": ('[/"', '"/]'),
            "llm": ('{{"', '"}}'),
            "tool": ('["', '"]'),
            "memory_read": ('[("', '")]'),
            "memory_write": ('[("', '")]'),
            "output": ('[\\"', '"\\]'),
            "condition": ('{"', '"}'),
            "switch": ('{"', '"}'),
        }
        lines = ["flowchart LR"]
        for node_id, node in self.nodes.items():
            left, right = shapes[node["type"]]
            label = f"{node_id}<br/>{node['type']}"
            if node["type"] == "tool":
                label += f": {node['tool']}"
            lines.append(f"  {node_id}{left}{label}{right}")
        for source, target, branch in self.edges:
            arrow = f" -->|{branch}| " if branch is not None else " --> "
            lines.append(f"  {source}{arrow}{target}")
        return "\n".join(lines)


def _parse_edge(raw: list[Any]) -> Edge:
    if not isinstance(raw, list) or len(raw) not in (2, 3):
        raise WorkflowError(f"Edge must be [source, target] or [source, target, branch]: {raw}")
    return (raw[0], raw[1], str(raw[2]) if len(raw) == 3 else None)


def load_workflow(path: str | Path) -> Workflow:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    nodes: dict[str, dict[str, Any]] = {}
    for node in data.get("nodes", []):
        node_id = node.get("id")
        if not node_id:
            raise WorkflowError("Every node needs an 'id'")
        if node_id in nodes:
            raise WorkflowError(f"Duplicate node id: {node_id}")
        if node.get("type") not in NODE_TYPES:
            raise WorkflowError(f"Node '{node_id}' has unknown type '{node.get('type')}'. Use one of {sorted(NODE_TYPES)}")
        missing = [name for name in REQUIRED_FIELDS.get(node["type"], []) if name not in node]
        if missing:
            raise WorkflowError(f"Node '{node_id}' ({node['type']}) is missing: {', '.join(missing)}")
        if node["type"] == "tool" and node["tool"] not in tools.TOOLS:
            raise WorkflowError(f"Node '{node_id}' uses unknown tool '{node['tool']}'")
        if node["type"] == "condition" and node["check"].get("op") not in CHECK_OPS:
            raise WorkflowError(f"Node '{node_id}' uses unknown check op. Use one of {sorted(CHECK_OPS)}")
        nodes[node_id] = node
    if not nodes:
        raise WorkflowError("Workflow has no nodes")

    edges = [_parse_edge(edge) for edge in data.get("edges", [])]
    for source, target, branch in edges:
        for node_id in (source, target):
            if node_id not in nodes:
                raise WorkflowError(f"Edge {source} -> {target} points to unknown node '{node_id}'")
        kind = nodes[source]["type"]
        if branch is not None and kind not in BRANCH_TYPES:
            raise WorkflowError(f"Edge {source} -> {target} has branch '{branch}' but '{source}' is a {kind} node")
        if kind == "condition" and branch not in ("true", "false"):
            raise WorkflowError(f"Edge {source} -> {target} needs branch 'true' or 'false'")
        if kind == "switch" and branch not in [*map(str, nodes[source]["cases"]), "default"]:
            raise WorkflowError(f"Edge {source} -> {target} needs a branch from cases {nodes[source]['cases']} or 'default'")
    workflow = Workflow(
        name=data.get("name", Path(path).stem),
        description=data.get("description", ""),
        inputs=data.get("inputs", []),
        nodes=nodes,
        edges=edges,
    )
    workflow.order()
    return workflow


def evaluate_check(check: dict[str, Any], context: dict[str, Any]) -> bool:
    left = render(check.get("left", ""), context)
    right = render(check.get("right"), context)
    op = check["op"]
    if op == "equals":
        return left == right
    if op == "not_equals":
        return left != right
    if op == "contains":
        return str(right) in str(left)
    if op == "empty":
        return left in (None, "", [], {})
    if op == "not_empty":
        return left not in (None, "", [], {})
    if op == "in":
        return left in (right or [])
    if op == "gt":
        return float(left) > float(right)
    if op == "lt":
        return float(left) < float(right)
    raise WorkflowError(f"Unsupported check op: {op}")


def run_node(node: dict[str, Any], context: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    """Execute one node. Returns (output, extra trace info)."""
    kind = node["type"]
    if kind == "input":
        return context["input"], {}
    if kind == "llm":
        system = str(render(node.get("system", ""), context))
        prompt = str(render(node["prompt"], context))
        reply, provider = llm.complete(node, prompt, system, context)
        return reply, {"provider": provider, "prompt": prompt}
    if kind == "tool":
        args = render(node.get("args", {}), context)
        return tools.call_tool(node["tool"], args), {"args": args}
    if kind == "memory_read":
        key = str(render(node["key"], context))
        return memory.read(key), {"key": key}
    if kind == "memory_write":
        key = str(render(node["key"], context))
        return memory.write(key, render(node["value"], context)), {"key": key}
    if kind == "output":
        return render(node["value"], context), {}
    if kind == "condition":
        passed = evaluate_check(node["check"], context)
        return {"result": passed, "branch": "true" if passed else "false"}, {}
    if kind == "switch":
        value = render(node["value"], context)
        cases = [str(case) for case in node["cases"]]
        branch = str(value) if str(value) in cases else "default"
        return {"value": value, "branch": branch}, {}
    raise WorkflowError(f"Unsupported node type: {kind}")


def _is_active(node_id: str, workflow: Workflow, status: dict[str, str], context: dict[str, Any]) -> bool:
    """Decide whether a node runs.

    - A branch edge works as a gate: if its source was skipped or chose another
      branch, the node is skipped.
    - Otherwise the node runs if at least one incoming edge is taken, so a node
      where two exclusive branches meet again (plain edges) still runs.
    """
    incoming = [(source, branch) for source, target, branch in workflow.edges if target == node_id]
    if not incoming:
        return True
    taken = False
    for source, branch in incoming:
        ran = status.get(source) == "ok"
        if branch is not None:
            if not ran or context["nodes"][source]["output"].get("branch") != branch:
                return False
            taken = True
        elif ran:
            taken = True
    return taken


def run_workflow(workflow: Workflow, inputs: dict[str, Any], verbose: bool = True) -> dict[str, Any]:
    missing = [name for name in workflow.inputs if name not in inputs]
    if missing:
        raise WorkflowError(f"Missing inputs: {', '.join(missing)} (pass with --input name=value)")

    context: dict[str, Any] = {"input": inputs, "nodes": {}}
    trace: list[dict[str, Any]] = []
    status: dict[str, str] = {}
    order = workflow.order()
    result: Any = None
    for index, node_id in enumerate(order, start=1):
        node = workflow.nodes[node_id]
        step = {"step": index, "id": node_id, "type": node["type"]}
        if not _is_active(node_id, workflow, status, context):
            status[node_id] = "skipped"
            step["status"] = "skipped"
            trace.append(step)
            if verbose:
                print(f"[{index}/{len(order)}] {node_id:<14} {node['type']:<12} skipped (branch not taken)")
            continue
        started = time.perf_counter()
        try:
            output, extra = run_node(node, context)
        except Exception as error:
            step.update(status="failed", error=f"{type(error).__name__}: {error}")
            trace.append(step)
            if verbose:
                print(f"[{index}/{len(order)}] {node_id:<14} {node['type']:<12} FAILED  {step['error']}")
            return {"workflow": workflow.name, "status": "failed", "result": None, "trace": trace}
        elapsed = round((time.perf_counter() - started) * 1000, 1)
        context["nodes"][node_id] = {"output": output}
        status[node_id] = "ok"
        step.update(status="ok", ms=elapsed, output=output, **extra)
        trace.append(step)
        if node["type"] == "output":
            result = output
        if verbose:
            preview = json.dumps(output, ensure_ascii=False)
            print(f"[{index}/{len(order)}] {node_id:<14} {node['type']:<12} ok {elapsed:>6}ms  {preview[:70]}")
    return {"workflow": workflow.name, "status": "completed", "result": result, "trace": trace}
