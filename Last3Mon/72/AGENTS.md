# AGENTS.md · n8n 실행 흐름 최적화·안정성 작업 규칙 (72일차 실습 폴더)

이 파일은 **CLI 코딩 에이전트**(Codex, Claude Code, Antigravity 등)가 이 폴더에서 n8n 워크플로우를 만들 때 따르는 규칙입니다. 사람도 읽을 수 있게 썼습니다. 71일차 규칙과 같고, 3절이 오늘 만드는 **헬프데스크 · 상태 점검의 계약**, 5절에 **시간 기록 · 캐시 · 타임아웃 · 재시도 · 오류 출력**이 더해졌습니다.

## 1. 작업 순서 (항상 이 순서)

1. 요청을 읽고, 만들 워크플로우의 **입력 · 노드 순서 · 결과 모양**을 3~5줄로 먼저 정리해 보여 준다. 빠르게 하는 요청이면 **어느 단계를 줄이거나 건너뛰는지**, 안정성 요청이면 **어느 노드가 실패하면 어디로 가는지**도 함께 보여 준다.
2. 워크플로우 JSON을 `my-work/<이름>.json`에 쓴다. 이미 있으면 그 파일을 고친다 (새 파일을 만들지 않는다).
3. `uv run tools/flow.py check my-work/<이름>.json` → 오류(✘)가 없을 때까지 고친다.
4. 끝나면 한국어로 짧게 보고한다: 바꾼 노드, check 결과, 그리고 사람이 실행할 명령 두 줄.
   ```bash
   uv run tools/flow.py push my-work/<이름>.json
   uv run tools/flow.py test cases/<요청에 나온 테스트 파일>.json -v
   ```
5. **push와 test는 사람이 실행해 결과를 확인한다.** 사람이 "네가 push·test까지 해"라고 하면 직접 실행해도 된다 (push는 약 10초, n8n이 잠깐 재시작됨).
6. 사람이 실패 보고서(`runs/*.json`)를 알려 주면 실패한 케이스의 요청·응답을 읽고 원인을 설명한 뒤 고친다. **같은 곳을 3번 고쳐도 실패하면 멈추고** 다른 방법을 제안한다.
7. 문서(`my-work/*.md`)를 써 달라는 요청이면 워크플로우를 만들지 않고 문서만 쓴다.

## 2. 환경 (바꾸지 말 것)

| 항목 | 값 |
| --- | --- |
| n8n | 2.42.6, 65일차 공식 설치 `~/day65-n8n` (Docker 프로젝트 `day65-n8n`, 컨테이너 보통 `day65-n8n-n8n-1`), 브라우저 http://localhost:5678 |
| n8n 켜고 끄기 | `~/aio-01d4-stu/Last3Mon/65/n8n`에서 `docker compose start/stop` (사람이 함, Ollama 컨테이너는 없음) |
| 게시된 웹훅 주소 | 밖에서 `http://localhost:5678/webhook/<path>` |
| OpenAI Credential | id `openAiCourse0001`, name `OpenAI (.env)`, 모델 `gpt-4.1-mini` |
| 다른 Credential | 쓰지 않음 (Ollama 등 없음, LLM은 모두 위 OpenAI Credential) |
| 데이터 API | n8n 안에서 `http://data-api:8800`, 터미널에서 `http://localhost:8800` (**72일차 판** `Last3Mon/72/data-api`: 71일차 + 고장 스위치 + 캐시) |
| 비교 기준 | `reference/baseline-helpdesk.json` (웹훅 `base-helpdesk`, 고치지 않는다) |

### 데이터 API (72일차 판)

| 요청 | 응답 |
| --- | --- |
| `GET /faq?q=<질문>` | `{"query", "results": [{"id": "FAQ-003", "title", "answer", "score"}]}` · 없으면 `results: []` |
| `GET /tickets/<id>?requester=<이름>` | 접수 건 · 없으면 404 · 남의 건이면 403 |
| `GET /cache/<key>` | `{"key", "value", "hits"}` · 없으면 HTTP 404 `{"error": "not cached"}` |
| `POST /cache/<key>` 본문 `{"value": {...}, "ttl": 600}` | `{"stored": true}` (ttl 초가 지나면 사라짐) |
| `POST /cache-clear` · `GET /cache-stats` | 캐시 비우기 · `{"entries", "hits", "misses"}` |
| `GET /admin/fault` · `POST /admin/fault` | 고장 스위치 `{"faq": "ok"|"slow"|"error", "tickets": ..., "slow_seconds": 8}` (연습용, **사람이** `flow.py fault`로 바꿈) |
| `GET /health` | `{"status": "ok"}` (고장 스위치와 상관없음) |

