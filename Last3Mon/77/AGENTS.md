# AGENTS.md · n8n 실행 로그 분석 작업 규칙 (77일차 실습 폴더)

이 파일은 **CLI 코딩 에이전트**(Codex, Claude Code, Antigravity 등)가 이 폴더에서 n8n 워크플로우를 만들 때 따르는 규칙입니다. 사람도 읽을 수 있게 썼습니다. 76일차 규칙과 같고, 3절이 오늘 만드는 **로그 보고서 · 요약 · 주간 보고 · SLO 알림 · 라이브 헬프데스크의 계약**과 **지표 정의**, 5절에 로그를 읽고 계산하는 노드가 더해졌습니다.

## 1. 작업 순서 (항상 이 순서)

1. 요청을 읽고, 만들 워크플로우의 **입력 · 노드 순서 · 결과 모양**을 3~5줄로 먼저 정리해 보여 준다. 지표 요청이면 **지표 정의(무엇을 세고 무엇으로 나누는지)** 를 먼저 적어 보여 준다.
2. 워크플로우 JSON을 `my-work/<이름>.json`에 쓴다. 이미 있으면 그 파일을 고친다 (새 파일을 만들지 않는다).
3. `uv run tools/flow.py check my-work/<이름>.json` → 오류(✘)가 없을 때까지 고친다.
4. 끝나면 한국어로 짧게 보고한다: 바꾼 노드, check 결과, 그리고 사람이 실행할 명령 두 줄.
   ```bash
   uv run tools/flow.py push my-work/<이름>.json
   uv run tools/flow.py test cases/<요청에 나온 테스트 파일>.json
   ```
5. **push와 test는 사람이 실행해 결과를 확인한다.** 사람이 "네가 push·test까지 해"라고 하면 직접 실행해도 된다.
6. 사람이 실패 보고서(`runs/*.json`)를 알려 주면 실패한 케이스의 요청·응답을 읽고 원인을 설명한 뒤 고친다. **같은 곳을 3번 고쳐도 실패하면 멈추고** 다른 방법을 제안한다.
7. 문서(`my-work/*.md`)를 써 달라는 요청이면 워크플로우를 만들지 않고 문서만 쓴다.

## 2. 환경 (바꾸지 말 것)

| 항목 | 값 |
| --- | --- |
| n8n | 2.42.6, 65일차 공식 설치 `~/day65-n8n` (Docker 프로젝트 `day65-n8n`), 브라우저 http://localhost:5678 |
| n8n 켜고 끄기 | `~/aio-01d4-stu/Last3Mon/65/n8n`에서 `docker compose start/stop` (사람이 함, Ollama 컨테이너는 없음) |
| 게시된 웹훅 주소 | 밖에서 · n8n 안에서 모두 `http://localhost:5678/webhook/<path>` |
| OpenAI Credential | id `openAiCourse0001`, name `OpenAI (.env)`, 모델 `gpt-4.1-mini` |
| 다른 Credential | 쓰지 않음 (Ollama 등 없음) |
| 데이터 API | n8n 안에서 `http://data-api:8800`, 터미널에서 `http://localhost:8800` (**77일차 판** `Last3Mon/77/data-api`: 76일차 + 실행 로그 + FAQ 더하기) |
| 비교 기준 · 제공 | `reference/baseline-report.json` (`base-report`, 팀이 지난달 급히 만든 보고서 — 정의가 다름, 고치지 않는다) · `reference/helpdesk-live.json` (`my-helpdesk`, 실행마다 로그를 남기는 헬프데스크 — Lab 03에서 복사해 고침) |

### 데이터 API (77일차 판)

