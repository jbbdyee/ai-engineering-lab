import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from miniflow.platforms import FailoverRunner, PlatformError, load_config


class FakeN8n(BaseHTTPRequestHandler):
    mode = "ok"
    received: list = []

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FakeN8n.received.append((self.path, body))
        if FakeN8n.mode == "error":
            self.send_response(500)
            self.end_headers()
            return
        payload = json.dumps({"category": "network", "faq_id": "FAQ-003", "route": "자동 답변", "reply": "n8n reply"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


@pytest.fixture()
def n8n(monkeypatch, tmp_path):
    server = HTTPServer(("127.0.0.1", 0), FakeN8n)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    FakeN8n.mode, FakeN8n.received = "ok", []
    monkeypatch.setenv("N8N_BASE_URL", f"http://127.0.0.1:{server.server_port}")
    monkeypatch.setenv("MINIFLOW_LLM", "mock")
    monkeypatch.setenv("MINIFLOW_MEMORY_FILE", str(tmp_path / "memory.json"))
    yield server
    server.shutdown()


INPUTS = {"user": "kim", "text": "VPN 접속이 계속 끊겨요"}


def test_n8n_serves_when_healthy(n8n):
    report = FailoverRunner(["n8n", "miniflow"]).run("request", INPUTS)
    assert report["served_by"] == "n8n"
    assert FakeN8n.received[-1] == ("/webhook/ai-request", INPUTS)


def test_failover_to_miniflow_when_n8n_errors(n8n):
    FakeN8n.mode = "error"
    report = FailoverRunner(["n8n", "miniflow"]).run("request", INPUTS)
    assert report["served_by"] == "miniflow"
    assert [a["status"] for a in report["attempts"]] == ["failed", "ok"]
    assert report["result"]["route"] == "자동 답변"


def test_failover_when_n8n_is_down(monkeypatch, tmp_path):
    monkeypatch.setenv("N8N_BASE_URL", "http://127.0.0.1:9")
    monkeypatch.setenv("N8N_TIMEOUT", "2")
    monkeypatch.setenv("MINIFLOW_LLM", "mock")
    monkeypatch.setenv("MINIFLOW_MEMORY_FILE", str(tmp_path / "memory.json"))
    report = FailoverRunner(["n8n", "miniflow"]).run("request", {"user": "lee", "text": "점심 메뉴 추천해줘"})
    assert report["served_by"] == "miniflow"
    assert report["result"]["route"] == "담당자 확인"


def test_all_platforms_failing_raises(n8n):
    FakeN8n.mode = "error"
    with pytest.raises(PlatformError, match="All platforms failed"):
        FailoverRunner(["n8n"]).run("request", INPUTS)


def test_unknown_platform_is_rejected():
    with pytest.raises(PlatformError, match="Unknown platform"):
        FailoverRunner(["nowhere"], load_config())
