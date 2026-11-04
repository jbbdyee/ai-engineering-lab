"""A fake n8n + data API on a local port, answering with responses recorded from the day 79 answers (answers/06 · 08 · 14 · 16 · 18 · 25)."""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

DATA = Path(__file__).parent / "data"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


class Fake:
    def __init__(self):
        self.calls: list[tuple[str, dict]] = []
        self.cost_down = False
        self.brief_down = False


def handler(fake: Fake):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def send(self, code, data):
            body = json.dumps(data, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            fake.calls.append((self.path, body))
            if self.path == "/webhook/my-ops-facts":
                return self.send(200, load("facts-cost-down.json" if fake.cost_down else "facts.json"))
            if self.path == "/webhook/my-ops-ask":
                asks = load("asks.json")
                return self.send(200, asks.get(body.get("question"), asks["점심 메뉴 추천해 줘"]))
            if self.path == "/webhook/my-ops-brief":
                return self.send(500, {"message": "Error in workflow"}) if fake.brief_down else self.send(200, load("brief.json"))
            if self.path == "/webhook/my-ops-eval":
                cases = body.get("cases") or []
                if not cases:
                    return self.send(400, {"error": "cases must be a non-empty list"})
                e = load("eval.json")
                return self.send(200, e["pass"] if len(cases) == 8 else e["fail"])
            if self.path == "/audit/list":
                return self.send(200, load("audit.json"))
            self.send(404, {"message": "not registered"})

    return H


@pytest.fixture
def fake():
    f = Fake()
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler(f))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    f.base = f"http://127.0.0.1:{server.server_address[1]}"
    yield f
    server.shutdown()


@pytest.fixture
def down():
    """An address nothing listens on (n8n turned off)."""
    return "http://127.0.0.1:9"