## 3. 오늘 만드는 것의 계약 (요청에 다른 말이 없으면 이대로)

| 무엇 | 파일 · 웹훅 | 입력 (본문) | 결과 |
| --- | --- | --- | --- |
| 헬프데스크 | `my-work/helpdesk.json` · `POST /webhook/my-helpdesk` (처음은 `reference/baseline-helpdesk.json`을 복사) | `question`(필수), `user`, `no_cache`(true면 캐시를 읽지도 쓰지도 않음), `budget_ms`(Lab 01 과제 2, 기본 3000) | `{"route", "category", "answer", "sources", "llm_calls", "cached", "steps", "timings"}` + 실습마다 더하는 칸 (아래) |
| 상태 점검 | `my-work/health.json` · `POST /webhook/my-health` | 없음 | `{"status": "ok"|"degraded"|"down", "checks": {"data_api", "faq", "llm"}, "failed", "seconds"}` |

- `route`: `자동 답변` · `간단 답변`(LLM 없이 데이터 그대로) · `담당자 연결`. `category`: `faq` · `ticket` · `other`.
- `llm_calls`: 이번 요청에서 실제로 부른 LLM 노드 수. `steps`: 지나간 단계 이름 목록(예: `["rule", "faq", "ticket", "answer", "check"]`). 둘 다 **워크플로우가 정해진 값으로** 넣는다 (LLM에게 쓰게 하지 않는다).
- `timings`: 단계별 걸린 시간 ms (`classify_ms`, `data_ms`, `answer_ms`, `review_ms`, ... `total_ms`). 지나가지 않은 단계는 넣지 않는다.
- 빈 질문은 HTTP 400 `{"error": "question is required"}` (LLM을 부르지 않는다).
- **접수 현황(`ticket`)은 캐시하지 않는다** (상태가 바뀐다). 캐시 키는 질문을 앞뒤 공백 제거 · 소문자 · 연속 공백 하나로 바꾼 글자.

실습마다 더하는 칸 (요청에 나올 때만):

| 실습 | 칸 | 뜻 |
| --- | --- | --- |
| Lab 01 과제 1 | `timings.faq_ms` · `timings.ticket_ms`, `slowest_step` | 데이터 조회를 둘로 나눔, `total_ms`를 뺀 가장 큰 단계 이름 (`_ms` 뺀 것) |
| Lab 01 과제 2 | `llm_ms`, `budget_ms`, `over_budget` | LLM 단계(`classify` · `answer` · `review`) 시간의 합 (`timings` **밖**에 둔다: `slowest_step` 계산에 섞이지 않게), 이번 요청의 시간 예산, `total_ms > budget_ms` |
| Lab 02 과제 2 | `cache_by` | 캐시에서 왔으면 `"question"`(질문 키) 또는 `"faq"`(FAQ 번호 키), 아니면 `null` |
| Lab 03 | `reason` | `담당자 연결` · `간단 답변`의 까닭: `data_api_down` · `tickets_down` · `breaker_open` · `llm_down` |

캐시 키 (데이터 API `/cache/<key>`):

| 키 | 값 | ttl | 실습 |
| --- | --- | --- | --- |
| 질문을 고친 글자 (예: `vpn 접속이 자꾸 끊겨요. 어떻게 하나요?`) | `{route, category, answer, sources}` | 600 | Lab 02 예제 2 |
| `faq-<FAQ 번호>` (예: `faq-FAQ-003`) | 같음 | 600 | Lab 02 과제 2 |
| `breaker-faq` | `{"open": true, "since": <ms>}` | 30 | Lab 03 과제 2 (차단기) |

## 4. 워크플로우 파일 규칙

```json
{
  "name": "72 IT helpdesk (my)",
  "nodes": [ ... ],
  "connections": { ... },
  "settings": { "executionOrder": "v1" }
}
```

