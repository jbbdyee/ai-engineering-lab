# AGENTS.md · n8n 에러 처리·예외 대응 작업 규칙 (76일차 실습 폴더)

이 파일은 **CLI 코딩 에이전트**(Codex, Claude Code, Antigravity 등)가 이 폴더에서 n8n 워크플로우를 만들 때 따르는 규칙입니다. 사람도 읽을 수 있게 썼습니다. 75일차 규칙과 같고, 3절이 오늘 만드는 **문의 일괄 접수 · 에러 처리 · 재처리의 계약**, 5절에 **항목마다 실패 · 재시도 · 멱등 키 · DLQ · Error Workflow** 노드가 더해졌습니다.

## 1. 작업 순서 (항상 이 순서)

1. 요청을 읽고, 만들 워크플로우의 **입력 · 노드 순서 · 결과 모양**을 3~5줄로 먼저 정리해 보여 준다. 에러 처리 요청이면 **어떤 실패가 어디로 가는지(거절 · 재시도 · DLQ · 알림)** 를 표로 함께 보여 준다.
2. 워크플로우 JSON을 `my-work/<이름>.json`에 쓴다. 이미 있으면 그 파일을 고친다 (새 파일을 만들지 않는다).
3. `uv run tools/flow.py check my-work/<이름>.json` → 오류(✘)가 없을 때까지 고친다.
4. 끝나면 한국어로 짧게 보고한다: 바꾼 노드, check 결과, 그리고 사람이 실행할 명령 두 줄.
   ```bash
   uv run tools/flow.py push my-work/<이름>.json
   uv run tools/flow.py test cases/<요청에 나온 테스트 파일>.json
   ```
5. **push와 test는 사람이 실행해 결과를 확인한다.** 사람이 "네가 push·test까지 해"라고 하면 직접 실행해도 된다 (push는 약 10초, n8n이 잠깐 재시작됨).
6. 사람이 실패 보고서(`runs/*.json`)를 알려 주면 실패한 케이스의 요청·응답을 읽고 원인을 설명한 뒤 고친다. **같은 곳을 3번 고쳐도 실패하면 멈추고** 다른 방법을 제안한다.
7. 문서(`my-work/*.md`)를 써 달라는 요청이면 워크플로우를 만들지 않고 문서만 쓴다.

## 2. 환경 (바꾸지 말 것)

| 항목 | 값 |
| --- | --- |
| n8n | 2.42.6, 65일차 공식 설치 `~/day65-n8n` (Docker 프로젝트 `day65-n8n`, 컨테이너 보통 `day65-n8n-n8n-1`), 브라우저 http://localhost:5678 |
| n8n 켜고 끄기 | `~/aio-01d4-stu/Last3Mon/65/n8n`에서 `docker compose start/stop` (사람이 함, Ollama 컨테이너는 없음) |
| 게시된 웹훅 주소 | 밖에서 `http://localhost:5678/webhook/<path>`, **n8n 안에서도** `http://localhost:5678/webhook/<path>` |
| OpenAI Credential | id `openAiCourse0001`, name `OpenAI (.env)`, 모델 `gpt-4.1-mini` (분류). `gpt-4.1-nano`는 OpenAI가 받지 않음 |
| 다른 Credential | 쓰지 않음 (Ollama 등 없음) |
| 데이터 API | n8n 안에서 `http://data-api:8800`, 터미널에서 `http://localhost:8800` (**76일차 판** `Last3Mon/76/data-api`: 75일차 + 접수 건 만들기 · DLQ · 알림) |
| 비교 기준 · 제공 | `reference/baseline-intake.json` (`base-intake`), `reference/nightly-report.json` (`nightly-report`, 일부러 버그가 있음). 고치지 않는다 |

### 데이터 API (76일차 판)

