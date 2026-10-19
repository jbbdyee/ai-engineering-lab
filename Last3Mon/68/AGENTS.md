# AGENTS.md · n8n Multi-Agent 워크플로우 작업 규칙 (68일차 실습 폴더)

이 파일은 **CLI 코딩 에이전트**(Codex, Claude Code, Antigravity 등)가 이 폴더에서 n8n 워크플로우를 만들 때 따르는 규칙입니다. 사람도 읽을 수 있게 썼습니다. 67일차 규칙과 같고, 여러 Agent를 부르는 라우터용 노드(5절)가 더해졌습니다.

## 1. 작업 순서 (항상 이 순서)

1. 요청을 읽고, 만들 워크플로우의 **입력 · 노드 순서 · 결과 모양**을 3~5줄로 먼저 정리해 보여 준다. 업무가 여럿이면 **업무 → 담당 Agent** 표도 함께 보여 준다.
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
| 게시된 웹훅 주소 | 밖에서 `http://localhost:5678/webhook/<path>`, **n8n 안에서도** `http://localhost:5678/webhook/<path>` (같은 컨테이너) |
| OpenAI Credential | id `openAiCourse0001`, name `OpenAI (.env)`, 모델 `gpt-4.1-mini` |
| 다른 Credential | 쓰지 않음 (Ollama 등 없음, LLM은 모두 위 OpenAI Credential) |
| 데이터 API | n8n 안에서 `http://data-api:8800`, 터미널에서 `http://localhost:8800` (67일차 `Last3Mon/67/data-api`) |

## 3. 이미 있는 Agent (`agents/`, 고치지 말 것)

라우터는 이 Agent들을 **HTTP로 부른다.** 내용을 바꾸지 말고 계약(입력 · 결과)만 지킨다.

| Agent | 파일 | 웹훅 | 입력 (요청 본문) | 결과 |
| --- | --- | --- | --- | --- |
| IT 문의 Agent (67일차) | `agents/it-agent.json` | `POST /webhook/it-agent` | `question`, `user` (둘 다 필수, 없으면 400) | `route`(자동 답변·담당자 연결), `answer`, `tools_used`, `sources` |
| 회의록 Agent (66일차) | `agents/meeting-agent.json` | `POST /webhook/meeting-agent` | `title`, `notes` (`notes` 필수, 없으면 400 `{"error": "notes are required"}`) | `route`, `title`, `count`, `summary`, `actions: [{owner, task, due}]` |

- IT 문의 Agent는 남의 접수 건을 보여 주지 않고 `route: 담당자 연결`로 돌려준다 (67일차 규칙).
- 라우터의 요청 본문: `message`(직원 요청 문장), `user`(요청한 사람), 회의록이 있으면 `title`, `notes`.

## 4. 워크플로우 파일 규칙

```json
{
  "name": "68 Assistant router (my)",
  "nodes": [ ... ],
  "connections": { ... },
  "settings": { "executionOrder": "v1" }
}
```

- 파일 하나에 워크플로우 하나. `id`는 쓰지 않아도 된다 (`push`가 파일 이름으로 정한다).
- 노드 `name`은 영어로, 워크플로우 안에서 겹치지 않게. 노드마다 `type`, `typeVersion`, `position: [x, y]`, `parameters`가 필요하다.
- **API 키를 JSON에 쓰지 않는다.** LLM 노드는 위 Credential id만 쓴다.
- 웹훅은 `POST`, `responseMode: "responseNode"`, 결과는 Respond to Webhook 노드로 보낸다.
- 요청 본문은 `$json.body.message`, `$json.body.user`처럼 `body` 아래에 있다.

## 5. 검증된 노드 (n8n 2.42.6에서 실행 확인)

아래 `type`/`typeVersion`을 그대로 쓴다. 다른 노드가 필요하면 써도 되지만 `flow.py check`가 이 n8n에 있는지 확인한다.

### Webhook · If · Respond to Webhook
```json
{"name": "Assistant webhook", "type": "n8n-nodes-base.webhook", "typeVersion": 2, "position": [0, 300],
 "parameters": {"httpMethod": "POST", "path": "my-assistant", "responseMode": "responseNode", "options": {}}}
```
```json
{"name": "Has message?", "type": "n8n-nodes-base.if", "typeVersion": 2.2, "position": [200, 300],
 "parameters": {"conditions": {"options": {"caseSensitive": true, "leftValue": "", "typeValidation": "strict", "version": 2},
   "conditions": [{"id": "c1", "leftValue": "={{ $json.body.message }}", "rightValue": "",
     "operator": {"type": "string", "operation": "notEmpty", "singleValue": true}}], "combinator": "and"}, "options": {}}}
```
- If 출력 0번이 true, 1번이 false. 숫자 비교는 `"operator": {"type": "number", "operation": "equals"}` (`gt`, `lt`도 있음).
```json
{"name": "Send result", "type": "n8n-nodes-base.respondToWebhook", "typeVersion": 1.1, "position": [2360, 300],
 "parameters": {"respondWith": "json", "responseBody": "={{ $json }}", "options": {}}}
```
- 오류 응답: `"responseBody": "{ \"error\": \"message is required\" }"`, `"options": {"responseCode": 400}`