| 요청 | 응답 |
| --- | --- |
| `POST /logs/query` 본문 `{"from": "2026-10-26", "to": "2026-10-30", "tag": "", "source": "all"}` | `{"count", "logs": [...]}` — 날짜는 **포함**(`from ≤ 날짜 ≤ to`), 비우면 전체. `source`: `all` · `seed`(두 주 기록) · `live`(오늘 실습) |
| `GET /logs?from=&to=&tag=&source=&limit=` | 같음 |
| `POST /logs` 본문 `{"items": [{...}]}` | 실행 기록 더하기 (`started_at`이 없으면 지금) |
| `POST /logs-reset` | 오늘 실습 기록(`live`)만 지움 (두 주 기록은 그대로). 본문 `{"tag": "after"}`면 그 `tag`의 기록만 |
| `POST /faq/add` 본문 `{"id", "title", "keywords": [...], "answer"}` · `POST /faq-reset` | FAQ 더하기 · 되돌리기 (**사람이**) |
| `GET /faq-extra` | 오늘 더한 FAQ `{"count", "faq"}` |
| `POST /alerts` · `POST /alerts/list` · `POST /alerts/latest` | 알림 남기기 · 거르기 `{"workflow", "reason", "within": 초}` · 가장 최근 (76일차와 같음) |
| `POST /admin/fault` | `{"faq": "slow", "slow_seconds": 1.2}` 등 (72일차와 같음, **사람이** · 테스트가) |

`uv run tools/flow.py logs [--from --to --tag --source --last N]`가 기록을 훑어보고, `ops`가 오늘 기록 · 더한 FAQ · 알림을, `ops --reset`이 그것을 비웁니다 (**사람이**).

### 실행 기록 한 줄

```json
{"execution_id": 5301, "workflow": "helpdesk", "started_at": "2026-10-26T09:05:39", "user": "윤하늘", "topic": "비밀번호",
 "question": "...", "release": "1.0.0", "channel": "stable", "status": "success" | "error", "error_node": null, "error_message": null,
 "route": "자동 답변" | "담당자 연결" | "잠시 후" | null, "duration_ms": 1164, "steps": {"faq_ms": 20, "answer_ms": 1100},
 "llm_calls": 1, "cost_usd": 0.00012, "repeat": false, "tag": ""}
```
- `route`가 `null`이면 실행이 오류로 끝난 것. `repeat`: 같은 사람이 10분 안에 같은 주제를 다시 물음 (답이 도움이 안 됐다는 신호).
- `steps`: 단계마다 걸린 시간. 그 단계를 거치지 않은 실행은 0 (`잠시 후`는 FAQ · 답 모두 0, `담당자 연결`은 답 0).

## 3. 오늘 만드는 것의 계약과 지표 정의

| 무엇 | 파일 · 웹훅 | 입력 (본문) | 결과 |
| --- | --- | --- | --- |
| 로그 보고서 | `my-work/log-report.json` · `POST /webhook/my-log-report` | `from`, `to`, `tag`, `source`, `slo`(선택) | 아래 지표 |
| 로그 요약 | `my-work/log-summary.json` · `POST /webhook/my-log-summary` | 보고서와 같음 | `{"summary", "numbers_ok", "unknown_numbers", "top_topic", "worst_hour"}` |
| 주간 보고 | `my-work/weekly.json` · `POST /webhook/my-weekly` | `from`, `to`, `prev_from`, `prev_to` | `{"markdown", "total", "error_rate", "slo_ok", "numbers_ok"}` |
| SLO 알림 (Lab 03 과제 2) | `my-work/slo-alert.json` · `POST /webhook/my-slo-alert` | 보고서와 같음 + `slo` | `{"ok", "breaches", "alert": "sent" \| "suppressed" \| "none", "message", "total"}` + 보낼 때 `POST /alerts` |
| 라이브 헬프데스크 | `my-work/helpdesk.json` · `POST /webhook/my-helpdesk` (제공 파일을 복사) | `question`, `user`, `tag` | `{"route", "status", "topic", "answer", "error"}` + `/logs`에 한 줄 |

