"""Named settings in ~/.tbench/profiles.toml, so `tbench run <name>` works from any folder."""
import tomllib

from .store import home

FIELDS = ("url", "body_file", "n", "method", "timeout", "warmup", "concurrency", "headers", "max_p95", "max_failures")


def path():
    return home() / "profiles.toml"


def load_all():
    p = path()
    return tomllib.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _value(v):
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(v, list):
        return "[" + ", ".join(_value(x) for x in v) + "]"
    return str(v).lower() if isinstance(v, bool) else str(v)


def save(name, settings):
    profiles = load_all()
    profiles[name] = {k: v for k, v in settings.items() if k in FIELDS and v not in (None, [])}
    out = []
    for pname, values in profiles.items():
        out.append(f'["{pname}"]')
        out += [f"{k} = {_value(v)}" for k, v in values.items()]
        out.append("")
    p = path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(out), encoding="utf-8")
    return p
