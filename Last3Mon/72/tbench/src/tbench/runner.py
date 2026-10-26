"""Call a URL many times. run() yields one result dict per call, as it finishes."""
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx


def call_once(client, url, method, body, headers, timeout):
    """One call, timed from just before sending until the whole body is read."""
    start = time.perf_counter()
    status, error_kind, timings = None, None, None
    try:
        response = client.request(method, url, content=body, headers=headers, timeout=timeout)
        response.read()
        status = response.status_code
        if status >= 500:
            error_kind = "http_5xx"
        elif status >= 400:
            error_kind = "http_4xx"
        else:
            try:
                data = response.json()
                if isinstance(data, dict) and isinstance(data.get("timings"), dict):
                    timings = data["timings"]
            except ValueError:
                pass
    except httpx.TimeoutException:
        error_kind = "timeout"
    except httpx.TransportError:
        error_kind = "connect"
    return {"status": status, "seconds": round(time.perf_counter() - start, 4),
            "error_kind": error_kind, "timings": timings}


def run(url, body=None, n=10, method="POST", headers=None, timeout=30.0, warmup=0, concurrency=1):
    """Yield warmup calls (warmup=True) first, then n measured calls numbered 1..n."""
    headers = dict(headers or {})
    if body is not None and not any(k.lower() == "content-type" for k in headers):
        headers["Content-Type"] = "application/json"
    content = body.encode() if isinstance(body, str) else body
    with httpx.Client() as client:
        for w in range(warmup):
            r = call_once(client, url, method, content, headers, timeout)
            yield {"i": w + 1, "warmup": True, "note": "warmup", **r}
        first_note = "first call" if warmup == 0 else ""
        if concurrency <= 1:
            for i in range(1, n + 1):
                r = call_once(client, url, method, content, headers, timeout)
                yield {"i": i, "warmup": False, "note": first_note if i == 1 else "", **r}
            return
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = {pool.submit(call_once, client, url, method, content, headers, timeout): i
                       for i in range(1, n + 1)}
            for future in as_completed(futures):
                i = futures[future]
                yield {"i": i, "warmup": False, "note": first_note if i == 1 else "", **future.result()}


def read_body(path):
    """Read a JSON body file; keep the exact text so its hash matches what was sent."""
    if path is None:
        return None
    with open(path, encoding="utf-8") as f:
        text = f.read()
    json.loads(text)
    return text
