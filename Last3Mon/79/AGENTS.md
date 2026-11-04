# AGENTS.md · n8n Workflow Ops Assistant 작업 규칙 (79일차 실습 폴더)

이 파일은 **CLI 코딩 에이전트**(Codex, Claude Code, Antigravity 등)가 이 폴더에서 n8n 워크플로우를 만들 때 따르는 규칙입니다. 사람도 읽을 수 있게 썼습니다. 78일차 규칙과 같고, 3절에 오늘 만드는 **운영 사실 · 질문 답변 · 브리핑 · 평가의 계약**과 **사실 · 상태 정의**, 5절에 여러 출처를 모으는 노드가 더해졌습니다.

## 1. 작업 순서 (항상 이 순서)

1. 요청을 읽고, 만들 워크플로우의 **입력 · 노드 순서 · 결과 모양**을 3~5줄로 먼저 정리해 보여 준다. 사실 · 상태 요청이면 **정의(어느 출처의 무엇을 어떻게 셀지)** 를 먼저 표로 보여 준다.
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
| 데이터 API | n8n 안에서 `http://data-api:8800`, 터미널에서 `http://localhost:8800` (**79일차 판** `Last3Mon/79/data-api`: 78일차 + **운영 아침 상태**를 켤 때 채워 둠) |
| 비교 기준 · 제공 | `reference/baseline-ops-facts.json` (`base-ops-facts`, 팀이 지난달 만든 아침 대시보드 — 기간 없이 전체를 셈, 품질 · 릴리스 없음) · `reference/baseline-ops-ask.json` (`base-ops-ask`, 사실 전부를 LLM에게 주고 무엇이든 답하던 챗봇). **고치지 않는다** (비교용). `reference/ops-facts-health.json`은 Lab 01 과제를 못 끝냈을 때 Lab 02 · 03에 쓰는 사실 |

### 운영 아침 상태 (2026-11-04 08:30, 연습 데이터)

데이터 API를 켜거나 `POST /ops-reset`을 하면 아래 상태로 돌아갑니다 (`data-api/data/ops-seed.json`).

| 출처 (72~78일차) | 요청 | 들어 있는 것 |
| --- | --- | --- |
| 실행 기록 (77) | `POST /logs/query` `{"from", "to"}` | 두 주 666줄 (10/19~10/30) |
| 알림 (76 · 78) | `GET /alerts` → `{"count", "alerts": [{"workflow", "node", "severity", "reason", "message", "at"}]}` | 6건 |
| DLQ (76) | `GET /dlq` → `{"size", "items": [{"dlq_id", "item", "reason", "attempts", "parked"}]}` | 3건 |
| 품질 기록 · 격리함 (78) | `GET /quality-log` → `{"count", "items"}`, `GET /quarantine` → `{"size", "items"}` | 4줄 · 1건 |
| 사용량 · 예산 (75) | `GET /usage/summary` → `{"requests", "calls", "cost_usd", "by_user": {이름: {"cost_usd"}}}`, `GET /budget` → `{"daily_usd", "used_usd"}` | 오늘 192번 부름 · 예산 $0.08 |
| 릴리스 (74) | `GET /releases/helpdesk` → `{"active", "canary": {"release", "percent"} 또는 null}` | 1.1.0 + 카나리 1.2.0 20% |
| 감사 기록 (73) | `POST /audit` 본문 `{...}` 한 줄 더하기 · `GET /audit` (`POST /audit/list`) → `{"events": [...]}` | 처음엔 비어 있음 (Lab 02 과제 2) |
| 고장 스위치 (72) | `POST /admin/fault {"usage": "error"}` → `GET /usage/summary`가 500 (79일차 판) | **사람이** · 테스트가 (Lab 01 과제 2) |
| 되돌리기 | `POST /ops-reset` · `GET /ops/seed-info` | **사람이** · 테스트가 (`flow.py morning --reset`, `ops --reset`과 같음) |