### AI Agent + OpenAI chat model (업무 나누기, Supervisor)
```json
{"name": "Split tasks", "type": "@n8n/n8n-nodes-langchain.agent", "typeVersion": 3.1, "position": [420, 300],
 "parameters": {"promptType": "define", "text": "={{ $('Assistant webhook').first().json.body.message }}",
   "options": {"systemMessage": "You split one employee message into separate tasks. ... Return only JSON, no code fence: {\"tasks\": [...]}", "maxIterations": 2}}}
```
```json
{"name": "OpenAI chat model", "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi", "typeVersion": 1.2, "position": [380, 520],
 "parameters": {"model": {"__rl": true, "mode": "id", "value": "gpt-4.1-mini"}, "options": {"temperature": 0}},
 "credentials": {"openAiApi": {"id": "openAiCourse0001", "name": "OpenAI (.env)"}}}
```
- Agent의 결과는 `$json.output`(글자). JSON을 달라고 해도 **글자**로 오므로 다음 Code 노드에서 `JSON.parse` 한다 (앞뒤 ```` ``` ````를 지우고, 실패하면 빈 목록).
- `returnIntermediateSteps: true`면 `$json.intermediateSteps`에 Tool 호출 기록: `[{ "action": { "tool": "Ask_IT_agent", "toolInput": {...} }, "observation": "..." }]`. Tool 이름은 노드 이름의 빈칸이 `_`로 바뀐 것.

### Code (JavaScript) · 여러 항목 돌려주기
```json
{"name": "One item per task", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [880, 300],
 "parameters": {"jsCode": "return $json.tasks.map((task, index) => ({ json: { index: index + 1, ...task } }));"}}
```
- 반드시 `[{ json: {...} }, ...]` 배열을 돌려준다. 항목이 여럿이면 다음 노드는 **항목마다** 한 번씩 실행된다.
- 앞 노드는 `$('노드 이름').first().json`, 같은 항목의 앞 노드 값은 `$('노드 이름').item.json`.

### Switch (업무 유형별로 나누기)
```json
{"name": "Route by type", "type": "n8n-nodes-base.switch", "typeVersion": 3.2, "position": [1080, 300],
 "parameters": {"rules": {"values": [
   {"conditions": {"options": {"caseSensitive": true, "leftValue": "", "typeValidation": "strict", "version": 2},
     "conditions": [{"id": "r-it", "leftValue": "={{ $json.type }}", "rightValue": "it", "operator": {"type": "string", "operation": "equals"}}],
     "combinator": "and"}, "renameOutput": true, "outputKey": "it"},
   {"conditions": {"...": "meeting 같은 모양"}, "renameOutput": true, "outputKey": "meeting"}]}, "options": {}}}
```
- 규칙 순서대로 출력 0, 1, 2 …. 연결의 `main`도 같은 순서의 칸.

### HTTP Request (다른 Agent 부르기)
```json
{"name": "Call IT agent", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [1300, 100],
 "parameters": {"method": "POST", "url": "http://localhost:5678/webhook/it-agent", "sendBody": true, "specifyBody": "json",
   "jsonBody": "={{ JSON.stringify({ question: $json.text, user: $('Assistant webhook').first().json.body.user }) }}",
   "options": {"timeout": 60000, "response": {"response": {"neverError": true}}}}}
```
- `neverError: true`가 없으면 부른 Agent가 400·404·500을 돌려줄 때 **워크플로우 전체가 멈춘다** (응답 500).
- 응답 본문이 그대로 다음 노드의 `$json`이 된다 (`$json.route`, `$json.answer` …).

### HTTP Request Tool (Supervisor가 Agent를 Tool로 부를 때)
```json
{"name": "Ask IT agent", "type": "n8n-nodes-base.httpRequestTool", "typeVersion": 4.2, "position": [480, 520],
 "parameters": {"toolDescription": "Ask the company IT agent one IT question ... Input: one question in Korean.",
   "method": "POST", "url": "http://localhost:5678/webhook/it-agent", "sendBody": true,
   "bodyParameters": {"parameters": [
     {"name": "question", "value": "={{ $fromAI('question', 'One IT question in Korean', 'string') }}"},
     {"name": "user", "value": "={{ $('Assistant webhook').first().json.body.user }}"}]},
   "options": {"timeout": 60000, "response": {"response": {"neverError": true}}}}}
```
- `$fromAI`는 LLM이 정하는 값. **LLM이 정하면 안 되는 값**(요청한 사람, 회의록 원문)은 웹훅 입력에서 표현식으로 가져온다.

### Edit Fields (Set) · Merge · Aggregate (결과 모으기)
```json
{"name": "IT result", "type": "n8n-nodes-base.set", "typeVersion": 3.4, "position": [1520, 100],
 "parameters": {"assignments": {"assignments": [
   {"id": "a0", "name": "index", "value": "={{ $('Route by type').item.json.index }}", "type": "number"},
   {"id": "a1", "name": "route", "value": "={{ $json.route || '담당자 연결' }}", "type": "string"},
   {"id": "a2", "name": "answer", "value": "={{ $json.answer }}", "type": "string"}]}, "options": {}}}
```
```json
{"name": "Collect results", "type": "n8n-nodes-base.merge", "typeVersion": 3, "position": [1760, 300], "parameters": {"numberInputs": 3}}
```
```json
{"name": "All results", "type": "n8n-nodes-base.aggregate", "typeVersion": 1, "position": [1960, 300],
 "parameters": {"aggregate": "aggregateAllItemData", "destinationFieldName": "results", "options": {}}}
```
- Merge는 갈래를 하나로 모은다 (입력 수 = `numberInputs`, 연결의 `index`로 몇 번 입력인지 정함). 데이터가 오지 않은 입력이 있어도 동작한다.
- Aggregate는 여러 항목을 `results` 배열 **한 항목**으로 묶는다. 그 뒤 Code에서 `index`로 정렬해 답을 만든다.

## 6. 연결 (`connections`)

```json
{
  "Has message?": {"main": [[{"node": "Split tasks", "type": "main", "index": 0}], [{"node": "Reject empty", "type": "main", "index": 0}]]},
  "OpenAI chat model": {"ai_languageModel": [[{"node": "Split tasks", "type": "ai_languageModel", "index": 0}]]},
  "Route by type": {"main": [[{"node": "Call IT agent", "type": "main", "index": 0}], [{"node": "Call meeting agent", "type": "main", "index": 0}], [{"node": "Other result", "type": "main", "index": 0}]]},
  "IT result": {"main": [[{"node": "Collect results", "type": "main", "index": 0}]]},
  "Meeting result": {"main": [[{"node": "Collect results", "type": "main", "index": 1}]]}
}
```
- 키는 **보내는 노드 이름**, 안의 `node`는 받는 노드 이름. If·Switch의 `main`은 출력 순서대로 칸이 나뉜다.
- Chat model은 `ai_languageModel`, Tool은 `ai_tool`로 **Agent에** 연결한다 (`main` 아님).
- Merge로 들어가는 연결은 `index`가 입력 번호 (0, 1, 2 …).

## 7. 표현식 주의

- 표현식은 `=`로 시작한다: `"={{ $json.body.message }}"`. `=`가 없으면 그냥 글자로 남는다.
- `{{ }}` 안에서 객체를 만들 때 `}}`가 붙지 않게 띄어 쓴다: `"={{ JSON.stringify({ question: $json.text }) }}"`
- Agent·HTTP 뒤 노드에서 웹훅 입력은 `$('Assistant webhook').first().json.body`로 읽는다 (`$json`은 바로 앞 노드 결과).

## 8. 테스트 파일 (`cases/*.json`)

```json
{
  "webhook": "my-assistant",
  "cases": [
    {"name": "복합 요청", "request": "requests/composite.json",
     "expect": {"status": 200, "equals": {"count": 3, "results.1.agent": "meeting-agent"},
                "contains": {"results.0.answer": ["처리 중"]}, "not_contains": {"reply": ["정우성"]}}},
    {"name": "직접 쓴 요청", "body": {"message": "", "user": "이준호"}, "expect": {"status": 400}},
    {"name": "다른 웹훅으로", "webhook": "it-agent", "body": {"question": "VPN", "user": "이준호"}, "expect": {}}
  ]
}
```
- 필드 이름은 점으로 내려간다: `results.0.answer` = `results` 첫 항목의 `answer`.
- `equals`: 값이 같아야 함 · `contains`: 목록 중 **하나라도** 들어 있어야 함 (배열·객체는 JSON 글자로 바꿔 찾음) · `not_contains`: 하나도 없어야 함 · `status`: HTTP 코드(기본 200)
- `uv run tools/flow.py test <파일> --repeat 3`: LLM 답은 매번 조금씩 다르므로 3번 이상 돌려 본다.
- **테스트를 통과시키려고 테스트 파일의 기대 결과를 바꾸지 않는다.** 기대 결과가 틀렸다고 생각되면 사람에게 묻는다.

## 9. 하지 말 것

- `tools/`, `agents/`, `requests/`, 이 파일(`AGENTS.md`)을 고치지 않는다 (요청받은 경우만).
- 이미 있는 Agent의 일을 라우터 안에서 다시 만들지 않는다 (FAQ·접수 현황을 라우터가 직접 조회하지 않는다).
- n8n 컨테이너를 지우거나 `docker compose down`을 하지 않는다. `~/day65-n8n`(n8n 설치·비밀값)을 읽거나 고치지 않는다. Credential을 새로 만들지 않는다.
- `.env`나 API 키를 읽어서 출력하지 않는다.
