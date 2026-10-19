# AGENTS.md · n8n 워크플로우 작업 규칙 (67일차 실습 폴더)

이 파일은 **CLI 코딩 에이전트**(Codex, Claude Code, Antigravity 등)가 이 폴더에서 n8n 워크플로우를 만들 때 따르는 규칙입니다. 사람도 읽을 수 있게 썼습니다.

## 1. 작업 순서 (항상 이 순서)

1. 요청을 읽고, 만들 워크플로우의 **입력 · 노드 순서 · 결과 모양**을 3~5줄로 먼저 정리해 보여 준다.
2. 워크플로우 JSON을 `my-work/<이름>.json`에 쓴다. 이미 있으면 그 파일을 고친다 (새 파일을 만들지 않는다).
3. `uv run tools/flow.py check my-work/<이름>.json` → 오류(✘)가 없을 때까지 고친다.
4. 끝나면 한국어로 짧게 보고한다: 바꾼 노드, check 결과, 그리고 사람이 실행할 명령 두 줄.
   ```bash
   uv run tools/flow.py push my-work/<이름>.json
   uv run tools/flow.py test cases/<요청에 나온 테스트 파일>.json
   ```
5. **push와 test는 사람이 실행해 결과를 확인한다.** 사람이 "네가 push·test까지 해"라고 하면 직접 실행해도 된다 (push는 약 10초, n8n이 잠깐 재시작됨).
6. 사람이 실패 보고서(`runs/*.json`)를 알려 주면 실패한 케이스의 요청·응답을 읽고 원인을 설명한 뒤 고친다. **같은 곳을 3번 고쳐도 실패하면 멈추고** 다른 방법을 제안한다.

## 2. 환경 (바꾸지 말 것)

| 항목 | 값 |
| --- | --- |
| n8n | 2.42.6, 65일차 공식 설치 `~/day65-n8n` (Docker 프로젝트 `day65-n8n`, 컨테이너 보통 `day65-n8n-n8n-1`), 브라우저 http://localhost:5678 |
| n8n 켜고 끄기 | `~/aio-01d4-stu/Last3Mon/65/n8n`에서 `docker compose start/stop` (사람이 함, Ollama 컨테이너는 없음) |
| 게시된 웹훅 주소 | `http://localhost:5678/webhook/<path>` (`flow.py push`가 게시까지 한다) |
| OpenAI Credential | id `openAiCourse0001`, name `OpenAI (.env)`, 모델 `gpt-4.1-mini` |
| 다른 Credential | 쓰지 않음 (Ollama 등 없음, LLM은 모두 위 OpenAI Credential) |
| 데이터 API (n8n 안에서) | `http://data-api:8800` (n8n 노드에서는 반드시 이 주소. `localhost` 아님) |
| 데이터 API (터미널에서) | `http://localhost:8800` |

### 데이터 API

| 요청 | 응답 |
| --- | --- |
| `GET /faq?q=<키워드>` | `{"query": "...", "results": [{"id": "FAQ-003", "title": "...", "answer": "...", "score": 1}]}` · 없으면 `results: []` |
| `GET /tickets/<id>` | `{"ticket_id": "T-1002", "title": "...", "requester": "박서연", "status": "처리 중", "assignee": "...", "updated": "...", "note": "..."}` · 없으면 HTTP 404 `{"error": "ticket not found"}` |
| `GET /tickets/<id>?requester=<이름>` | 위와 같음. 다른 사람의 접수 건이면 HTTP 403 `{"error": "not your ticket"}` |

데이터: FAQ-001~006 (비밀번호, 계정 잠김, VPN, 프린터, 메일함, 소프트웨어 설치), 접수 건 T-1001~T-1004.

## 3. 워크플로우 파일 규칙

```json
{
  "name": "67 IT help agent (my)",
  "nodes": [ ... ],
  "connections": { ... },
  "settings": { "executionOrder": "v1" }
}
```

- 파일 하나에 워크플로우 하나. `id`는 쓰지 않아도 된다 (`push`가 파일 이름으로 정한다).
- 노드 `name`은 영어로, 워크플로우 안에서 겹치지 않게. 노드마다 `type`, `typeVersion`, `position: [x, y]`, `parameters`가 필요하다.
- **API 키를 JSON에 쓰지 않는다.** LLM 노드는 위 Credential id만 쓴다.
- 웹훅은 `POST`, `responseMode: "responseNode"`, 결과는 Respond to Webhook 노드로 보낸다.
- 요청 본문은 `$json.body.question`, `$json.body.user`처럼 `body` 아래에 있다.