## 3. 오늘 만드는 것의 계약과 정의

| 무엇 | 파일 · 웹훅 | 입력 (본문) | 결과 |
| --- | --- | --- | --- |
| 운영 사실 | `my-work/ops-facts.json` · `POST /webhook/my-ops-facts` | `from`, `to` (비면 `2026-10-26` · `2026-10-30`) | 아래 "사실" (과제 1: + `health`, `red`, `yellow`, `overall` · 과제 2: + `sources_down`, `unknown`) |
| 질문 답변 | `my-work/ops-ask.json` · `POST /webhook/my-ops-ask` | `question` | `{"question", "area", "router", "refused", "reason", "answer", "numbers_ok", "unknown_numbers"}` (과제 2: 질문마다 감사 기록 한 줄) |
| 브리핑 | `my-work/ops-brief.json` · `POST /webhook/my-ops-brief` | `from`, `to` | `{"overall", "red", "yellow", "actions": [{"area", "status", "action"}], "markdown"}` (+ `summary`, `numbers_ok`) |
| 평가 | `my-work/ops-eval.json` · `POST /webhook/my-ops-eval` | `{"cases": [{"question", "area", "refused", "numbers"}], "min_score"}` (`min_score`는 과제 2, 기본 0.9) | `{"total", "passed", "score", "area_ok", "refused_ok", "number_ok", "grounded", "failed": [...]}` (과제 2: + `min_score`, `gate`), 빈 목록이면 **400** |

### 사실 (`my-ops-facts`)

| 필드 | 정의 |
| --- | --- |
| `period` | `{"from", "to"}` 쓴 기간 |
| `runs` | 그 기간 실행 기록: `total`, `errors`, `error_rate`, `p95_ms`, `unanswered_rate` (**77일차 정의 그대로**), `top_failure` `{"node", "message", "count"}` 가장 많은 (노드, 메시지) 묶음 또는 `null` |
| `alerts` | `count`, `high`(`severity`가 `high`), `by_reason` `{reason: 수}` |
| `dlq` | `size`, `parked`, `waiting`(parked 아님) |
| `quality` | `batches`(품질 기록 줄 수), `avg_score`(4자리), `last_score`(마지막 줄, 없으면 `null`), `rejected_batches`, `quarantine`(격리함 수) |
| `cost` | `requests`, `calls`, `cost_usd`(6자리), `daily_usd`, `used_ratio`(`used_usd / daily_usd`, 4자리), `top_user` `{"user", "cost_usd", "share"}` 비용 1위 사용자 |
| `release` | `active`, `canary_release`(없으면 `null`), `canary_percent`(없으면 0), `active_repeat_rate` · `canary_repeat_rate`: 그 기간 `자동 답변` 실행 중 그 릴리스의 `repeat` 비율(4자리, 실행이 없으면 `null`) |

- 기간은 **실행 기록에만** 적용합니다. 알림 · DLQ · 품질 · 비용 · 릴리스는 "지금" 상태입니다. 0건이면 비율 · p95는 0, `top_failure` · 반복 비율은 `null`.

### 출처가 멈추면 (Lab 01 과제 2)

| 출처가 답하지 않으면 (HTTP 오류 · 모양이 다름) | 처리 |
| --- | --- |
| 그 영역 | 사실을 `null`, `sources_down`에 영역 이름 (이 순서: alerts, dlq, quality, cost, release — 실행 기록이 멈추면 워크플로우 오류) |
| 상태 | `health`의 그 영역은 `unknown`, `unknown` 목록에 (`red` · `yellow`에는 넣지 않음) |
| 전체 | red가 있으면 red, 아니면 yellow나 unknown이 있으면 **yellow**, 아니면 green — 모르는 것을 초록으로 말하지 않음 |
| 응답 | 언제나 HTTP 200 (다른 출처의 사실은 그대로) |

