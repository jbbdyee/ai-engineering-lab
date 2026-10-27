"""Fake secrets are built here at test time, so no file in this repository holds one (tscan would find it)."""
import subprocess

import pytest

FAKE_KEY = "sk-" + "test-" + "abcdefghij" * 2
FAKE_PHONE = "010-" + "0000-" + "1234"
FAKE_EMAIL = "tester" + "@" + "example.com"
FAKE_RRN = "900101-" + "1000000"
FAKE_TOKEN = "abc123" + "def456"


@pytest.fixture
def fake(tmp_path, monkeypatch):
    monkeypatch.setenv("TSCAN_HOME", str(tmp_path / "home"))
    root = tmp_path / "proj"
    root.mkdir()
    (root / "notes.md").write_text(
        f"key = {FAKE_KEY}\n"
        f"call {FAKE_PHONE} or mail {FAKE_EMAIL}\n"
        f"id {FAKE_RRN}\n"
        "date 2026-10-27, order 202610271234, version 1.0.10-20261027\n"
    )
    (root / ".env").write_text(f"TOKEN={FAKE_TOKEN}\nDEBUG=true\n")
    (root / "config.py").write_text(f'token = "{FAKE_TOKEN}"\n')
    (root / "big.log").write_text("x" * 1_100_000)
    (root / "image.png").write_bytes(b"\x89PNG\0\0" + FAKE_KEY.encode())
    (root / "node_modules").mkdir()
    (root / "node_modules" / "lib.js").write_text(f"k='{FAKE_KEY}'\n")
    return root


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setenv("TSCAN_HOME", str(tmp_path / "home"))
    root = tmp_path / "repo"
    root.mkdir()
    for args in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        subprocess.run(["git", "-C", str(root), *args], check=True)
    monkeypatch.chdir(root)
    return root