## 4. 검증된 노드 (n8n 2.42.6에서 실행 확인)

아래 `type`/`typeVersion`을 그대로 쓴다. 다른 노드가 필요하면 써도 되지만 `flow.py check`가 이 n8n에 있는지 확인한다.

### Webhook
```json
{"name": "IT question webhook", "type": "n8n-nodes-base.webhook", "typeVersion": 2, "position": [0, 300],
 "parameters": {"httpMethod": "POST", "path": "my-it-agent", "responseMode": "responseNode", "options": {}}}
```

### AI Agent + OpenAI chat model
```json
{"name": "IT help agent", "type": "@n8n/n8n-nodes-langchain.agent", "typeVersion": 3.1, "position": [260, 300],
 "parameters": {"promptType": "define", "text": "={{ $('IT question webhook').first().json.body.question }}",
   "options": {"systemMessage": "You are the company IT help agent. ...", "maxIterations": 5, "returnIntermediateSteps": true}}}
```
```json
{"name": "OpenAI chat model", "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi", "typeVersion": 1.2, "position": [160, 520],
 "parameters": {"model": {"__rl": true, "mode": "id", "value": "gpt-4.1-mini"}, "options": {"temperature": 0}},
 "credentials": {"openAiApi": {"id": "openAiCourse0001", "name": "OpenAI (.env)"}}}
```
- Agent의 결과: `$json.output`(답 글자). `returnIntermediateSteps: true`면 `$json.intermediateSteps`에 Tool 호출 기록이 남는다: `[{ "action": { "tool": "Search_FAQ", "toolInput": {...} }, "observation": "<Tool 응답 글자>" }]`
- Tool 이름은 노드 이름의 빈칸이 `_`로 바뀐 것이다 (`Search FAQ` → `Search_FAQ`). systemMessage에서도 이 이름으로 부른다.

### HTTP Request Tool (Agent가 부르는 데이터 조회)
```json
{"name": "Search FAQ", "type": "n8n-nodes-base.httpRequestTool", "typeVersion": 4.2, "position": [360, 520],
 "parameters": {"toolDescription": "Search the company IT FAQ ... Input: keywords of the question in Korean.",
   "url": "http://data-api:8800/faq", "sendQuery": true,
   "queryParameters": {"parameters": [{"name": "q", "value": "={{ $fromAI('query', 'Keywords of the IT question in Korean', 'string') }}"}]},
   "options": {}}}
```
```json
{"name": "Get ticket", "type": "n8n-nodes-base.httpRequestTool", "typeVersion": 4.2, "position": [540, 520],
 "parameters": {"toolDescription": "Look up the status of an IT request ticket ... Input: the ticket id.",
   "url": "=http://data-api:8800/tickets/{{ $fromAI('ticket_id', 'Ticket id such as T-1002', 'string') }}",
   "options": {"response": {"response": {"neverError": true}}}}}
```
- `$fromAI('이름', '설명', 'string')`: 그 값을 **LLM이 정해서** 넣는다.
- **LLM이 정하면 안 되는 값**(요청한 사람, 권한, 금액 등)은 `$fromAI`를 쓰지 않고 표현식으로 웹훅 입력에서 가져온다. 예: `"={{ $('IT question webhook').first().json.body.user }}"`
- 404·403도 Agent가 읽을 수 있게 `neverError: true`를 둔다.

### If
```json
{"name": "Has question?", "type": "n8n-nodes-base.if", "typeVersion": 2.2, "position": [200, 300],
 "parameters": {"conditions": {"options": {"caseSensitive": true, "leftValue": "", "typeValidation": "strict", "version": 2},
   "conditions": [{"id": "c1", "leftValue": "={{ $json.body.question }}", "rightValue": "",
     "operator": {"type": "string", "operation": "notEmpty", "singleValue": true}}], "combinator": "and"}, "options": {}}}
```
- 출력 0번이 true, 1번이 false. Boolean 검사는 `"operator": {"type": "boolean", "operation": "true", "singleValue": true}`.

