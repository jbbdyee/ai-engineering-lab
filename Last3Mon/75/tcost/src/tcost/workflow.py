"""LLM steps of an n8n workflow (R4): which node calls which model, and the fixed text it sends every time."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from . import tokens

CHAT_URL = "chat/completions"
MODEL = re.compile(r"""\bmodel['"]?\s*:\s*['"]([\w.\-]+)['"]""")
SYSTEM = re.compile(r"""role['"]?\s*:\s*['"]system['"]\s*,\s*['"]?content['"]?\s*:\s*("(?:[^"\\]|\\.)*")""", re.S)
LIMIT = re.compile(r"""\bmax_(?:completion_)?tokens['"]?\s*:\s*(\d+)""")


class NotWorkflow(ValueError):
    pass


@dataclass
class Step:
    node: str
    model: str
    system: str          # the system prompt as sent (empty when it is built at run time)
    system_tokens: int
    max_out: int | None  # max_completion_tokens, if the node sets one
    dynamic: bool        # True when the system prompt comes from another node (counted as 0 here)


def is_workflow(data: object) -> bool:
    return isinstance(data, dict) and isinstance(data.get("nodes"), list) and isinstance(data.get("connections"), dict)


def load(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not is_workflow(data):
        raise NotWorkflow(f"{path}: not an n8n workflow (needs 'nodes' and 'connections')")
    return data


def _http_step(node: dict) -> Step | None:
    params = node.get("parameters") or {}
    if CHAT_URL not in str(params.get("url", "")):
        return None
    body = str(params.get("jsonBody", ""))
    model = MODEL.search(body)
    system = SYSTEM.search(body)
    limit = LIMIT.search(body)
    text = json.loads(system.group(1)) if system else ""
    return Step(node["name"], model.group(1) if model else "?", text, tokens.count(text),
                int(limit.group(1)) if limit else None, system is None)


def _agent_steps(workflow: dict) -> list[Step]:
    """AI Agent nodes (days 66~74): the model comes from the chat model node joined by ai_languageModel."""
    nodes = {n["name"]: n for n in workflow["nodes"]}
    model_of: dict[str, str] = {}
    for source, outputs in workflow["connections"].items():
        for link in (outputs.get("ai_languageModel") or [[]])[0]:
            value = ((nodes.get(source) or {}).get("parameters") or {}).get("model")
            model_of[link["node"]] = value.get("value", "?") if isinstance(value, dict) else str(value or "?")
    steps = []
    for node in workflow["nodes"]:
        if not node.get("type", "").endswith(".agent"):
            continue
        text = str(((node.get("parameters") or {}).get("options") or {}).get("systemMessage", ""))
        dynamic = "{{" in text
        text = "" if dynamic else text.removeprefix("=")
        steps.append(Step(node["name"], model_of.get(node["name"], "?"), text, tokens.count(text), None, dynamic))
    return steps


def llm_steps(workflow: dict) -> list[Step]:
    steps = [step for node in workflow["nodes"] if (step := _http_step(node))]
    return steps + _agent_steps(workflow)