- 파일 하나에 워크플로우 하나. `id`는 쓰지 않아도 된다 (`push`가 파일 이름으로 정한다).
- 노드 `name`은 영어로, 워크플로우 안에서 겹치지 않게. 노드마다 `type`, `typeVersion`, `position: [x, y]`, `parameters`가 필요하다.
- **API 키를 JSON에 쓰지 않는다.** LLM 노드는 위 Credential id만 쓴다.
- 웹훅은 `POST`, `responseMode: "responseNode"`, 결과는 Respond to Webhook 노드로 보낸다. 갈래마다 Respond 노드를 따로 두어도 된다.
- 요청 본문은 `$json.body.question`처럼 `body` 아래에 있다. 다른 노드 뒤에서는 `$('Question webhook').first().json.body`.

## 5. 검증된 노드 (n8n 2.42.6에서 실행 확인)

### Webhook · If · Respond (71일차와 같음)
```json
{"name": "Question webhook", "type": "n8n-nodes-base.webhook", "typeVersion": 2, "position": [0, 300],
 "parameters": {"httpMethod": "POST", "path": "my-helpdesk", "responseMode": "responseNode", "options": {}}}
```
```json
{"name": "Cached?", "type": "n8n-nodes-base.if", "typeVersion": 2.2, "position": [880, 300],
 "parameters": {"conditions": {"options": {"caseSensitive": true, "leftValue": "", "typeValidation": "loose", "version": 2},
   "conditions": [{"id": "c1", "leftValue": "={{ $json.value !== undefined }}", "rightValue": "",
     "operator": {"type": "boolean", "operation": "true", "singleValue": true}}], "combinator": "and"}, "options": {}}}
```
- If 출력 0번이 true, 1번이 false. 글자 비교: `"operator": {"type": "string", "operation": "notEquals"}`, `"rightValue": "unknown"`.
```json
{"name": "Send result", "type": "n8n-nodes-base.respondToWebhook", "typeVersion": 1.1, "position": [2600, 300],
 "parameters": {"respondWith": "json", "responseBody": "={{ $json }}", "options": {}}}
```

### AI Agent + OpenAI chat model
```json
{"name": "Answer", "type": "@n8n/n8n-nodes-langchain.agent", "typeVersion": 3.1, "position": [1500, 300],
 "parameters": {"promptType": "define", "text": "=질문: {{ $('Question webhook').first().json.body.question }}\n...",
   "options": {"systemMessage": "You are the company IT help desk. ...", "maxIterations": 1}}}
```
```json
{"name": "Answer model", "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi", "typeVersion": 1.2, "position": [1500, 520],
 "parameters": {"model": {"__rl": true, "mode": "id", "value": "gpt-4.1-mini"}, "options": {"temperature": 0}},
 "credentials": {"openAiApi": {"id": "openAiCourse0001", "name": "OpenAI (.env)"}}}
```
- Agent마다 Chat model 노드를 하나씩 둔다. 결과는 `$json.output`(글자). Chat model `options`에 `"timeout": 8000`(ms), `"maxRetries": 0`을 둘 수 있다.

### HTTP Request (데이터 API · 캐시)
```json
{"name": "Search FAQ", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [660, 300],
 "parameters": {"url": "http://data-api:8800/faq", "sendQuery": true,
   "queryParameters": {"parameters": [{"name": "q", "value": "={{ $('Question webhook').first().json.body.question }}"}]},
   "options": {"timeout": 2000}},
 "retryOnFail": true, "maxTries": 2, "waitBetweenTries": 500, "onError": "continueErrorOutput"}
```
```json
{"name": "Store in cache", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [2200, 180],
 "parameters": {"method": "POST", "url": "=http://data-api:8800/cache/{{ encodeURIComponent($('Cache key').first().json.key) }}",
   "sendBody": true, "specifyBody": "json",
   "jsonBody": "={{ JSON.stringify({ value: { route: $json.route, answer: $json.answer }, ttl: 600 }) }}",
   "options": {"response": {"response": {"neverError": true}}}}}
```
- `options.timeout`: 이 시간(ms) 안에 답이 없으면 실패. 없으면 **끝없이 기다린다**.
- 노드 설정 `retryOnFail` · `maxTries` · `waitBetweenTries`(ms): 실패하면 다시. `parameters` 밖, 노드 바로 아래에 쓴다.
- 노드 설정 `"onError": "continueErrorOutput"`: 실패하면 워크플로우를 멈추지 않고 **두 번째 출력**(오류 출력)으로 보낸다. 연결은 `main`의 1번 칸 (아래 6절). `"continueRegularOutput"`은 실패해도 보통 출력으로 (결과에 `error`가 담김).
- `neverError: true`: **404 같은 4xx를** 실패가 아니라 보통 결과로 받는다 (캐시 없음 404를 읽을 때). 이 n8n(2.42.6)에서 실제로 재 보니(10/24) **500은 그래도 실패**로 보고 재시도 · 오류 출력으로 간다. 그리고 `retryOnFail`이 켜져 있으면 **404도 재시도를 다 한 뒤에** 보통 결과로 받는다 (시간을 씀).
- `fullResponse: true`(`neverError`와 함께): 결과가 `{"statusCode", "headers", "body"}`가 되고 **500도 보통 결과**로 바로 온다 (재시도 · 오류 출력 없음). 상태 코드를 보고 **워크플로우가 직접** 나눌 때 쓴다 (Lab 03 예제 3).

  | 설정 (`retryOnFail` 3번, 기다림 1초) | 404 | 500 |
  | --- | --- | --- |
  | 없음 | 재시도 뒤 오류 출력 (2.1초) | 재시도 뒤 오류 출력 (2.1초) |
  | `neverError` | 재시도 뒤 **보통** 출력 (2.2초) | 재시도 뒤 오류 출력 (2.2초) |
  | `neverError` + `fullResponse` | 바로 보통 출력, `statusCode: 404` (0.1초) | 바로 보통 출력, `statusCode: 500` (0.1초) |