| 지표 | 정의 |
| --- | --- |
| `total` · `errors` | 실행 수 · `status`가 `error`인 수 |
| `error_rate` | `errors / total`, 소수 4자리 반올림 (0건이면 0) |
| `p50_ms` · `p95_ms` | `duration_ms`를 오름차순으로 놓고 **`ceil(p × n)`번째** 값 (n = 실행 수, 오류 포함) |
| `by_route` | `route`별 수, `null`은 `"오류"` |
| `by_day` | `{"2026-10-26": {"total", "errors", "error_rate"}}`, 날짜순 |
| `by_release` | `route`가 `자동 답변`인 실행만: `{"1.2.0": {"answers", "repeats", "repeat_rate"}}` |
| `steps` (Lab 01 과제 2) | `{"faq_ms": {"runs", "p50", "p95"}, "answer_ms": {...}}` — 그 단계 값이 0보다 큰 실행만, 백분위 정의는 위와 같음 |
| `cost_usd` · `cost_per_run` · `llm_calls` | 비용 합(소수 5자리) · 실행당 비용(`cost_usd / total`, 소수 6자리, 0건이면 0) · LLM 호출 수 합 |
| `failures` | 오류를 `(error_node, error_message)`로 묶어 `[{"node", "message", "count"}]`, 많은 순 |
| `unanswered_topics` | `route`가 `담당자 연결`인 실행을 `topic`으로 묶어 `[{"topic", "count"}]`, 많은 순 |
| `repeat_topics` (Lab 02 과제 1) | `자동 답변`인 실행을 `topic`으로 묶어 `[{"topic", "answers", "repeats", "repeat_rate"}]`, 다시 물음이 0인 주제는 빼고, `repeat_rate` 높은 순(같으면 `repeats` 많은 순) |
| `anomalies` | 시간(`started_at` 앞 13자, 예 `2026-10-26T09`)별로 묶어 **실행 5건 이상**이고 **오류율 ≥ 전체 오류율의 3배**이고 오류가 1건 이상인 시간 `[{"hour", "total", "errors", "error_rate"}]`, 시간순 |
| `unanswered_rate` | `담당자 연결` 수 / `total` |
| `slo` | 기준(기본 `error_rate` 0.01 · `p95_ms` 3000 · `unanswered_rate` 0.02, 본문 `slo`로 바꿀 수 있음)을 넘은 지표 이름 `breaches`, `ok`, `limits` |

- 비율은 모두 소수 4자리 반올림, 분모가 0이면 0. 날짜는 **포함**(`from ≤ started_at 앞 10자 ≤ to`, 데이터 API가 거름).
- 요약의 숫자 확인: 요약 글의 숫자가 모두 통계 안에 있는지(비율은 ×100 반올림도 허용, 날짜 · 시간의 숫자 허용) **Code가** 확인해 `numbers_ok`. 요약은 `my-log-report`를 **다시 불러** 받은 통계로 쓴다 (정의를 두 벌 만들지 않는다).
- SLO 알림: `breaches`가 없으면 `none`. 있으면 `POST /alerts/list {"workflow": "slo", "reason": "slo", "within": 600}`로 10분 안의 같은 알림을 보고, 있으면 `suppressed`, 없으면 `POST /alerts {"workflow": "slo", "severity": "high", "reason": "slo", "breaches", "message"}` 후 `sent`. `message`는 `SLO breach: error_rate 0.0588 > 0.01, …`.

## 4. 워크플로우 파일 규칙

```json
{"name": "77 Log report (my)", "nodes": [ ... ], "connections": { ... }, "settings": { "executionOrder": "v1" }}
```

- 파일 하나에 워크플로우 하나. 노드 `name`은 영어로, 겹치지 않게. **API 키를 JSON에 쓰지 않는다.**
- **숫자는 Code가 계산한다.** LLM에게 통계를 계산하게 하지 않는다 (LLM은 계산된 통계를 글로 설명만).

## 5. 검증된 노드 (n8n 2.42.6에서 실행 확인)

### 로그 가져오기 (HTTP POST) → 계산 (Code)
```json
{"name": "Get logs", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [220, 300],
 "parameters": {"method": "POST", "url": "http://data-api:8800/logs/query", "sendBody": true, "specifyBody": "json",
   "jsonBody": "={{ JSON.stringify({ from: $json.body.from ?? '', to: $json.body.to ?? '', tag: $json.body.tag ?? '', source: $json.body.source ?? 'all' }) }}", "options": {}}}
```
```json
{"name": "Compute metrics", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [440, 300],
 "parameters": {"jsCode": "const rows = $json.logs ?? [];\nconst pct = (vals, p) => { const s = [...vals].sort((a, b) => a - b); return s.length ? s[Math.max(0, Math.ceil(p * s.length) - 1)] : 0; };\n...\nreturn [{ json: out }];"}}
```
- 로그 600여 줄은 Code 하나에서 계산해도 충분히 빠르다 (수업 준비 때 0.1초 안팎).