| 요청 | 응답 |
| --- | --- |
| `POST /tickets` 본문 `{"key", "title", "requester", "category", "priority"}` | 201 `{"ticket_id": "T-2001", "duplicate": false}` · **같은 `key`면** 200 `{"ticket_id"(처음 것), "duplicate": true}` · `key` · `title`이 없으면 400 · 고장 스위치 `tickets`를 따른다 |
| `GET /tickets-created` (`POST /tickets-created/list`) | `{"count", "tickets": [...]}` |
| `POST /dlq` 본문 `{"items": [{"item": <원래 요청>, "reason", "workflow"}]}` | `{"stored", "size"}` · **같은 `item.id`면 새 줄 없이 `attempts` +1** |
| `GET /dlq` (`POST /dlq/list`) | `{"size", "parked", "items": [{"dlq_id", "item", "reason", "attempts", "parked"}]}` · 고장 스위치 `dlq`를 따른다 (`POST /dlq`가 500) |
| `POST /dlq/update` | `{"dlq_id", "remove": true}` 또는 `{"dlq_id", "parked": true, "reason"}` |
| `POST /alerts` 본문 `{"workflow", "node", "message", "severity", "reason", ...}` | `{"stored", "count"}` |
| `GET /alerts` · `POST /alerts/list` · `POST /alerts/latest` | 모든 알림 · **거르기** 본문 `{"workflow", "reason", "severity", "within": 초}` (예: `{"workflow": "intake", "reason": "dlq", "within": 600}`는 10분 안의 것만) · 가장 최근 알림 |
| `POST /admin/fault` | `{"tickets": "ok" \| "slow" \| "error" \| "flaky", "dlq": ...}` — `flaky`: 접수 건 만들기에서 **키마다 첫 번째 시도만 실패**, `slow`: 8초 기다린 뒤 **그래도 접수 건을 만든다**(부른 쪽이 포기했어도) (**사람이** `flow.py fault`로) |
| `POST /tickets-reset` · `/dlq-clear` · `/alerts-clear` | 비우기 (`flow.py ops --reset`이 한 번에) |

## 3. 오늘 만드는 것의 계약 (요청에 다른 말이 없으면 이대로)

| 무엇 | 파일 · 웹훅 | 입력 (본문) | 결과 |
| --- | --- | --- | --- |
| 문의 일괄 접수 | `my-work/intake.json` · `POST /webhook/my-intake` | `{"requests": [{"id": "R-101", "user": "이준호", "text": "..."}]}` | HTTP 200 `{"total", "created", "failed", "rejected", "duplicates", "unclassified", "results": [{"id", "status": "created" \| "failed" \| "rejected", "ticket_id", "duplicate", "category", "priority", "reason"}]}` |
| 에러 처리기 | `my-work/error-handler.json`, 파일 안에 **`"id": "errHandler76001"`**, Error Trigger로 시작 | (n8n이 부름) | `POST /alerts` `{"workflow", "workflow_id", "node", "message", "execution_id", "severity": "critical", "reason": "unexpected"}` |
| 재처리 | `my-work/replay.json` · `POST /webhook/my-replay` | `{"max_attempts": 3}`(선택) | `{"replayed", "ok", "still_failed", "parked", "duplicates"}` |
| 운영 상태 (Lab 03 과제 2) | `my-work/ops-status.json` · `POST /webhook/my-ops-status` | `{}` | `{"status": "ok" \| "warn" \| "critical", "dlq", "parked", "created", "alerts": {"critical", "high"}, "reasons": [...]}` |

- `requests`가 목록이 아니면 HTTP 400 `{"error": "requests must be a list"}`. (Lab 01 과제 2) 10건이 넘으면 HTTP 400 `{"error": "too many requests (max 10)"}`, 같은 요청 안에 같은 `id`가 또 있으면 두 번째부터 거절 `duplicate id in this request`.
- 항목 하나가 잘못돼도(**거절** `rejected`: id · user · text 없음) 나머지는 처리한다. 결과는 늘 HTTP 200 (부분 성공).
- 접수 건을 만들 때 **`key` = 요청의 `id`** (멱등 키). 같은 요청을 다시 보내도 접수 건이 두 번 생기지 않는다.
- 데이터 API 실패는 timeout 3초 · 재시도 3번 뒤 **실패** `failed`로 표시하고 원래 요청을 DLQ에 넣는다.
- LLM 분류가 실패하면 `category: 미분류`, `priority: 보통`으로 접수한다 (멈추지 않는다).
- (Lab 02 과제 1) 처리한 실패(DLQ로 간 것)가 1건 이상이면 `POST /alerts` `{"workflow": "intake", "severity": "high", "reason": "dlq", "count"}`. DLQ에 넣지 **못했으면**(`stored`가 없음) `{"severity": "critical", "reason": "dlq_down", "count", "message"(잃을 뻔한 id들)}`. 결과에 `dlq_saved`(true/false, 실패가 있을 때)와 `alert`(`sent` · `none`).
- (Lab 02 과제 2) 같은 `reason`의 high 알림이 10분 안에 이미 있으면 보내지 않고 `alert: "suppressed"`. critical은 늘 보낸다.
- (Lab 03 과제 2) 운영 상태: parked가 있거나 10분 안 critical 알림이 있으면 `critical`, parked가 아닌 DLQ가 있거나 10분 안 high 알림이 있으면 `warn`, 아니면 `ok`. `reasons`에 까닭을 한국어로.
- 접수 워크플로우와 `nightly-report`의 설정 `settings.errorWorkflow`는 `errHandler76001`.
- 재처리: DLQ에서 `parked`가 아닌 것을 `my-intake`로 하나씩 다시 보내고, 성공하면 DLQ에서 지운다. `attempts`가 `max_attempts` 이상이면 다시 보내지 않고 `parked: true` + 알림 `{"severity": "high", "reason": "parked"}`.

