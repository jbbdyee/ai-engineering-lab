"""Read and clean n8n workflow JSON: drop values that change without meaning (R2), find secrets (R7)."""
import json
import re
from pathlib import Path

NOISE = {"id", "position", "webhookId", "versionId", "meta", "pinData", "updatedAt", "createdAt", "active", "shared", "tags"}
SECRET = re.compile(r"\b(sk-[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|xox[abp]-[A-Za-z0-9-]{10,})")


class NotWorkflow(ValueError):
    pass


def is_workflow(data) -> bool:
    return isinstance(data, dict) and isinstance(data.get("nodes"), list) and isinstance(data.get("connections"), dict)


def load(path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise NotWorkflow(f"{path}: {error}") from error
    if not is_workflow(data):
        raise NotWorkflow(f"{path}: not an n8n workflow (needs nodes and connections)")
    return data


def parse(text: str, label: str = "workflow") -> dict:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise NotWorkflow(f"{label}: {error}") from error
    if not is_workflow(data):
        raise NotWorkflow(f"{label}: not an n8n workflow")
    return data


def clean(workflow: dict) -> dict:
    """Same meaning → same JSON: no ids, positions or export stamps; nodes sorted by name."""
    nodes = []
    for node in workflow.get("nodes", []):
        nodes.append({k: v for k, v in node.items() if k not in NOISE})
    nodes.sort(key=lambda n: str(n.get("name", "")))
    out = {k: v for k, v in workflow.items() if k not in NOISE | {"nodes"}}
    out["nodes"] = nodes
    return out


def dumps(workflow: dict) -> str:
    return json.dumps(clean(workflow), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def find_secrets(text: str) -> list[str]:
    """Masked secret-looking values (sk-… keys etc.). Credential references (id · name) are fine."""
    return [m.group(0)[:5] + "…" + m.group(0)[-2:] for m in SECRET.finditer(text)]
