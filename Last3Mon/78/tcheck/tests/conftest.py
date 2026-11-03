import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

DATA = Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def n8n():
    """What n8n my-check answered on 2026-11-01 for the same three batches (Last3Mon/78/answers/18 · 21)."""
    return json.loads((DATA / "n8n-my-check.json").read_text(encoding="utf-8"))


@pytest.fixture
def api():
    """A local stand-in for the day 78 data API: GET /schemas/<name> from tests/data/schemas, POST /quality-log kept in memory."""
    log: list[dict] = []

    class Handler(BaseHTTPRequestHandler):
        def send(self, status, body):
            data = json.dumps(body, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = DATA / "schemas" / (self.path.removeprefix("/schemas/") + ".json")
            if self.path.startswith("/schemas/") and path.exists():
                return self.send(200, json.loads(path.read_text(encoding="utf-8")))
            return self.send(404, {"error": "schema not found"})

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            if self.path == "/quality-log":
                log.append(body)
                return self.send(200, {"stored": 1, "count": len(log)})
            return self.send(404, {})

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    server.log = log
    yield server
    server.shutdown()


@pytest.fixture
def url(api):
    return f"http://127.0.0.1:{api.server_address[1]}"
