# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Course helper: check, push and test the n8n workflows that a CLI coding agent wrote.

  uv run tools/flow.py doctor                          # is everything ready?
  uv run tools/flow.py check my-work/meeting.json      # find mistakes before n8n sees the file
  uv run tools/flow.py push  my-work/meeting.json      # import + publish (one n8n restart)
  uv run tools/flow.py off   my-sms                     # unpublish by file or webhook path (a role that is down)
  uv run tools/flow.py call  my-meeting requests/weekly.json
  uv run tools/flow.py test  cases/lab02.json [--repeat 3]

Run it from the day folder (Last3Mon/66). n8n is the day 65 install (~/day65-n8n, Docker project
day65-n8n), started from Last3Mon/65/n8n. Environment overrides:
  N8N_CONTAINER (default: the running n8n service of project day65-n8n, else day65-n8n-n8n-1)
  N8N_HOME (default ~/day65-n8n), N8N_URL (default http://localhost:5678)
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = Path(__file__).resolve().parent / ".cache"
def n8n_home() -> Path:
    """Where the official n8n install lives: N8N_HOME, else Last3Mon/65/n8n/.env, else ~/day65-n8n."""
    if os.getenv("N8N_HOME"):
        return Path(os.environ["N8N_HOME"]).expanduser()
    env_file = ROOT.parent / "65" / "n8n" / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("N8N_HOME="):
                value = line.split("=", 1)[1].strip().strip("'\"")
                if value:
                    return (env_file.parent / Path(value).expanduser()).resolve()
    return Path.home() / "day65-n8n"


N8N_HOME = n8n_home()
START_HINT = "cd ~/aio-01d4-stu/Last3Mon/65/n8n && docker compose start   (n8n install: ~/day65-n8n)"


def find_container() -> str:
    """The n8n container of the day 65 project, whichever folder it was started from."""
    if os.getenv("N8N_CONTAINER"):
        return os.environ["N8N_CONTAINER"]
    if shutil.which("docker"):
        result = subprocess.run(["docker", "ps", "-a", "--filter", "label=com.docker.compose.project=day65-n8n",
                                 "--filter", "label=com.docker.compose.service=n8n", "--format", "{{.Names}}"],
                                capture_output=True, text=True)
        names = result.stdout.split()
        if names:
            return names[0]
    return "day65-n8n-n8n-1"


CONTAINER = find_container()
N8N_URL = os.getenv("N8N_URL", "http://localhost:5678").rstrip("/")

# Versions written in AGENTS.md. Other versions still work if n8n knows them (warning only).
RECOMMENDED = {
    "n8n-nodes-base.webhook": 2,
    "n8n-nodes-base.respondToWebhook": 1.1,
    "n8n-nodes-base.if": 2.2,
    "n8n-nodes-base.switch": 3.2,
    "n8n-nodes-base.set": 3.4,
    "n8n-nodes-base.code": 2,
    "n8n-nodes-base.httpRequest": 4.2,
    "n8n-nodes-base.httpRequestTool": 4.2,
    "@n8n/n8n-nodes-langchain.agent": 3.1,
    "@n8n/n8n-nodes-langchain.lmChatOpenAi": 1.2,
    "@n8n/n8n-nodes-langchain.vectorStoreInMemory": 1.3,
    "@n8n/n8n-nodes-langchain.embeddingsOpenAi": 1.2,
    "@n8n/n8n-nodes-langchain.documentDefaultDataLoader": 1.1,
}
USES_DATA_API = False  # day 66 labs do not call the data API
AGENT_HOOKS: tuple[str, ...] = ()  # no ready-made agents on day 66
COURSE_CREDENTIALS = {"openAiCourse0001": "OpenAI (.env)"}  # OpenAI only from day 66 (no Ollama)
CONNECTION_TYPES = {"main", "ai_tool", "ai_languageModel", "ai_memory", "ai_outputParser", "ai_embedding", "ai_document"}
SECRET = re.compile(r"\bsk-[A-Za-z0-9_-]{16,}")

OK, BAD, WARN = "✔", "✘", "!"


# ---------------------------------------------------------------- helpers
def die(message: str) -> None:
    print(f"{BAD} {message}", file=sys.stderr)
    sys.exit(1)


def docker(*args: str, stdin: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    if not shutil.which("docker"):
        die("docker command not found. Start Docker first.")
    result = subprocess.run(["docker", *args], input=stdin, capture_output=True, text=True)
    if check and result.returncode != 0:
        die(f"docker {' '.join(args[:2])} failed:\n{(result.stderr or result.stdout).strip()}")
    return result


def n8n(*args: str, stdin: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return docker("exec", "-i", CONTAINER, "n8n", *args, stdin=stdin, check=check)


def container_running() -> bool:
    if not shutil.which("docker"):
        return False
    result = subprocess.run(["docker", "inspect", "-f", "{{.State.Running}}", CONTAINER], capture_output=True, text=True)
    return result.stdout.strip() == "true"


def http(method: str, url: str, body: object | None = None, timeout: float = 300) -> tuple[int, object, float]:
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    start = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status, raw = response.status, response.read()
    except urllib.error.HTTPError as error:
        status, raw = error.code, error.read()
    except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
        return 0, {"error": str(getattr(error, "reason", error))}, time.monotonic() - start
    text = raw.decode("utf-8", errors="replace")
    try:
        payload: object = json.loads(text) if text.strip() else ""
    except json.JSONDecodeError:
        payload = text
    return status, payload, time.monotonic() - start


def load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        die(f"file not found: {path}")
    except json.JSONDecodeError as error:
        die(f"{path} is not valid JSON (line {error.lineno}, column {error.colno}): {error.msg}")


def resolve(path: str) -> Path:
    candidate = Path(path)
    if candidate.exists() or candidate.is_absolute():
        return candidate
    return ROOT / path


def node_versions() -> dict[str, list[float]]:
    """Node types and versions that this n8n really has (exported once, then cached)."""
    cache = CACHE / "node-versions.json"
    if cache.exists():
        return json.loads(cache.read_text())
    if not container_running():
        return {}
    n8n("export:nodes", "--output=/tmp/course-nodes.json")
    raw = docker("exec", CONTAINER, "sh", "-c", "cat /tmp/course-nodes.json && rm -f /tmp/course-nodes.json").stdout
    versions: dict[str, set[float]] = {}
    for node in json.loads(raw):
        value = node.get("version")
        versions.setdefault(node["name"], set()).update(value if isinstance(value, list) else [value])
    result = {name: sorted(values) for name, values in versions.items()}
    CACHE.mkdir(exist_ok=True)
    cache.write_text(json.dumps(result))
    return result


def walk_strings(value: object, where: str = ""):
    if isinstance(value, str):
        yield where, value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from walk_strings(item, f"{where}.{key}" if where else key)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk_strings(item, f"{where}[{index}]")


def webhooks(workflow: dict) -> list[tuple[str, str]]:
    found = []
    for node in workflow.get("nodes", []):
        if node.get("type") == "n8n-nodes-base.webhook":
            parameters = node.get("parameters", {})
            found.append((str(parameters.get("httpMethod", "GET")).upper(), str(parameters.get("path", "")).strip("/")))
    return found


# ---------------------------------------------------------------- check
def check_workflow(workflow: object) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(workflow, dict):
        return ["the file must be one workflow object { name, nodes, connections }"], warnings
    if not str(workflow.get("name", "")).strip():
        errors.append("missing workflow 'name'")
    nodes = workflow.get("nodes")
    connections = workflow.get("connections")
    if not isinstance(nodes, list) or not nodes:
        return errors + ["'nodes' must be a non-empty list"], warnings
    if not isinstance(connections, dict):
        errors.append("'connections' must be an object")
        connections = {}

    known = node_versions()
    names: dict[str, dict] = {}
    for index, node in enumerate(nodes):
        label = f"node #{index + 1}"
        if not isinstance(node, dict):
            errors.append(f"{label} is not an object")
            continue
        name = node.get("name")
        if not name:
            errors.append(f"{label} has no 'name'")
            continue
        label = f"node '{name}'"
        if name in names:
            errors.append(f"{label} appears twice (node names must be unique)")
        names[name] = node
        node_type, version = node.get("type"), node.get("typeVersion")
        if not node_type or version is None:
            errors.append(f"{label} needs 'type' and 'typeVersion'")
        elif known and node_type not in known:
            errors.append(f"{label}: type '{node_type}' does not exist in this n8n")
        elif known and version not in known[node_type]:
            errors.append(f"{label}: {node_type} has no typeVersion {version} (available: {known[node_type]})")
        elif node_type in RECOMMENDED and version != RECOMMENDED[node_type]:
            warnings.append(f"{label}: typeVersion {version} (AGENTS.md uses {RECOMMENDED[node_type]})")
        if not isinstance(node.get("parameters"), dict):
            errors.append(f"{label} needs 'parameters' (use {{}} when empty)")
        position = node.get("position")
        if not (isinstance(position, list) and len(position) == 2):
            errors.append(f"{label} needs 'position': [x, y]")
        for kind, credential in (node.get("credentials") or {}).items():
            credential_id = (credential or {}).get("id")
            if credential_id not in COURSE_CREDENTIALS:
                errors.append(f"{label}: credential '{kind}' must use a course id {list(COURSE_CREDENTIALS)}, got {credential_id!r}")
        for where, text in walk_strings(node.get("parameters", {})):
            if SECRET.search(text):
                errors.append(f"{label}: parameters.{where} looks like an API key. Use a credential instead.")
            if "{{" in text and "}}" in text and not text.startswith("="):
                warnings.append(f"{label}: parameters.{where} has {{{{ }}}} but does not start with '=' (it stays plain text)")

    targets_of: dict[str, set[str]] = {}
    for source, outputs in connections.items():
        if source not in names:
            errors.append(f"connections: source '{source}' is not a node name")
            continue
        if not isinstance(outputs, dict):
            errors.append(f"connections['{source}'] must be an object like {{\"main\": [[...]]}}")
            continue
        for kind, branches in outputs.items():
            if kind not in CONNECTION_TYPES:
                errors.append(f"connections['{source}']: unknown connection type '{kind}'")
            for branch in branches or []:
                for link in branch or []:
                    target = (link or {}).get("node")
                    if target not in names:
                        errors.append(f"connections['{source}'] points to '{target}', which is not a node name")
                    elif link.get("type") != kind:
                        errors.append(f"connections['{source}'] -> '{target}': link type must be '{kind}'")
                    else:
                        targets_of.setdefault(target, set()).add(kind)
                        if kind != "main":
                            targets_of.setdefault(f"{source}::from", set()).add(kind)

    has_respond = any(node.get("type") == "n8n-nodes-base.respondToWebhook" for node in names.values())
    for name, node in names.items():
        node_type = node.get("type", "")
        parameters = node.get("parameters", {}) if isinstance(node.get("parameters"), dict) else {}
        if node_type == "n8n-nodes-base.webhook":
            if not str(parameters.get("path", "")).strip("/"):
                errors.append(f"node '{name}': webhook needs a 'path'")
            if parameters.get("responseMode") == "responseNode" and not has_respond:
                errors.append(f"node '{name}': responseMode is 'responseNode' but there is no Respond to Webhook node")
        if node_type == "@n8n/n8n-nodes-langchain.agent" and "ai_languageModel" not in targets_of.get(name, set()):
            errors.append(f"node '{name}': AI Agent needs a chat model connected with 'ai_languageModel'")
        if node_type.endswith("Tool") or node_type.startswith("@n8n/n8n-nodes-langchain.tool"):
            if "ai_tool" not in targets_of.get(f"{name}::from", set()):
                errors.append(f"node '{name}': a tool must be connected to an AI Agent with 'ai_tool'")
        if node_type.startswith("@n8n/n8n-nodes-langchain.lmChat"):
            if "ai_languageModel" not in targets_of.get(f"{name}::from", set()):
                errors.append(f"node '{name}': a chat model must be connected to an AI Agent with 'ai_languageModel'")
        is_sub_node = bool(targets_of.get(f"{name}::from"))  # model, tool, embeddings, loader: connected by ai_* links
        if node_type != "n8n-nodes-base.webhook" and not node_type.startswith("@n8n/n8n-nodes-langchain.lm") and not is_sub_node \
                and not (node_type.endswith("Tool") or node_type.startswith("@n8n/n8n-nodes-langchain.tool")) \
                and "main" not in targets_of.get(name, set()) and "trigger" not in node_type.lower():
            warnings.append(f"node '{name}': nothing is connected into it (it never runs)")
    if not webhooks(workflow):
        warnings.append("no Webhook node: 'push' works, but 'call' and 'test' need a webhook path")
    return errors, warnings


def cmd_check(args: argparse.Namespace) -> int:
    path = resolve(args.file)
    errors, warnings = check_workflow(load_json(path))
    for warning in warnings:
        print(f"{WARN} {warning}")
    for error in errors:
        print(f"{BAD} {error}")
    if errors:
        print(f"{BAD} {path.name}: {len(errors)} error(s). Fix them and run check again.")
        return 1
    print(f"{OK} {path.name}: no errors" + (f" ({len(warnings)} warning(s))" if warnings else ""))
    return 0


# ---------------------------------------------------------------- push
def stable_id(path: Path) -> str:
    return "w" + hashlib.sha1(path.stem.encode("utf-8")).hexdigest()[:15]


def wait_until_ready(paths: list[tuple[str, str]], seconds: int = 90) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        status, _, _ = http("GET", f"{N8N_URL}/healthz", timeout=3)
        if status == 200:
            break
        time.sleep(1)
    else:
        return False
    for method, path in paths:
        while time.monotonic() < deadline:
            # A webhook that is registered for POST answers a GET with a hint, not "is not registered".
            status, payload, _ = http("GET" if method != "GET" else "HEAD", f"{N8N_URL}/webhook/{path}", timeout=5)
            text = json.dumps(payload, ensure_ascii=False)
            if "not registered for" in text or status not in (0, 404, 500, 502, 503):
                break
            time.sleep(1)
    time.sleep(2)  # webhooks of the other published workflows finish registering right after
    return time.monotonic() < deadline


def exported_workflows() -> list[dict]:
    exported = docker("exec", CONTAINER, "sh", "-c",
                      "n8n export:workflow --all --output=/tmp/course-all.json >/dev/null 2>&1; "
                      "cat /tmp/course-all.json 2>/dev/null; rm -f /tmp/course-all.json", check=False).stdout
    try:
        return json.loads(exported) if exported.strip() else []
    except json.JSONDecodeError:
        return []


def prepare(path: Path) -> dict | None:
    workflow = load_json(path)
    errors, warnings = check_workflow(workflow)
    for warning in warnings:
        print(f"{WARN} {path.name}: {warning}")
    if errors:
        for error in errors:
            print(f"{BAD} {path.name}: {error}")
        return None
    workflow = dict(workflow)
    if not re.fullmatch(r"[A-Za-z0-9]{10,}", str(workflow.get("id", ""))):
        workflow["id"] = stable_id(path)
    workflow["active"] = False
    workflow.setdefault("settings", {}).setdefault("executionOrder", "v1")
    for node in workflow["nodes"]:
        node.setdefault("id", str(uuid.uuid5(uuid.NAMESPACE_URL, f"{workflow['id']}/{node['name']}")))
        if node["type"] == "n8n-nodes-base.webhook":
            node.setdefault("webhookId", str(uuid.uuid5(uuid.NAMESPACE_URL, f"{workflow['id']}/webhook/{node['name']}")))
    return workflow


def cmd_push(args: argparse.Namespace) -> int:
    paths = [resolve(file) for file in args.files]
    workflows = [prepare(path) for path in paths]
    if None in workflows:
        print(f"{BAD} not pushed. Fix the errors first (uv run tools/flow.py check <file>).")
        return 1
    if not container_running():
        die(f"n8n container '{CONTAINER}' is not running. {START_HINT}")
    mine_ids = {workflow["id"] for workflow in workflows}
    hooks = {hook for workflow in workflows for hook in webhooks(workflow)}

    # Another published workflow with the same webhook path would block this one.
    for other in exported_workflows():
        if other.get("id") not in mine_ids and other.get("active") and hooks & set(webhooks(other)):
            n8n("unpublish:workflow", f"--id={other['id']}")
            print(f"{WARN} unpublished '{other.get('name')}' ({other['id']}): it used the same webhook path")

    for workflow in workflows:
        docker("exec", "-i", CONTAINER, "sh", "-c",
               "cat > /tmp/course-workflow.json && n8n import:workflow --input=/tmp/course-workflow.json; "
               "status=$?; rm -f /tmp/course-workflow.json; exit $status",
               stdin=json.dumps(workflow, ensure_ascii=False))
        n8n("publish:workflow", f"--id={workflow['id']}")
    # The CLI changes the database only; one restart makes the running n8n load the new versions (about 5 s).
    docker("restart", CONTAINER)
    ready = wait_until_ready(sorted(hooks))
    for workflow in workflows:
        print(f"{OK} pushed '{workflow['name']}' (id {workflow['id']})")
        for method, hook in sorted(webhooks(workflow)):
            print(f"   {method} {N8N_URL}/webhook/{hook}")
    if not ready:
        print(f"{WARN} n8n is still starting. Wait a few seconds before 'call' or 'test'.")
    return 0


def cmd_off(args: argparse.Namespace) -> int:
    """Unpublish workflows, given as files or webhook paths, to see how the others behave when one role is down."""
    if not container_running():
        die(f"n8n container '{CONTAINER}' is not running. {START_HINT}")
    exported = exported_workflows()
    wanted: dict[str, str] = {}
    for item in args.files:
        path = resolve(item) if (ROOT / item).exists() or Path(item).exists() else None
        if path:
            workflow = load_json(path)
            workflow_id = workflow.get("id") if re.fullmatch(r"[A-Za-z0-9]{10,}", str(workflow.get("id", ""))) else stable_id(path)
            wanted[workflow_id] = item
            hooks = {hook for _, hook in webhooks(workflow)}
        else:
            hooks = {item.strip("/")}
        for other in exported:
            if other.get("active") and hooks & {hook for _, hook in webhooks(other)}:
                wanted[other["id"]] = item
    active = {item.get("id") for item in exported if item.get("active")}
    for workflow_id, item in wanted.items():
        if workflow_id in active:
            n8n("unpublish:workflow", f"--id={workflow_id}")
            print(f"{OK} unpublished {item} (id {workflow_id})")
    docker("restart", CONTAINER)
    wait_until_ready([])
    print(f"{OK} n8n restarted. Turn it back on with: uv run tools/flow.py push <the workflow file>")
    return 0


# ---------------------------------------------------------------- call / test
def request_body(spec: str | dict, base: Path = ROOT) -> object:
    if isinstance(spec, dict):
        return spec
    text = spec.strip()
    if text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError as error:
            die(f"request is not valid JSON: {error.msg}")
    path = Path(text)
    if not path.exists():
        path = base / text
    return load_json(path)


def cmd_call(args: argparse.Namespace) -> int:
    body = request_body(args.request) if args.request else {}
    status, payload, seconds = http("POST", f"{N8N_URL}/webhook/{args.path.strip('/')}", body)
    print(f"HTTP {status} · {seconds:.1f}s")
    print(json.dumps(payload, ensure_ascii=False, indent=2) if not isinstance(payload, str) else payload)
    return 0 if 200 <= status < 300 else 1


def field(payload: object, dotted: str) -> object:
    value = payload
    for part in dotted.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        elif isinstance(value, list) and part.isdigit() and int(part) < len(value):
            value = value[int(part)]
        else:
            return None
    return value


def as_text(value: object) -> str:
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


def judge(expect: dict, status: int, payload: object) -> list[str]:
    problems = []
    if status != expect.get("status", 200):
        problems.append(f"status {status} (expected {expect.get('status', 200)})")
    for name, wanted in (expect.get("equals") or {}).items():
        actual = field(payload, name)
        if actual != wanted:
            problems.append(f"{name} = {as_text(actual)[:60]} (expected {as_text(wanted)})")
    for name, words in (expect.get("contains") or {}).items():
        words = [words] if isinstance(words, str) else words
        text = as_text(field(payload, name) or "")
        if not any(word in text for word in words):
            problems.append(f"{name} has none of {words}")
    for name, words in (expect.get("not_contains") or {}).items():
        words = [words] if isinstance(words, str) else words
        text = as_text(field(payload, name) or "")
        leaked = [word for word in words if word in text]
        if leaked:
            problems.append(f"{name} must not have {leaked}")
    return problems


def cmd_test(args: argparse.Namespace) -> int:
    path = resolve(args.cases)
    suite = load_json(path)
    hook = (args.webhook or suite.get("webhook", "")).strip("/")
    cases = suite.get("cases", [])
    if not hook or not cases:
        die(f"{path.name} needs \"webhook\" and a non-empty \"cases\" list")
    # "before": calls to make once before the cases, e.g. rebuild the in-memory index (lost when n8n restarts).
    for step in ([] if args.no_before else suite.get("before", [])):
        step_hook = str(step.get("webhook", "")).strip("/")
        status, payload, seconds = http("POST", f"{N8N_URL}/webhook/{step_hook}", request_body(step.get("body") or step.get("request", "{}")))
        shown = json.dumps(payload, ensure_ascii=False)[:120] if not isinstance(payload, str) else payload[:120]
        print(f"{OK if 200 <= status < 300 else BAD} before: POST /webhook/{step_hook} · HTTP {status} · {seconds:.1f}s · {shown}")
        if not 200 <= status < 300:
            die(f"the 'before' step failed. Is '{step_hook}' pushed? Try: uv run tools/flow.py call {step_hook}")
    print(f"POST {N8N_URL}/webhook/{hook} · {len(cases)} case(s) × {args.repeat}")
    results, passed = [], 0
    for case in cases:
        body = request_body(case.get("body") or case.get("request", "{}"))
        case_hook = (case.get("webhook") or hook).strip("/") if not args.webhook else hook
        for run in range(1, args.repeat + 1):
            status, payload, seconds = http("POST", f"{N8N_URL}/webhook/{case_hook}", body)
            problems = judge(case.get("expect", {}), status, payload)
            passed += not problems
            mark = OK if not problems else BAD
            suffix = f" #{run}" if args.repeat > 1 else ""
            print(f"{mark} {case.get('name', '?')}{suffix} · {seconds:.1f}s" + ("" if not problems else " · " + "; ".join(problems)))
            results.append({"case": case.get("name"), "webhook": case_hook, "run": run, "passed": not problems, "problems": problems,
                            "seconds": round(seconds, 1), "status": status, "request": body, "response": payload})
    total = len(results)
    print(f"Passed {passed}/{total}")
    runs = ROOT / "runs"
    runs.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    report = runs / f"{path.stem}-{stamp}.json"
    report.write_text(json.dumps({"cases": str(path.name), "webhook": hook, "passed": passed, "total": total,
                                  "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"report: {report.relative_to(ROOT)}")
    return 0 if passed == total else 1


# ---------------------------------------------------------------- doctor
def cmd_doctor(args: argparse.Namespace) -> int:
    failures = 0

    def line(good: bool, text: str, hint: str = "") -> None:
        nonlocal failures
        failures += not good
        print(f"{OK if good else BAD} {text}" + ("" if good or not hint else f"\n   → {hint}"))

    installed = (N8N_HOME / "compose.yml").exists()
    print(f"{OK if installed else WARN} n8n install folder {N8N_HOME}" + ("" if installed else
          "\n   → day 65 SETUP-N8N 5단계 (get.n8n.io 설치). 다른 곳에 설치했다면 Last3Mon/65/n8n/.env 에 N8N_HOME=<폴더>"))
    running = container_running()
    line(running, f"n8n container {CONTAINER}", START_HINT)
    status, _, _ = http("GET", f"{N8N_URL}/healthz", timeout=5)
    line(status == 200, f"n8n {N8N_URL}", "wait 10 seconds after starting n8n, then run doctor again")
    status, _, _ = http("GET", "http://localhost:8800/health", timeout=5)
    if USES_DATA_API:
        line(status == 200, "data API http://localhost:8800", "cd ~/aio-01d4-stu/Last3Mon/67/data-api && docker compose up -d --force-recreate   (start n8n first)")
        docs_status, docs, _ = http("GET", "http://localhost:8800/docs", timeout=5)
        count = len(docs.get("docs", [])) if isinstance(docs, dict) else 0
        line(docs_status == 200 and count > 0, f"policy documents /docs ({count})",
             "the data API is an older day's version: cd ~/aio-01d4-stu/Last3Mon/67/data-api && docker compose up -d --force-recreate")
    else:
        print(f"{OK if status == 200 else WARN} data API http://localhost:8800 (not used today)")
    if running:
        probe = docker("exec", CONTAINER, "node", "-e",
                       "fetch('http://data-api:8800/health').then(r=>console.log(r.status)).catch(()=>console.log(0))",
                       check=False).stdout.strip()
        if USES_DATA_API:
            line(probe == "200", "n8n → http://data-api:8800", "data API must join the day65-n8n_default network (compose.yml)")
        exported = docker("exec", CONTAINER, "sh", "-c",
                          "n8n export:credentials --all --output=/tmp/course-cred.json >/dev/null 2>&1; "
                          "cat /tmp/course-cred.json 2>/dev/null; rm -f /tmp/course-cred.json", check=False).stdout
        try:
            ids = {item.get("id") for item in json.loads(exported)} if exported.strip() else set()
        except json.JSONDecodeError:
            ids = set()
        for credential_id, name in COURSE_CREDENTIALS.items():
            line(credential_id in ids, f"credential '{name}' ({credential_id})",
                 "cd ~/aio-01d4-stu/Last3Mon/65/n8n && bash register-credentials.sh")
        line(bool(node_versions()), "node catalog (for check)")
        for hook in AGENT_HOOKS:
            _, payload, _ = http("GET", f"{N8N_URL}/webhook/{hook}", timeout=5)
            line("not registered for" in json.dumps(payload, ensure_ascii=False), f"agent webhook /{hook}",
                 "uv run tools/flow.py push <agent workflow file>")
    agents = [name for name in ("codex", "claude", "agy") if shutil.which(name)]
    line(bool(agents), "CLI coding agent: " + (", ".join(agents) if agents else "none"),
         "install one of codex / claude / agy (see Lecture/66/00-DAY66-PREP.md)")
    print("ready" if not failures else f"{failures} item(s) to fix")
    return 0 if not failures else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Check, push and test course n8n workflows.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="check n8n, data API, credentials and CLI agents").set_defaults(run=cmd_doctor)
    item = commands.add_parser("check", help="find mistakes in a workflow file")
    item.add_argument("file")
    item.set_defaults(run=cmd_check)
    item = commands.add_parser("push", help="import and publish workflow files (one n8n restart)")
    item.add_argument("files", nargs="+")
    item.set_defaults(run=cmd_push)
    item = commands.add_parser("off", help="unpublish workflow files or webhook paths (a role that is down)")
    item.add_argument("files", nargs="+")
    item.set_defaults(run=cmd_off)
    item = commands.add_parser("call", help="POST one request to a webhook path")
    item.add_argument("path", help="webhook path, e.g. my-notice")
    item.add_argument("request", nargs="?", help="request file or inline JSON")
    item.set_defaults(run=cmd_call)
    item = commands.add_parser("test", help="run a test case file")
    item.add_argument("cases")
    item.add_argument("--repeat", type=int, default=1, help="run every case N times")
    item.add_argument("--webhook", help="override the webhook path in the case file")
    item.add_argument("--no-before", action="store_true", help="skip the 'before' steps (keep the index you built by hand)")
    item.set_defaults(run=cmd_test)
    args = parser.parse_args()
    return args.run(args)


if __name__ == "__main__":
    sys.exit(main())
