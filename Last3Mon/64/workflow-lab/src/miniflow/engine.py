"""Load, validate and run a workflow made of nodes and edges."""

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from miniflow import llm, memory, tools
from miniflow.template import render

NODE_TYPES = {"input", "llm", "tool", "memory_read", "memory_write", "output"}
REQUIRED_FIELDS = {
    "llm": ["prompt"],
    "tool": ["tool"],
    "memory_read": ["key"],
    "memory_write": ["key", "value"],
    "output": ["value"],
}


class WorkflowError(ValueError):
    pass


@dataclass
class Workflow:
    name: str
    nodes: dict[str, dict[str, Any]]
    edges: list[tuple[str, str]]
    description: str = ""
    inputs: list[str] = field(default_factory=list)

    def order(self) -> list[str]:
        """Topological order of node ids (Kahn's algorithm, file order breaks ties)."""
        indegree = {node_id: 0 for node_id in self.nodes}
        for _, target in self.edges:
            indegree[target] += 1
        ready = [node_id for node_id in self.nodes if indegree[node_id] == 0]
        ordered = []
        while ready:
            current = ready.pop(0)
            ordered.append(current)
            for source, target in self.edges:
                if source == current:
                    indegree[target] -= 1
                    if indegree[target] == 0:
                        ready.append(target)
        if len(ordered) != len(self.nodes):
            raise WorkflowError("Edges contain a cycle. Day 64 workflows must flow in one direction.")
        return ordered

    def to_mermaid(self) -> str:
        shapes = {
            "input": ('[/"', '"/]'),
            "llm": ('{{"', '"}}'),
            "tool": ('["', '"]'),
            "memory_read": ('[("', '")]'),
            "memory_write": ('[("', '")]'),
            "output": ('[\\"', '"\\]'),
        }
        lines = ["flowchart LR"]
        for node_id, node in self.nodes.items():
            left, right = shapes[node["type"]]
            label = f"{node_id}<br/>{node['type']}"
            if node["type"] == "tool":
                label += f": {node['tool']}"
            lines.append(f"  {node_id}{left}{label}{right}")
        lines += [f"  {source} --> {target}" for source, target in self.edges]
        return "\n".join(lines)


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
        nodes[node_id] = node
    if not nodes:
        raise WorkflowError("Workflow has no nodes")

    edges = [tuple(edge) for edge in data.get("edges", [])]
    for source, target in edges:
        for node_id in (source, target):
            if node_id not in nodes:
                raise WorkflowError(f"Edge {source} -> {target} points to unknown node '{node_id}'")
    workflow = Workflow(
        name=data.get("name", Path(path).stem),
        description=data.get("description", ""),
        inputs=data.get("inputs", []),
        nodes=nodes,
        edges=edges,
    )
    workflow.order()
    return workflow


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
    raise WorkflowError(f"Unsupported node type: {kind}")


def run_workflow(workflow: Workflow, inputs: dict[str, Any], verbose: bool = True) -> dict[str, Any]:
    missing = [name for name in workflow.inputs if name not in inputs]
    if missing:
        raise WorkflowError(f"Missing inputs: {', '.join(missing)} (pass with --input name=value)")

    context: dict[str, Any] = {"input": inputs, "nodes": {}}
    trace: list[dict[str, Any]] = []
    order = workflow.order()
    result: Any = None
    for index, node_id in enumerate(order, start=1):
        node = workflow.nodes[node_id]
        started = time.perf_counter()
        step = {"step": index, "id": node_id, "type": node["type"]}
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
        step.update(status="ok", ms=elapsed, output=output, **extra)
        trace.append(step)
        if node["type"] == "output":
            result = output
        if verbose:
            preview = json.dumps(output, ensure_ascii=False)
            print(f"[{index}/{len(order)}] {node_id:<14} {node['type']:<12} ok {elapsed:>6}ms  {preview[:70]}")
    return {"workflow": workflow.name, "status": "completed", "result": result, "trace": trace}
