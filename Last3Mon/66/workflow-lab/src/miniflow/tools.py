"""Tools a workflow can call. Each tool reads local sample data, so no network is needed."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


class ToolError(RuntimeError):
    pass


def _load(name: str) -> Any:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def get_weather(city: str) -> dict[str, Any]:
    """Return today's sample weather for a city."""
    table = _load("weather.json")
    if city not in table:
        raise ToolError(f"Unknown city '{city}'. Available: {', '.join(table)}")
    return {"city": city, **table[city]}


def search_faq(query: str, top_k: int = 2) -> list[dict[str, Any]]:
    """Return FAQ entries ranked by keyword overlap with the query."""
    words = {word for word in query.lower().split() if len(word) > 1}
    scored = []
    for item in _load("faq.json"):
        keywords = {keyword.lower() for keyword in item["keywords"]}
        score = sum(1 for word in words if any(keyword in word or word in keyword for keyword in keywords))
        if score:
            scored.append({"score": score, **item})
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[: int(top_k)]


def count_chars(text: str) -> dict[str, int]:
    """Count characters and words of a text."""
    return {"chars": len(text), "words": len(text.split())}


def parse_actions(text: str) -> dict[str, Any]:
    """Parse an LLM answer into a clean list of action items (task, owner, due)."""
    cleaned = str(text).strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").split("\n", 1)[-1]
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return {"actions": [], "count": 0, "error": "answer is not valid JSON"}
    items = data.get("actions", []) if isinstance(data, dict) else data
    actions = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict) or not str(item.get("task", "")).strip():
            continue
        actions.append({
            "task": str(item["task"]).strip(),
            "owner": str(item.get("owner") or "미정").strip() or "미정",
            "due": str(item.get("due") or "미정").strip() or "미정",
        })
    return {"actions": actions, "count": len(actions)}


TOOLS: dict[str, Callable[..., Any]] = {
    "get_weather": get_weather,
    "search_faq": search_faq,
    "count_chars": count_chars,
    "parse_actions": parse_actions,
}


def call_tool(name: str, args: dict[str, Any]) -> Any:
    if name not in TOOLS:
        raise ToolError(f"Tool '{name}' is not registered. Available: {', '.join(TOOLS)}")
    try:
        return TOOLS[name](**args)
    except TypeError as error:
        raise ToolError(f"Wrong arguments for tool '{name}': {error}") from error


def describe_tools() -> list[tuple[str, str]]:
    return [(name, (func.__doc__ or "").strip()) for name, func in TOOLS.items()]
