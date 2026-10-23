#!/usr/bin/env python3
"""Interactive HTTP integration checks for an unpublished Routine Scout workflow.

No request is sent until the operator selects a case and types POST for that
specific request. --list is read-only.
"""

import argparse
import datetime as dt
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


HERE = Path(__file__).resolve().parent
CASES_FILE = HERE / "routine-scout.json"
RESULTS_FILE = HERE / "http-results.jsonl"
STATUS_FILE = HERE / "TEST-STATUS.md"
TEST_URL = "http://localhost:5678/webhook-test/routine-scout/analyze"


def value_at(data, dotted):
    value = data
    for part in dotted.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        elif isinstance(value, list) and part.isdigit() and int(part) < len(value):
            value = value[int(part)]
        else:
            return None
    return value


def compare(expect, status, body):
    differences = []
    wanted_status = expect.get("status", 200)
    if status != wanted_status:
        differences.append(f"HTTP 상태: 기대 {wanted_status}, 실제 {status}")
    for field, wanted in expect.get("equals", {}).items():
        actual = value_at(body, field)
        if actual != wanted:
            differences.append(
                f"{field}: 기대 {json.dumps(wanted, ensure_ascii=False)}, "
                f"실제 {json.dumps(actual, ensure_ascii=False)}"
            )
    return differences


def parse_response(raw):
    if not raw.strip():
        return None, "응답 본문이 비어 있습니다."
    try:
        return json.loads(raw.decode("utf-8")), None
    except (UnicodeDecodeError, json.JSONDecodeError):
        return raw.decode("utf-8", errors="replace"), "응답 본문이 JSON이 아닙니다."


def run_case(case):
    payload = json.dumps(case["request"], ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        TEST_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    # Never inherit HTTP proxy settings for this local-only test.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=15) as response:
            status, raw = response.status, response.read()
    except urllib.error.HTTPError as error:
        status, raw = error.code, error.read()
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return {
            "result": "ERROR",
            "http_status": None,
            "response": None,
            "differences": [f"요청 실패: {error}"],
        }
    body, parse_error = parse_response(raw)
    differences = compare(case["expect"], status, body)
    if status == 404:
        return {
            "result": "ERROR",
            "http_status": status,
            "response": body,
            "differences": [
                "HTTP 404: Test Webhook이 등록되지 않았을 수 있습니다. "
                "n8n에서 Execute workflow를 누른 뒤 이 케이스를 다시 선택하세요.",
                *differences,
            ],
        }
    if parse_error:
        return {
            "result": "ERROR",
            "http_status": status,
            "response": body,
            "differences": [parse_error, *differences],
        }
    return {
        "result": "FAIL" if differences else "PASS",
        "http_status": status,
        "response": body,
        "differences": differences,
    }


def record(case, result):
    entry = {
        "kind": "http_integration",
        "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "case": case["name"],
        "url": TEST_URL,
        "request": case["request"],
        "expected": case["expect"],
        **result,
    }
    with RESULTS_FILE.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(entry, ensure_ascii=False) + "\n")


def previous_results(cases):
    """Combine manually documented passes with the latest recorded HTTP result."""
    names = {case["name"] for case in cases}
    results = {}
    if STATUS_FILE.exists():
        for line in STATUS_FILE.read_text(encoding="utf-8").splitlines():
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            if len(cells) >= 4 and cells[0] in names and cells[3] == "통과":
                results[cells[0]] = {"result": "PASS", "source": "TEST-STATUS.md"}
    if RESULTS_FILE.exists():
        for line in RESULTS_FILE.read_text(encoding="utf-8").splitlines():
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("kind") == "http_integration" and entry.get("case") in names:
                results[entry["case"]] = {
                    "result": entry.get("result", "ERROR"),
                    "source": "http-results.jsonl",
                    "http_status": entry.get("http_status"),
                }
    return results


def show_summary(cases, previous):
    passed = sum(previous.get(case["name"], {}).get("result") == "PASS" for case in cases)
    print(f"구조화 HTTP 통합 테스트: {passed}/{len(cases)}개 통과, {len(cases) - passed}개 남음")
    print("TEST-STATUS.md에 옮겨 적을 수 있는 요약 (Code 노드 독립 테스트와 별개):")
    print("| 번호 | 케이스 | 현재 기록 | 근거 |")
    print("| --- | --- | --- | --- |")
    for index, case in enumerate(cases, 1):
        entry = previous.get(case["name"], {})
        print(f"| {index} | {case['name']} | {entry.get('result', '미검증')} | {entry.get('source', '-')} |")


