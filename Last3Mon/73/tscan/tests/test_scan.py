import json
import subprocess

import pytest
from conftest import FAKE_EMAIL, FAKE_KEY, FAKE_PHONE, FAKE_RRN, FAKE_TOKEN

from tscan import cli, gitscan
from tscan.files import add_ignore, scan_folder
from tscan.scanner import mask, mask_line, scan_text


def kinds(found):
    return sorted(f.kind for f in found)


# R1 · R4 · R13
def test_finds_kinds_but_not_dates_and_skips(fake):
    found, report = scan_folder(fake)
    notes = [f for f in found if f.path == "notes.md"]
    assert kinds(notes) == ["email", "openai_key", "phone", "rrn"]
    assert all(f.line in (1, 2, 3) for f in notes)  # line 4 has a date, an order number and a version only
    assert report["skipped"] == {"too_big": 1, "binary": 1}
    assert not any(f.path.startswith("node_modules") for f in found)


# R2: the original value is nowhere in the output
def test_values_are_masked_everywhere(fake, capsys):
    with pytest.raises(SystemExit) as e:
        cli.main(["scan", str(fake), "--json"])
    assert e.value.code == 1
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["summary"]["total"] == 5
    for secret in (FAKE_KEY, FAKE_PHONE, FAKE_EMAIL, FAKE_RRN, FAKE_TOKEN):
        assert secret not in out
    assert mask(FAKE_PHONE, "phone") == "010-****-1234"
    assert mask(FAKE_EMAIL, "email") == "t***@example.com"
    assert mask(FAKE_RRN, "rrn") == "900101-*******"


# R3
def test_env_value_copied_elsewhere(fake):
    found, _ = scan_folder(fake)
    env = [f for f in found if f.kind == "env_value"]
    assert [(f.path, f.line) for f in env] == [("config.py", 1)]
    assert FAKE_TOKEN not in env[0].masked


def test_hidden_with_full_width(fake):
    wide = "".join(chr(ord(c) + 0xFEE0) if "!" <= c <= "~" else c for c in FAKE_KEY)
    assert kinds(scan_text(f"k={wide}")) == ["openai_key"]


def test_preview_line_is_masked():
    line = f"call {FAKE_PHONE}, key {FAKE_KEY}"
    shown = mask_line(line)
    assert FAKE_PHONE not in shown and FAKE_KEY not in shown and "010-****-1234" in shown


# R7 · R11 · R12
def test_ignore_rules_and_summary(fake, capsys, tmp_path):
    add_ignore(fake, "notes.md:3")
    add_ignore(fake, "email:*.md")
    (fake / ".tscan.toml").write_text('[[rule]]\nname = "employee_id"\npattern = "E-\\\\d{6}"\n')
    (fake / "staff.txt").write_text("owner E-123456\n")
    found, _ = scan_folder(fake)
    assert "rrn" not in kinds(found) and "email" not in kinds(found)
    assert "employee_id" in kinds(found)
    with pytest.raises(SystemExit):
        cli.main(["scan", str(fake), "--summary"])
    out = capsys.readouterr().out
    assert "by kind" in out and "skipped  binary 1  too_big 1" in out


def test_nothing_found_exit_0(tmp_path, monkeypatch):
    monkeypatch.setenv("TSCAN_HOME", str(tmp_path / "home"))
    (tmp_path / "ok.txt").write_text("hello 2026-10-27\n")
    with pytest.raises(SystemExit) as e:
        cli.main(["scan", str(tmp_path)])
    assert e.value.code == 0


# R5: the staged content counts, not the working file
def test_staged(repo, capsys):
    (repo / "a.txt").write_text(f"k={FAKE_KEY}\n")
    subprocess.run(["git", "add", "a.txt"], check=True)
    (repo / "a.txt").write_text("clean now\n")  # changed after git add: the index still has the key
    with pytest.raises(SystemExit) as e:
        cli.main(["staged"])
    assert e.value.code == 1
    subprocess.run(["git", "add", "a.txt"], check=True)
    with pytest.raises(SystemExit) as e:
        cli.main(["staged"])
    assert e.value.code == 0


# R6
def test_hook_keeps_other_hooks(repo):
    ok, _ = gitscan.install_hook(repo)
    assert ok and "tscan staged" in gitscan.hook_path(repo).read_text()
    assert gitscan.uninstall_hook(repo)[0] and not gitscan.hook_path(repo).exists()
    gitscan.hook_path(repo).write_text("#!/bin/sh\necho mine\n")
    ok, message = gitscan.install_hook(repo)
    assert not ok and "already exists" in message
    assert gitscan.hook_path(repo).read_text() == "#!/bin/sh\necho mine\n"
    assert not gitscan.uninstall_hook(repo)[0]


# R9
def test_history_finds_removed_secret(repo):
    (repo / "a.txt").write_text(f"k={FAKE_KEY}\n")
    subprocess.run(["git", "add", "a.txt"], check=True)
    subprocess.run(["git", "commit", "-qm", "add"], check=True)
    (repo / "a.txt").write_text("gone\n")
    subprocess.run(["git", "commit", "-qam", "remove"], check=True)
    found, _ = gitscan.history(repo)
    assert len(found) == 1 and found[0].kind == "openai_key" and found[0].path.endswith(" a.txt")


def test_not_a_repo_exit_2(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as e:
        cli.main(["staged"])
    assert e.value.code == 2
