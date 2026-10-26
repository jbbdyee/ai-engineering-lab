"""A fake server inside pytest, so tests never call the real helpdesk (or OpenAI).

Query options: delay=<s>, fail_every=<k> (every k-th call answers 500), first_delay=<s>,
status=<code>, timings=1 (answer with a helpdesk-like `timings`). Counters reset per test.
"""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import pytest


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        self.server.bodies.append(self.rfile.read(length).decode())
        self.handle_call()

    def do_GET(self):
        self.handle_call()

    def handle_call(self):
        q = {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}
        with self.server.lock:
            self.server.count += 1
            count = self.server.count
        delay = float(q.get("first_delay", 0)) if count == 1 and "first_delay" in q else float(q.get("delay", 0))
        time.sleep(delay)
        status = int(q.get("status", 200))
        if "fail_every" in q and count % int(q["fail_every"]) == 0:
            status = 500
        payload = {"count": count}
        if q.get("timings"):
            payload["timings"] = {"classify_ms": 100 * count, "answer_ms": 300, "total_ms": 400 + 100 * count}
        data = json.dumps(payload).encode()
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass


@pytest.fixture
def server(tmp_path, monkeypatch):
    monkeypatch.setenv("TBENCH_HOME", str(tmp_path / "home"))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    httpd.daemon_threads = True
    httpd.count, httpd.lock, httpd.bodies = 0, threading.Lock(), []
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    httpd.base = f"http://127.0.0.1:{httpd.server_address[1]}/hook"
    yield httpd
    httpd.shutdown()
    httpd.server_close()


@pytest.fixture
def body_file(tmp_path):
    p = tmp_path / "faq-vpn.json"
    p.write_text(json.dumps({"question": "VPN 접속이 자꾸 끊겨요", "no_cache": True}, ensure_ascii=False))
    return p