- Agent 노드에도 `"onError": "continueErrorOutput"`을 둘 수 있다 (LLM이 실패하면 오류 출력으로).

### Code (시간 기록 · 결과 모양)
```json
{"name": "Start clock", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [440, 300],
 "parameters": {"jsCode": "return [{ json: { t: Date.now() } }];"}}
```
```json
{"name": "After answer", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [1720, 300],
 "parameters": {"jsCode": "return [{ json: { ...$json, t: Date.now() } }];"}}
```
- 단계가 끝날 때마다 `Date.now()`를 남기고, 마지막 Code에서 앞 기록과의 차이를 `timings`로 만든다.
- 지나가지 않았을 수 있는 노드는 `$('노드').isExecuted`(true/false)로 먼저 확인한 뒤 읽는다. `steps`, `llm_calls`도 이것으로 센다.
- 반드시 `[{ json: {...} }]` 배열을 돌려준다. Code 노드 안에는 `URL` 클래스가 없다.

### HTTP Request (상태 코드를 직접 보기, Lab 03 예제 3)
```json
{"name": "Get ticket", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [880, 300],
 "parameters": {"url": "=http://data-api:8800/tickets/...", "sendQuery": true, "queryParameters": {"parameters": [{"name": "requester", "value": "={{ ... }}"}]},
   "options": {"timeout": 2000, "response": {"response": {"fullResponse": true, "neverError": true}}}},
 "retryOnFail": true, "maxTries": 2, "onError": "continueErrorOutput"}
```
```json
{"name": "Ticket check", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [980, 460],
 "parameters": {"jsCode": "const status = Number($json.statusCode ?? 200);\nreturn [{ json: { ticket: status >= 500 ? {} : ($json.body ?? {}), ticket_status: status } }];"}}
```
- 결과의 접수 건은 `$json.body`에 있다. 뒤에서 `$('Get ticket').first().json`을 읽던 곳은 `$('Ticket check').first().json.ticket`으로 바꾼다.
- `timeout`(느림)은 여전히 실패로 오류 출력에 간다.

### Edit Fields (Set) — 정해진 답
```json
{"name": "Data down", "type": "n8n-nodes-base.set", "typeVersion": 3.4, "position": [1500, 820],
 "parameters": {"assignments": {"assignments": [
   {"id": "d1", "name": "route", "value": "담당자 연결", "type": "string"},
   {"id": "d2", "name": "answer", "value": "사내 데이터 시스템이 응답하지 않아 담당자에게 연결합니다.", "type": "string"}]}, "options": {}}}
```

## 6. 연결 (`connections`)

