"""Resolve {{path.to.value}} placeholders against the workflow context."""

import json
import re
from typing import Any

PLACEHOLDER = re.compile(r"\{\{\s*([a-zA-Z0-9_.\-]+)\s*\}\}")


class TemplateError(KeyError):
    pass


def lookup(context: dict[str, Any], path: str) -> Any:
    value: Any = context
    for part in path.split("."):
        if isinstance(value, dict) and part in value:
            value = value[part]
        elif isinstance(value, list) and part.isdigit() and int(part) < len(value):
            value = value[int(part)]
        else:
            raise TemplateError(f"Cannot resolve '{{{{{path}}}}}': '{part}' not found")
    return value


def _to_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def render(template: Any, context: dict[str, Any]) -> Any:
    """Render strings, lists and dicts recursively.

    A string that is exactly one placeholder keeps the original type
    (dict, list, number). Mixed text is rendered as a string.
    """
    if isinstance(template, dict):
        return {key: render(value, context) for key, value in template.items()}
    if isinstance(template, list):
        return [render(item, context) for item in template]
    if not isinstance(template, str):
        return template

    whole = PLACEHOLDER.fullmatch(template.strip())
    if whole:
        return lookup(context, whole.group(1))
    return PLACEHOLDER.sub(lambda m: _to_text(lookup(context, m.group(1))), template)
