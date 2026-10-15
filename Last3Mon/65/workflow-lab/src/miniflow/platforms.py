"""Run the same business workflow on interchangeable platforms, with failover.

Application code calls `FailoverRunner(["n8n", "miniflow"]).run("request", inputs)`.
Which platforms exist and how each one runs a workflow is decided by adapters
and `platforms.json`, so the calling code never changes when a platform is swapped.
"""

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Protocol

from miniflow.engine import WorkflowError, load_workflow, run_workflow

PROJECT_DIR = Path(__file__).resolve().parents[2]
CONFIG_FILE = PROJECT_DIR / "platforms.json"


class PlatformError(RuntimeError):
    """A platform could not run the workflow (down, timeout, bad answer)."""


class WorkflowPlatform(Protocol):
    name: str

    def run(self, workflow: str, inputs: dict[str, Any]) -> dict[str, Any]: ...


def load_config(path: Path = CONFIG_FILE) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


class N8nPlatform:
    """Calls an n8n workflow through its production webhook URL."""

    name = "n8n"

    def __init__(self, config: dict[str, Any]):
        self.workflows = config["workflows"]
        self.base_url = os.getenv("N8N_BASE_URL", config.get("n8n", {}).get("base_url", "http://localhost:5678"))
        self.timeout = float(os.getenv("N8N_TIMEOUT", config.get("n8n", {}).get("timeout", 120)))

    def run(self, workflow: str, inputs: dict[str, Any]) -> dict[str, Any]:
        settings = self.workflows.get(workflow, {}).get("n8n")
        if not settings:
            raise PlatformError(f"n8n has no mapping for workflow '{workflow}'")
        url = f"{self.base_url.rstrip('/')}/webhook/{settings['webhook']}"
        request = urllib.request.Request(url, data=json.dumps(inputs).encode("utf-8"),
                                         headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            raise PlatformError(f"n8n returned HTTP {error.code} for {url}") from error
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            raise PlatformError(f"n8n is not reachable at {url} ({error})") from error
        except json.JSONDecodeError as error:
            raise PlatformError("n8n answered with something that is not JSON") from error


class MiniflowPlatform:
    """Runs the matching JSON flow with the local miniflow engine."""

    name = "miniflow"

    def __init__(self, config: dict[str, Any]):
        self.workflows = config["workflows"]

    def run(self, workflow: str, inputs: dict[str, Any]) -> dict[str, Any]:
        settings = self.workflows.get(workflow, {}).get("miniflow")
        if not settings:
            raise PlatformError(f"miniflow has no mapping for workflow '{workflow}'")
        try:
            report = run_workflow(load_workflow(PROJECT_DIR / settings["flow"]), inputs, verbose=False)
        except WorkflowError as error:
            raise PlatformError(str(error)) from error
        if report["status"] != "completed":
            failed = report["trace"][-1]
            raise PlatformError(f"miniflow failed at node '{failed['id']}': {failed.get('error')}")
        return report["result"]


PLATFORMS: dict[str, type] = {"n8n": N8nPlatform, "miniflow": MiniflowPlatform}


def register_platform(name: str, adapter: type) -> None:
    """Add another platform adapter without touching the calling code."""
    PLATFORMS[name] = adapter


class FailoverRunner:
    """Try platforms in order; when one raises PlatformError, move on to the next."""

    def __init__(self, order: list[str], config: dict[str, Any] | None = None):
        config = config or load_config()
        unknown = [name for name in order if name not in PLATFORMS]
        if unknown:
            raise PlatformError(f"Unknown platform(s): {', '.join(unknown)}. Registered: {', '.join(PLATFORMS)}")
        self.platforms = [PLATFORMS[name](config) for name in order]

    def run(self, workflow: str, inputs: dict[str, Any]) -> dict[str, Any]:
        attempts = []
        for platform in self.platforms:
            started = time.perf_counter()
            try:
                result = platform.run(workflow, inputs)
            except PlatformError as error:
                attempts.append({"platform": platform.name, "status": "failed", "error": str(error),
                                 "ms": round((time.perf_counter() - started) * 1000, 1)})
                continue
            attempts.append({"platform": platform.name, "status": "ok",
                             "ms": round((time.perf_counter() - started) * 1000, 1)})
            return {"workflow": workflow, "served_by": platform.name, "result": result, "attempts": attempts}
        raise PlatformError("All platforms failed: " + "; ".join(f"{a['platform']}: {a['error']}" for a in attempts))