- HTTP 노드에 `neverError`를 켜야 출처 하나의 오류가 워크플로우 전체를 멈추지 않는다. 비용은 `usage/summary`의 `cost_usd`와 `budget`의 `daily_usd`가 숫자일 때만 "답했다"로 본다.

### 상태 (Lab 01 과제)

| 영역 | 🔴 red | 🟡 yellow | 그 밖 🟢 green |
| --- | --- | --- | --- |
| `runs` | `error_rate > 0.01` | `unanswered_rate > 0.02` | |
| `alerts` | `high ≥ 5` | `count ≥ 1` | |
| `dlq` | `parked > 0` | `size > 0` | |
| `quality` | `last_score < 0.8` | `last_score < 0.9` 또는 `quarantine > 0` | |
| `cost` | `used_ratio ≥ 1` | `used_ratio ≥ 0.8` | |
| `release` | 카나리가 있고 두 비율이 모두 있고 `canary_repeat_rate > 2 × active_repeat_rate` | 카나리가 있음 | |

- `health` `{영역: 색}`, `red` · `yellow`: 그 색인 영역을 **이 순서**(runs, alerts, dlq, quality, cost, release)로, `overall`: red가 있으면 red, 아니면 yellow가 있으면 yellow, 아니면 green.

### 질문 답변 (`my-ops-ask`)

| 단계 | 규칙 |
| --- | --- |
| 작업 요청 (Lab 02 예제 2) | "다시 돌려 · 재처리해 · 지워 · 삭제해 · 꺼 줘 · 켜 줘 · 배포해 · 되돌려 · 롤백해 · 바꿔 줘 · 올려 줘 · 내려 줘 · 비워 줘"가 있으면 **거절**: `area: "action"`, `refused: true`, `reason: "read_only"`, LLM을 부르지 않음 |
| 낱말 라우터 | 영역마다 낱말 목록(아래), 맞은 낱말이 가장 많은 영역 (같으면 위의 순서 앞), 하나도 없으면 `unknown`, `router: "keyword"` |
| LLM 라우터 (Lab 02 과제) | 낱말 라우터가 `unknown`일 때만 LLM이 영역 하나 또는 `none`을 고름, `router: "llm"` |
| 운영 밖 | 끝까지 `unknown`이면 거절: `refused: true`, `reason: "out_of_scope"` |
| 답 | 사실 중 **그 영역만**(`overview`면 전부)을 LLM에게, 한국어 2~3문장, 사실에 있는 숫자만 |
| 숫자 확인 (Lab 02 예제 2) | 답의 숫자가 모두 그 영역 사실 안에 있는지(값, ×100, 반올림, 글자 속 숫자, 버전 `1.2.0`은 통째로) Code가 → `numbers_ok`, `unknown_numbers` |

| 영역 | 낱말 |
| --- | --- |
| `runs` | 오류, 에러, 실패율, 느려, 느린, 응답 시간, p95, 실행 |
| `alerts` | 알림, 경보 |
| `dlq` | dlq, 재처리, 쌓인, parked, 접수 실패 |
| `quality` | 품질, 배치, 격리 |
| `cost` | 비용, 돈, 예산, 토큰, 요금 |
| `release` | 릴리스, 버전, 카나리, 배포 |
| `overview` | 괜찮, 상태, 요약, 전체, 브리핑 |

### 브리핑 (`my-ops-brief`)

- 사실(상태 포함)을 다시 부름. `actions`: `red` 다음 `yellow`의 앞 3개, 영역마다 정해진 할 일 (아래). `markdown`: 제목 · 전체 · 영역 표(`| 영역 | 상태 | 숫자 |`) · "## 먼저 볼 것".
- (Lab 03 예제 2) LLM 세 문장 `summary` + 숫자 확인 `numbers_ok`, `markdown` 끝에 "## 요약".