## 4. 워크플로우 파일 규칙

```json
{
  "name": "76 Intake (my)",
  "nodes": [ ... ],
  "connections": { ... },
  "settings": { "executionOrder": "v1", "errorWorkflow": "errHandler76001" }
}
```

- 파일 하나에 워크플로우 하나. 노드 `name`은 영어로, 겹치지 않게. 노드마다 `type`, `typeVersion`, `position`, `parameters`.
- `id`를 쓰지 않으면 `push`가 파일 이름으로 정한다. **에러 처리기는 다른 워크플로우가 id로 부르므로** 파일 맨 위에 `"id": "errHandler76001"`을 쓴다 (70일차 모듈과 같음).
- **API 키를 JSON에 쓰지 않는다.** LLM 노드는 위 Credential id만 쓴다.

## 5. 검증된 노드 (n8n 2.42.6에서 실행 확인)

### 항목마다 확인 (Code → If) · 두 갈래 모으기 (Merge)
```json
{"name": "Check items", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [440, 300],
 "parameters": {"jsCode": "const requests = $('Intake webhook').first().json.body.requests;\nreturn requests.map((r, index) => ({ json: { index, valid: ..., reason: ..., id: r.id, user: r.user, text: r.text } }));"}}
```
```json
{"name": "Collect", "type": "n8n-nodes-base.merge", "typeVersion": 3, "position": [1760, 300], "parameters": {"numberInputs": 2}}
```
- 처리한 갈래 → `Collect` 입력 0번, 거절한 갈래 → 입력 1번 (`"index": 1`). 한쪽이 비어도 모은다.

### AI Agent (항목마다 분류) — 실패해도 계속
```json
{"name": "Classify", "type": "@n8n/n8n-nodes-langchain.agent", "typeVersion": 3.1, "position": [880, 200],
 "parameters": {"promptType": "define", "text": "={{ $json.text }}", "options": {"systemMessage": "... Return only JSON ...", "maxIterations": 1}},
 "onError": "continueRegularOutput"}
```
- Agent는 들어온 항목마다 한 번씩 돈다. `continueRegularOutput`이면 실패한 항목은 `output` 대신 `error`를 가진 채 다음으로 간다.

### 접수 건 만들기 (HTTP) — 재시도 · 멱등 키 · 실패해도 계속
```json
{"name": "Create ticket", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [1320, 200],
 "parameters": {"method": "POST", "url": "http://data-api:8800/tickets", "sendBody": true, "specifyBody": "json",
   "jsonBody": "={{ JSON.stringify({ key: $json.id, title: $json.text, requester: $json.user, category: $json.category, priority: $json.priority }) }}",
   "options": {"timeout": 3000}},
 "retryOnFail": true, "maxTries": 3, "waitBetweenTries": 300, "onError": "continueRegularOutput"}
```
- **노드의 재시도는 노드에 들어온 항목을 모두 다시 보낸다.** 그래서 멱등 키(`key`)가 없으면 이미 만든 접수 건이 또 생긴다.
- `continueRegularOutput`: 재시도 뒤에도 실패한 항목은 `{"error": {...}}`를 가진 채 다음 노드로. 다음 Code에서 앞 노드 항목과 같은 순서로 맞춰 `created` / `failed`를 정한다.