def choose_cases(cases, previous):
    remaining = [(index, case) for index, case in enumerate(cases, 1)
                 if previous.get(case["name"], {}).get("result") != "PASS"]
    if not remaining:
        print("남은 미통과 케이스가 없습니다.")
        return []
    print("\n남은 케이스:")
    for index, case in remaining:
        print(f"{index:2}. {case['name']}")
    print("원래 케이스 번호 하나, 쉼표로 구분한 번호, all(남은 케이스 전부) 또는 q를 입력하세요.")
    choice = input("선택: ").strip().lower()
    if choice in ("q", ""):
        return []
    if choice == "all":
        return [case for _, case in remaining]
    try:
        indexes = [int(part.strip()) for part in choice.split(",")]
    except ValueError:
        print("번호를 입력하세요.")
        return []
    allowed = {index for index, _ in remaining}
    if not indexes or any(index not in allowed for index in indexes):
        print("남은 케이스 번호만 선택할 수 있습니다. 이미 통과한 케이스는 중복 실행하지 않습니다.")
        return []
    return [cases[index - 1] for index in dict.fromkeys(indexes)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="케이스 목록만 표시하고 종료 (요청 없음)")
    parser.add_argument("--summary", action="store_true", help="기록을 요약하고 종료 (요청 없음)")
    args = parser.parse_args()
    suite = json.loads(CASES_FILE.read_text(encoding="utf-8"))
    if suite.get("webhook") != "routine-scout/analyze":
        print("예상과 다른 Webhook 경로입니다. 요청을 보내지 않습니다.", file=sys.stderr)
        return 2
    cases = suite["cases"]
    previous = previous_results(cases)
    if args.list:
        for index, case in enumerate(cases, 1):
            state = previous.get(case["name"], {}).get("result", "미검증")
            print(f"{index:2}. {case['name']} (예상 HTTP {case['expect'].get('status', 200)}, {state})")
        print(f"총 {len(cases)}개; HTTP 요청 0개")
        return 0
    if args.summary:
        show_summary(cases, previous)
        print("HTTP 요청 0개")
        return 0
    print("HTTP 통합 테스트 전용입니다. Code 노드 독립 테스트 결과와 별도로 기록합니다.")
    print(f"대상 Test URL: {TEST_URL}")
    show_summary(cases, previous)
    selected = choose_cases(cases, previous)
    if not selected:
        print("선택한 케이스가 없어 요청을 보내지 않았습니다.")
        return 0
    for case in selected:
        # A previous selection in this same session may have just passed.
        if previous.get(case["name"], {}).get("result") == "PASS":
            print(f"SKIP {case['name']}: 이미 통과했습니다.")
            continue
        print(f"\n케이스: {case['name']}")
        print("n8n에서 해당 워크플로우의 Execute workflow를 눌러 Test Webhook을 대기시키세요.")
        print("요청 JSON:")
        print(json.dumps(case["request"], ensure_ascii=False, indent=2))
        print(f"예상 HTTP: {case['expect'].get('status', 200)}")
        print("예상 JSON:")
        print(json.dumps(case["expect"].get("equals", {}), ensure_ascii=False, indent=2))
        confirmation = input("이 케이스를 지금 POST하려면 POST를 정확히 입력하세요 (그 외 건너뜀): ")
        if confirmation != "POST":
            print("SKIP: 요청하지 않았습니다.")
            continue
        result = run_case(case)
        print(f"{result['result']} {case['name']} · HTTP {result['http_status']}")
        print("실제 응답:")
        print(json.dumps(result["response"], ensure_ascii=False, indent=2))
        for difference in result["differences"]:
            print("차이/오류:", difference)
        try:
            record(case, result)
            print(f"기록: {RESULTS_FILE}")
            previous[case["name"]] = {"result": result["result"], "source": "http-results.jsonl"}
        except OSError as error:
            print(f"기록 실패: {error}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
