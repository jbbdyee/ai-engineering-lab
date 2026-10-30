"""One attempt of a command or of an HTTP call, as an Outcome (R1 · R3 · R4 · R5)."""
from __future__ import annotations

import json
import socket
import subprocess
import urllib.error
import urllib.request

from .retry import Outcome

# 408 timeout · 425 too early · 429 too many requests: waiting can help. Other 4xx: the request itself is wrong.
RETRY_4XX = {408, 425, 429}


def command(argv: list[str] | str, shell: bool = False):
    """attempt(timeout) for a command: exit code 0 is success; a timeout is retryable."""
    def attempt(timeout: float | None) -> Outcome:
        try:
            done = subprocess.run(argv, shell=shell, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return Outcome(False, True, f"timeout {timeout:.1f}s")
        except FileNotFoundError as error:
            return Outcome(False, False, f"not found: {error.filename}")
        if done.returncode == 0:
            return Outcome(True, output=done.stdout)
        tail = (done.stderr or done.stdout).strip().splitlines()[-1:] or [""]
        return Outcome(False, True, f"exit {done.returncode} {tail[0][:120]}".strip(), output=done.stdout)
    return attempt


def retry_after(value: str | None) -> float | None:
    try:
        return max(0.0, float(value)) if value else None
    except ValueError:
        return None  # an HTTP date: ignore, use our own backoff


def http(method: str, url: str, body: str | None = None, headers: dict[str, str] | None = None,
         idem_key: str | None = None, body_key: str | None = None):
    """attempt(timeout) for an HTTP call: 2xx success · 5xx, 408/425/429, timeout, connection error retryable ·
    other 4xx not retryable. The same idempotency key goes with every try (header, and the body field if asked)."""
    data = None
    send = dict(headers or {})
    if body is not None:
        if body_key and idem_key:
            parsed = json.loads(body)
            parsed.setdefault(body_key, idem_key)
            body = json.dumps(parsed, ensure_ascii=False)
        data = body.encode("utf-8")
        send.setdefault("Content-Type", "application/json")
    if idem_key:
        send["Idempotency-Key"] = idem_key

    def attempt(timeout: float | None) -> Outcome:
        request = urllib.request.Request(url, data=data, method=method.upper(), headers=send)
        try:
            with urllib.request.urlopen(request, timeout=timeout or 30) as response:
                return Outcome(True, output=response.read().decode("utf-8", "replace"), status=response.status)
        except urllib.error.HTTPError as error:
            text = error.read().decode("utf-8", "replace")
            retryable = error.code >= 500 or error.code in RETRY_4XX
            return Outcome(False, retryable, f"HTTP {error.code} {text[:120]}".strip(), output=text, status=error.code,
                           retry_after=retry_after(error.headers.get("Retry-After")))
        except (TimeoutError, socket.timeout):
            return Outcome(False, True, f"timeout {timeout or 30:.1f}s")
        except urllib.error.URLError as error:
            if isinstance(error.reason, (TimeoutError, socket.timeout)):
                return Outcome(False, True, f"timeout {timeout or 30:.1f}s")
            return Outcome(False, True, f"connection: {error.reason}")
    return attempt