```json
{
  "Has question?": {"main": [[{"node": "Start clock", "type": "main", "index": 0}], [{"node": "Reject empty", "type": "main", "index": 0}]]},
  "Search FAQ": {"main": [[{"node": "Get ticket", "type": "main", "index": 0}], [{"node": "Data down", "type": "main", "index": 0}]]},
  "Answer model": {"ai_languageModel": [[{"node": "Answer", "type": "ai_languageModel", "index": 0}]]}
}
```
- 키는 **보내는 노드 이름**, 안의 `node`는 받는 노드 이름. If의 `main`은 `[ [true 쪽], [false 쪽] ]`.
- `onError: continueErrorOutput`인 노드의 `main`도 `[ [성공 쪽], [실패 쪽] ]`.
- 두 갈래가 한 노드로 다시 들어와도 된다 (한 번에 한 갈래만 지나가므로). 다시 모인 노드에서는 `$json`으로 앞 결과를 읽는다.

## 7. 표현식 주의

- 표현식은 `=`로 시작한다: `"={{ $json.body.question }}"`. `=`가 없으면 그냥 글자로 남는다.
- `{{ }}` 안에서 객체를 만들 때 `}}`가 붙지 않게 띄어 쓴다: `"={{ JSON.stringify({ value: $json }) }}"`
- URL에 질문 같은 글자를 넣을 때는 `encodeURIComponent(...)`.

## 8. 테스트 파일 (`cases/*.json`)

```json
{
  "webhook": "my-helpdesk",
  "before": [{"url": "http://localhost:8800/cache-clear", "body": {}}],
  "after": [{"url": "http://localhost:8800/admin/fault", "body": {"faq": "ok", "tickets": "ok"}}],
  "cases": [
    {"name": "같은 질문", "request": "requests/faq-vpn-again.json",
     "expect": {"equals": {"cached": true, "llm_calls": 0}, "contains": {"answer": ["인증서"]}, "max_seconds": 1}},
    {"name": "FAQ 오류", "before": [{"url": "http://localhost:8800/admin/fault", "body": {"faq": "error"}}],
     "body": {"question": "비밀번호를 잊어버렸어요", "no_cache": true}, "expect": {"equals": {"route": "담당자 연결"}}},
    {"name": "LLM 멈춤", "before": [{"llm": "down"}], "after": [{"llm": "up"}], "request": "requests/faq-vpn-nocache.json",
     "expect": {"equals": {"route": "간단 답변"}}}
  ]
}
```
- `before` · `after`: 테스트 파일 전체 또는 케이스 하나의 앞뒤에 한 번. `{"webhook": ...}`(n8n), `{"url": ...}`(데이터 API에 POST), `{"llm": "down"|"up"}`(OpenAI Credential을 일부러 망가뜨렸다 되돌림). `after`는 실패해도 반드시 실행된다.
- `max_seconds`: 응답이 이 시간 안에 와야 함. `equals` · `contains` · `not_contains` · `status`는 71일차와 같다. 필드 이름은 점으로 내려간다 (`checks.faq`).
- `uv run tools/flow.py test <파일> -v`: `-v`(`--verbose`)는 케이스마다 보낸 요청 JSON과 받은 응답 JSON을 화면에 보여 준다 (보고서 `runs/*.json`에도 같은 것이 남음). `call ... -v`도 보낸 요청 JSON을 응답 위에 함께 보여 준다. **모든 명령이 `-v`를 받는다**: `bench -v`는 응답 JSON마다 · 정렬한 시간 · 단계별 평균 ms, `check -v` · `push -v`는 노드 · 연결 목록과 실행한 docker 명령, `fault -v` · `doctor -v`는 보낸 요청 · 받은 응답 (API 키는 `sk-***`로 가림).
- **테스트를 통과시키려고 테스트 파일의 기대 결과를 바꾸지 않는다.** 기대 결과가 틀렸다고 생각되면 사람에게 묻는다.

## 9. 하지 말 것

- `tools/`, `data-api/`, `requests/`, `reference/`, 이 파일(`AGENTS.md`)을 고치지 않는다 (요청받은 경우만).
- 고장 스위치(`/admin/fault`)나 `flow.py llm`을 워크플로우 안에서 부르지 않는다 (연습은 사람이 한다).
- 빠르게 하려고 **답의 내용 검사(테스트의 `contains`)를 없애지 않는다.** 빨라졌으면 품질이 그대로인지 원래 테스트로 확인한다.
- n8n 컨테이너를 지우거나 `docker compose down`을 하지 않는다. `~/day65-n8n`(n8n 설치·비밀값)을 읽거나 고치지 않는다. Credential을 새로 만들지 않는다.
- `.env`나 API 키를 읽어서 출력하지 않는다.