### Code (JavaScript)
```json
{"name": "Check answer", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [720, 200],
 "parameters": {"jsCode": "const answer = String($json.output ?? '').trim();\nreturn [{ json: { answer } }];"}}
```
- 반드시 `[{ json: {...} }]` 배열을 돌려준다. 앞 노드는 `$('노드 이름').first().json`으로 읽는다.

### Edit Fields (Set)
```json
{"name": "Auto answer", "type": "n8n-nodes-base.set", "typeVersion": 3.4, "position": [1160, 100],
 "parameters": {"assignments": {"assignments": [
   {"id": "a1", "name": "route", "value": "자동 답변", "type": "string"},
   {"id": "a2", "name": "answer", "value": "={{ $json.answer }}", "type": "string"},
   {"id": "a3", "name": "tools_used", "value": "={{ $json.tools_used }}", "type": "array"}]}, "options": {}}}
```

### Respond to Webhook
```json
{"name": "Send result", "type": "n8n-nodes-base.respondToWebhook", "typeVersion": 1.1, "position": [1380, 200],
 "parameters": {"respondWith": "json", "responseBody": "={{ $json }}", "options": {}}}
```
- 오류 응답: `"responseBody": "{ \"error\": \"question is required\" }"`, `"options": {"responseCode": 400}`

## 5. 연결 (`connections`)

```json
{
  "IT question webhook": {"main": [[{"node": "IT help agent", "type": "main", "index": 0}]]},
  "Has question?": {"main": [[{"node": "IT help agent", "type": "main", "index": 0}], [{"node": "Reject empty", "type": "main", "index": 0}]]},
  "OpenAI chat model": {"ai_languageModel": [[{"node": "IT help agent", "type": "ai_languageModel", "index": 0}]]},
  "Search FAQ": {"ai_tool": [[{"node": "IT help agent", "type": "ai_tool", "index": 0}]]}
}
```
- 키는 **보내는 노드 이름**, 안의 `node`는 받는 노드 이름.
- If의 `main`은 `[ [true 쪽], [false 쪽] ]` 두 칸.
- Chat model은 `ai_languageModel`, Tool은 `ai_tool`로 **Agent에** 연결한다 (`main` 아님).

## 6. 표현식 주의

- 표현식은 `=`로 시작한다: `"={{ $json.body.question }}"`. `=`가 없으면 그냥 글자로 남는다.
- `{{ }}` 안에서 객체를 만들 때 `}}`가 붙지 않게 띄어 쓴다: `"={{ { answer: $json.output } }}"`
- Agent 뒤 노드에서 웹훅 입력은 `$('IT question webhook').first().json.body`로 읽는다 (`$json`은 바로 앞 노드 결과).

## 7. 테스트 파일 (`cases/*.json`)

```json
{
  "webhook": "my-it-agent",
  "cases": [
    {"name": "VPN FAQ", "request": "requests/faq-vpn.json",
     "expect": {"status": 200, "equals": {"route": "자동 답변"}, "contains": {"answer": ["인증서"]},
                "not_contains": {"answer": ["정우성"]}}},
    {"name": "직접 쓴 요청", "body": {"question": "...", "user": "이준호"}, "expect": {"status": 400}}
  ]
}
```
- `equals`: 값이 같아야 함 · `contains`: 목록 중 **하나라도** 들어 있어야 함 · `not_contains`: 하나도 없어야 함 · `status`: HTTP 코드(기본 200)
- `uv run tools/flow.py test <파일> --repeat 3`: LLM 답은 매번 조금씩 다르므로 3번 이상 돌려 본다.
- **테스트를 통과시키려고 테스트 파일의 기대 결과를 바꾸지 않는다.** 기대 결과가 틀렸다고 생각되면 사람에게 묻는다.

## 8. 하지 말 것

- `tools/`, `data-api/`, `requests/`, 이 파일(`AGENTS.md`)을 고치지 않는다 (요청받은 경우만).
- n8n 컨테이너를 지우거나 `docker compose down`을 하지 않는다. `~/day65-n8n`(n8n 설치·비밀값)을 읽거나 고치지 않는다. Credential을 새로 만들지 않는다.
- `.env`나 API 키를 읽어서 출력하지 않는다.