### 다른 내 웹훅을 부르기 (주간 보고)
```json
{"name": "This week", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [220, 300],
 "parameters": {"method": "POST", "url": "http://localhost:5678/webhook/my-log-report", "sendBody": true, "specifyBody": "json",
   "jsonBody": "={{ JSON.stringify({ from: $json.body.from, to: $json.body.to }) }}", "options": {"timeout": 30000}}}
```

### AI Agent + OpenAI chat model (요약 글만)
- 67~76일차와 같다. `text`에는 필요한 통계만 JSON으로(`={{ JSON.stringify({ total: $json.total, failures: $json.failures, … }) }}`), 지시문에 "통계에 있는 숫자만 · 원인을 짐작하지 말 것".

### 라이브 헬프데스크 (제공 파일)
- `Topic`(Code, 낱말로 주제 · 시작 시각) → `Search FAQ`(HTTP, **timeout 1000ms**, 실패하면 오류 출력 → `Failed`) → `FAQ done`(FAQ 단계 시간) → `Found?` → `Answer`(Agent) 또는 `Not found` → `Log …`(POST `/logs`, `steps.faq_ms` · `steps.answer_ms` 포함) → 응답.
- 실행 기록은 갈래마다 같은 모양으로 남긴다 (2절 "실행 기록 한 줄").

## 6. 연결 · 7. 표현식

- 72~76일차와 같다. 다른 노드 뒤에서 웹훅 입력은 `$('Report webhook').first().json.body`.
- 키에 점이 없는 결과 필드는 테스트에서 `by_day.2026-10-26.errors`처럼 내려간다. 키에 점이 있으면(`1.2.0`) `contains`로 JSON 글자를 찾는다.

## 8. 테스트 파일 (`cases/*.json`)

```json
{"webhook": "my-log-report", "cases": [
  {"name": "둘째 주", "request": "requests/week2.json", "expect": {"equals": {"total": 357, "errors": 21, "error_rate": 0.0588}}},
  {"name": "고친 뒤", "body": {"tag": "after", "source": "live"}, "expect": {"equals": {"errors": 0}}}
]}
```
- 케이스마다 `body` 또는 `request`(파일), 다른 웹훅은 `"webhook"`, 데이터 API를 읽을 때는 `"url"`(POST). 파일 맨 위 `before`는 테스트 전에 한 번 (`/logs-reset` · 고장 스위치 등). `"range": {"steps.faq_ms.p50": [1150, 3500]}`는 범위 (오늘 실습 기록의 시간처럼 실행마다 다른 값).
- `--webhook base-report`를 붙이면 같은 케이스를 다른 웹훅에 돌린다 (기준과 비교).
- 기대 숫자는 두 주 기록(`data-api/data/run-logs.json`)을 3절 정의대로 계산한 값입니다. **테스트를 통과시키려고 기대 결과나 로그 파일을 바꾸지 않는다.** 정의가 다르다고 생각되면 사람에게 묻는다.

## 9. 하지 말 것

- `tools/`, `data-api/`(로그 파일 포함), `requests/`, `reference/`, 이 파일을 고치지 않는다 (요청받은 경우만).
- 워크플로우 안에서 `/logs-reset` · `/faq/add` · `/faq-reset` · `/alerts-clear` · 고장 스위치를 부르지 않는다.
- `reference/baseline-report.json`을 고쳐 테스트를 통과시키지 않는다 (오늘은 기준과 **비교**하는 연습).
- 요약 글에 통계에 없는 숫자 · 짐작한 원인을 넣지 않는다.
- n8n 컨테이너를 지우거나 `docker compose down`을 하지 않는다. `~/day65-n8n`을 읽거나 고치지 않는다. Credential을 새로 만들지 않는다. `.env`나 API 키를 출력하지 않는다.