| 영역 | 표의 이름 · 숫자 | 할 일 |
| --- | --- | --- |
| `runs` | 실행 · `오류율 5.88% · p95 2598ms · 답 못 함 4.76%` | 오류 묶음 1위 확인 · 고치기 (77일차) |
| `alerts` | 알림 · `6건 (높음 3)` | 높은 알림부터 확인하고 닫기 (76일차) |
| `dlq` | DLQ · `3건 (parked 2)` | parked 건 원인 확인 뒤 런북대로 재처리 (76일차) |
| `quality` | 데이터 품질 · `평균 0.6583 · 마지막 1 · 격리 1` | 격리함을 콘텐츠 담당자에게 (78일차) |
| `cost` | 비용 · `$0.073604 / $0.08 (92.01%)` | 비용 1위 사용자 · 한도 확인 (75일차) |
| `release` | 릴리스 · `1.1.0 · 카나리 1.2.0 20% (다시 묻기 62.5%)` | 카나리 끄기 · 되돌리기 검토 (74일차) |

- 상태 표시: 🔴 · 🟡 · 🟢 (출처가 멈춘 영역은 ⚪, 숫자 칸은 `출처 응답 없음`).

### 감사 기록 (Lab 02 과제 2)

- 질문마다 응답하기 **전에** `POST http://data-api:8800/audit` 한 줄: `{"kind": "ops-ask", "question", "area", "router", "refused", "reason", "numbers_ok"}` (거절이면 `numbers_ok: null`). 갈래 셋(작업 거절 · 운영 밖 · 답) 모두. 응답은 그대로.
- 감사 기록은 **덧붙이기만** 하는 기록이라 읽기 전용 원칙의 예외입니다 (실행 기록 `/logs`와 같음). 다른 상태는 바꾸지 않는다.

### 평가 (`my-ops-eval`)

- 케이스마다 `my-ops-ask`를 부르고: `area` 같음 · `refused` 같음(없으면 false) · `numbers` 중 하나가 답에 있음(없으면 통과) · 거절이 아니면 `numbers_ok` true → 넷 다 맞으면 통과. `score` = 통과 / 전체 (4자리). `failed`에는 통과 못 한 케이스 `{"question", "area", "area_ok", "refused_ok", "number_ok", "grounded", "answer"}`.
- (Lab 03 과제 2) 평가 관문: `min_score`(본문, 없으면 0.9)와 비교해 `gate` = `score ≥ min_score`면 `pass`, 아니면 `fail`. `fail`이면 `POST /alerts {"workflow": "ops-eval", "node": "Below?", "severity": "medium", "reason": "eval_below", "score", "min_score", "message"}`. 응답은 평가 결과 그대로 (+ `min_score`, `gate`). 평가는 운영 도우미가 아니라 **도우미를 시험하는** 워크플로우라 알림을 남겨도 됩니다.

## 4. 워크플로우 파일 규칙

```json
{"name": "79 Ops facts (my)", "nodes": [ ... ], "connections": { ... }, "settings": { "executionOrder": "v1" }}
```

- 파일 하나에 워크플로우 하나. 노드 `name`은 영어로, 겹치지 않게. **API 키를 JSON에 쓰지 않는다.**
- **숫자 · 상태는 Code가, 글은 LLM이.** LLM에게 사실을 세게 하거나 상태를 판정하게 하지 않는다.
- 운영 도우미는 **읽기만** 한다: 데이터 API에 POST로 바꾸는 요청(`/dlq/update`, `/releases/...`, `/budget`, `/ops-reset` 등)을 워크플로우에서 부르지 않는다 (`/logs/query`는 읽기, `/audit`은 덧붙이는 기록 · Lab 02 과제 2, 평가의 `/alerts`는 Lab 03 과제 2).

## 5. 검증된 노드 (n8n 2.42.6에서 실행 확인)