### Error Workflow (에러 처리기)
```json
{"name": "On error", "type": "n8n-nodes-base.errorTrigger", "typeVersion": 1, "position": [0, 300], "parameters": {}}
```
- 다른 워크플로우가 **처리하지 못한 오류로 멈추면** n8n이 이 워크플로우를 부른다. 받는 값: `$json.workflow.name`, `$json.workflow.id`, `$json.execution.id`, `$json.execution.lastNodeExecuted`, `$json.execution.error.message`.
- 부르는 쪽 설정: `"settings": {"executionOrder": "v1", "errorWorkflow": "errHandler76001"}`. 에러 처리기도 push(게시)해야 한다.
- 웹훅 응답(500)이 나간 **뒤에** 돈다 — 알림은 1~3초 늦게 생긴다.

### DLQ · 알림 (HTTP POST)
```json
{"name": "Send to DLQ", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [2420, 140],
 "parameters": {"method": "POST", "url": "http://data-api:8800/dlq", "sendBody": true, "specifyBody": "json",
   "jsonBody": "={{ JSON.stringify({ items: ... }) }}", "options": {"response": {"response": {"neverError": true}}}}}
```

### 내 웹훅 다시 부르기 (재처리, 항목마다)
```json
{"name": "Run intake again", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [1100, 200],
 "parameters": {"method": "POST", "url": "http://localhost:5678/webhook/my-intake", "sendBody": true, "specifyBody": "json",
   "jsonBody": "={{ JSON.stringify({ requests: [$json.item] }) }}", "options": {"response": {"response": {"neverError": true}}, "timeout": 60000}}}
```

### 그 밖 (72~75일차와 같음)
- Webhook · If · Code · Respond to Webhook. 비어 있을 수 있는 결과에는 노드에 `"alwaysOutputData": true`.

## 6. 연결 (`connections`)

```json
{
  "Valid?": {"main": [[{"node": "Classify", "type": "main", "index": 0}], [{"node": "Mark rejected", "type": "main", "index": 0}]]},
  "Mark results": {"main": [[{"node": "Collect", "type": "main", "index": 0}]]},
  "Mark rejected": {"main": [[{"node": "Collect", "type": "main", "index": 1}]]}
}
```

## 7. 표현식 주의

- 표현식은 `=`로 시작한다. 이번 실행 번호는 `$execution.id`, 항목 번호는 `$itemIndex`.
- Code 노드의 `throw new Error('...')`는 워크플로우를 멈춘다 (Error Workflow가 받음). 처리할 수 있는 실패는 던지지 말고 결과로.

## 8. 테스트 파일 (`cases/*.json`)

```json
{
  "webhook": "my-intake",
  "before": [{"url": "http://localhost:8800/tickets-reset", "body": {}}],
  "cases": [
    {"name": "API 오류", "before": [{"url": "http://localhost:8800/admin/fault", "body": {"tickets": "error"}}],
     "request": "requests/batch-two.json", "expect": {"equals": {"failed": 2}}},
    {"name": "DLQ 확인", "url": "http://localhost:8800/dlq/list", "body": {}, "expect": {"equals": {"size": 2}}},
    {"name": "알림 확인", "before": [{"sleep": 3}], "url": "http://localhost:8800/alerts/latest", "body": {}, "expect": {"equals": {"severity": "critical"}}},
    {"name": "다른 웹훅", "webhook": "my-replay", "body": {}, "expect": {"equals": {"ok": 2}}}
  ]
}
```
- `url` 케이스는 그 주소에 **POST** 합니다. 읽기만 할 때는 `/dlq/list`, `/alerts/list`, `/alerts/latest`, `/tickets-created/list`.
- `{"sleep": 3}`: 기다리기 (Error Workflow가 늦게 돌 때).
- **테스트를 통과시키려고 테스트 파일의 기대 결과를 바꾸지 않는다.** 기대 결과가 틀렸다고 생각되면 사람에게 묻는다.

## 9. 하지 말 것

- `tools/`, `data-api/`, `requests/`, `reference/`, 이 파일(`AGENTS.md`)을 고치지 않는다 (요청받은 경우만). `nightly-report`의 버그를 고쳐서 테스트를 통과시키지 않는다 (오늘은 일부러 실패시키는 연습).
- 워크플로우 안에서 고장 스위치 · `*-reset` · `*-clear`를 부르지 않는다.
- 실패를 숨기지 않는다: 실패한 항목을 결과에서 빼거나 성공으로 바꾸지 않는다.
- n8n 컨테이너를 지우거나 `docker compose down`을 하지 않는다. `~/day65-n8n`(n8n 설치·비밀값)을 읽거나 고치지 않는다. Credential을 새로 만들지 않는다.
- `.env`나 API 키를 읽어서 출력하지 않는다.