### 여러 출처를 차례로 가져오기 → 한 Code에서 모으기
```json
{"name": "Get alerts", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [440, 300],
 "parameters": {"url": "http://data-api:8800/alerts", "options": {}}}
```
- `Get logs`(POST `/logs/query`) → `Get alerts` → `Get DLQ` → `Get quality` → `Get quarantine` → `Get usage` → `Get budget` → `Get release` → `Make facts`(Code)를 **한 줄로** 잇는다. 아이템이 하나씩이라 각 HTTP 노드는 한 번만 부른다.
- `Make facts`에서 출처마다 `$('Get alerts').first().json`처럼 이름으로 읽는다. 웹훅 입력은 `$('Facts webhook').first().json.body`.
- 수업 준비 때 8개 출처를 다 모아도 0.1초 안팎.

### 다른 내 웹훅을 부르기 (답변 · 브리핑 → 사실, 평가 → 답변)
```json
{"name": "Get facts", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [880, 300],
 "parameters": {"method": "POST", "url": "http://localhost:5678/webhook/my-ops-facts", "sendBody": true, "specifyBody": "json",
   "jsonBody": "={{ JSON.stringify({ from: $('Ask webhook').first().json.body?.from ?? '', to: $('Ask webhook').first().json.body?.to ?? '' }) }}", "options": {"timeout": 30000}}}
```
- 평가에서는 케이스를 아이템으로 나눈 뒤(Code) HTTP 노드 하나가 **아이템마다** `my-ops-ask`를 부른다. 결과의 i번째 = 케이스의 i번째.

### 거절은 LLM 앞에서 (IF → Respond)
- `Route`(Code) → `Action?`(IF) → 맞으면 바로 `Respond`(거절). 작업 요청은 LLM에게 보내지 않는다 (73일차 "막는 쪽으로").

### AI Agent + OpenAI chat model (답 글 · 분류 · 요약)
- 67~78일차와 같다. 분류는 지시문에 영역 목록과 "Reply with only the area word", 받은 글에서 영문자만 남겨 목록에 있는지 확인, 없으면 `unknown`.

## 6. 연결 · 7. 표현식

- 72~78일차와 같다. 키에 점이 없는 결과 필드는 테스트에서 `runs.top_failure.count`, `health.dlq`, `actions.0.area`처럼 내려간다.

## 8. 테스트 파일 (`cases/*.json`)

```json
{"webhook": "my-ops-facts", "before": [{"url": "http://localhost:8800/ops-reset", "body": {}}], "cases": [
  {"name": "지난주 실행", "body": {}, "expect": {"equals": {"runs.total": 357, "runs.error_rate": 0.0588}}},
  {"name": "DLQ #3 처리 뒤", "before": [{"url": "http://localhost:8800/dlq/update", "body": {"dlq_id": 3, "remove": true}}], "body": {}, "expect": {"equals": {"dlq.size": 2}}}
]}
```
- 기대 숫자는 운영 아침 상태(`data-api/data/ops-seed.json`)와 실행 기록을 3절 정의대로 계산한 값입니다. **테스트를 통과시키려고 기대 결과나 데이터 파일을 바꾸지 않는다.** 정의가 다르다고 생각되면 사람에게 묻는다.

## 9. 하지 말 것

- `tools/`, `data-api/`(데이터 파일 포함), `requests/`, `reference/`, 이 파일을 고치지 않는다 (요청받은 경우만).
- 워크플로우 안에서 상태를 바꾸는 요청(`/ops-reset`, `/dlq/update`, `/dlq-clear`, `/releases/...` POST, `/budget` POST, 고장 스위치)을 부르지 않는다.
- 답 · 요약에 사실에 없는 숫자 · 짐작한 원인을 넣지 않는다. 운영 밖 질문에 답하지 않는다.
- n8n 컨테이너를 지우거나 `docker compose down`을 하지 않는다. `~/day65-n8n`을 읽거나 고치지 않는다. Credential을 새로 만들지 않는다. `.env`나 API 키를 출력하지 않는다.
