# AGENTS.md · n8n 워크플로우 작업 규칙 (66일차 실습 폴더)

이 파일은 **CLI 코딩 에이전트**(Codex, Claude Code, Antigravity 등)가 이 폴더에서 n8n 워크플로우를 만들 때 따르는 규칙입니다. 사람도 읽을 수 있게 썼습니다. 3절이 오늘 만드는 **회의록 → 할 일 워크플로우의 계약**입니다.

## 1. 작업 순서 (항상 이 순서)

1. 요청을 읽고, 만들 워크플로우의 **입력 · 노드 순서 · 결과 모양**을 3~5줄로 먼저 정리해 보여 준다. 항목이 몇 개씩 지나가는지(1 → N → 1)도 함께 적는다.
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
| 데이터 API | 오늘은 쓰지 않음 (67일차부터) |

## 3. 오늘 만드는 것의 계약 (요청에 다른 말이 없으면 이대로)

워크플로우 **하나**(`my-work/meeting.json`, 웹훅 `POST /webhook/my-meeting`)를 Lab 01 → 02 → 03으로 키워 간다.

| Lab | 입력 (요청 본문) | 결과 |
| --- | --- | --- |
| Lab 01 | `title`, `notes` | `{"title", "summary"}` |
| Lab 02 | 같음 | `{"title", "summary", "count", "actions": [{"owner", "task", "due"}]}` |
| Lab 03 | 같음 | Lab 02 + 할 일마다 `needs_check`(불리언), 전체 `needs_check_count` |

- `notes`가 비었거나 공백뿐이면 400 `{"error": "notes are required"}` (LLM을 부르지 않음). `title`이 없으면 `"회의"`.
- 담당자(`owner`)나 기한(`due`)이 회의록에 없으면 `"미정"`. 지어내지 않는다.
- `needs_check`: `owner`나 `due`가 `"미정"`이면 `true`.

## 4. 워크플로우 파일 규칙

```json
{
  "name": "66 Meeting actions (my)",
  "nodes": [ ... ],
  "connections": { ... },
  "settings": { "executionOrder": "v1" }
}
```

- 파일 하나에 워크플로우 하나. `id`는 쓰지 않아도 된다 (`push`가 파일 이름으로 정한다).
- 노드 `name`은 영어로, 워크플로우 안에서 겹치지 않게. 노드마다 `type`, `typeVersion`, `position: [x, y]`, `parameters`가 필요하다.
- **API 키를 JSON에 쓰지 않는다.** LLM 노드는 위 Credential id만 쓴다.
- 웹훅은 `POST`, `responseMode: "responseNode"`, 결과는 Respond to Webhook 노드로 보낸다.
- 요청 본문은 `$json.body.title`, `$json.body.notes`처럼 `body` 아래에 있다.

## 5. 검증된 노드 (n8n 2.42.6에서 실행 확인)

아래 `type`/`typeVersion`을 그대로 쓴다. 다른 노드가 필요하면 써도 되지만 `flow.py check`가 이 n8n에 있는지 확인한다.

### Webhook · If · Respond to Webhook
```json
{"name": "Meeting webhook", "type": "n8n-nodes-base.webhook", "typeVersion": 2, "position": [0, 300],
 "parameters": {"httpMethod": "POST", "path": "my-meeting", "responseMode": "responseNode", "options": {}}}
```
```json
{"name": "Has notes?", "type": "n8n-nodes-base.if", "typeVersion": 2.2, "position": [200, 300],
 "parameters": {"conditions": {"options": {"caseSensitive": true, "leftValue": "", "typeValidation": "strict", "version": 2},
   "conditions": [{"id": "c1", "leftValue": "={{ $json.body.notes }}", "rightValue": "",
     "operator": {"type": "string", "operation": "notEmpty", "singleValue": true}}], "combinator": "and"}, "options": {}}}
```
- If 출력 0번이 true, 1번이 false. 조건을 둘 넣으면 `combinator: "and"`. 불리언은 `"leftValue": "={{ $json.passed }}", "operator": {"type": "boolean", "operation": "true", "singleValue": true}`.
```json
{"name": "Send result", "type": "n8n-nodes-base.respondToWebhook", "typeVersion": 1.1, "position": [2600, 300],
 "parameters": {"respondWith": "json", "responseBody": "={{ $json }}", "options": {}}}
```
- 오류 응답: `"responseBody": "{ \"error\": \"notes are required\" }"`, `"options": {"responseCode": 400}`

### AI Agent + OpenAI chat model (요약, 할 일 뽑기)
```json
{"name": "Extract actions", "type": "@n8n/n8n-nodes-langchain.agent", "typeVersion": 3.1, "position": [680, 300],
 "parameters": {"promptType": "define", "text": "=회의 제목: {{ $('Meeting webhook').first().json.body.title }}\n회의록:\n{{ $('Meeting webhook').first().json.body.notes }}",
   "options": {"systemMessage": "You read Korean meeting notes and list every action item. Return only JSON, no code fence: {\"actions\": [...]} ...", "maxIterations": 2}}}
```
```json
{"name": "OpenAI chat model", "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi", "typeVersion": 1.2, "position": [380, 520],
 "parameters": {"model": {"__rl": true, "mode": "id", "value": "gpt-4.1-mini"}, "options": {"temperature": 0}},
 "credentials": {"openAiApi": {"id": "openAiCourse0001", "name": "OpenAI (.env)"}}}
```
- Agent의 결과는 `$json.output`(글자). JSON을 달라고 해도 **글자**로 오므로 다음 Code 노드에서 `JSON.parse` 한다 (앞뒤 ```` ``` ````를 지우고, 실패하면 빈 값).
- Chat model 노드 하나는 Agent **하나**에 연결한다. Agent가 둘이면 model 노드도 둘 (`Summary model`, `Actions model`).

### Code (JavaScript) · LLM 글자를 JSON으로
```json
{"name": "Parse actions", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [940, 300],
 "parameters": {"jsCode": "const raw = String($json.output ?? '').trim().replace(/^```(json)?\\s*|```$/g, '');\nlet data = {};\ntry { data = JSON.parse(raw); } catch (error) { data = {}; }\nconst actions = (data.actions ?? []).map(a => ({ owner: a.owner || '미정', task: a.task, due: a.due || '미정' }));\nreturn [{ json: { count: actions.length, actions } }];"}}
```
- 반드시 `[{ json: {...} }]` 배열을 돌려준다. 앞 노드는 `$('노드 이름').first().json`.
- LLM에게 JSON을 달라고 해도 **글자**로 온다. 읽지 못하면 멈추지 말고 빈 목록으로.

### Split Out · Aggregate (항목 하나씩 → 다시 하나로)
```json
{"name": "One item per action", "type": "n8n-nodes-base.splitOut", "typeVersion": 1, "position": [1380, 200], "parameters": {"fieldToSplitOut": "actions", "options": {}}}
```
```json
{"name": "Collect actions", "type": "n8n-nodes-base.aggregate", "typeVersion": 1, "position": [1820, 200],
 "parameters": {"aggregate": "aggregateAllItemData", "destinationFieldName": "actions", "options": {}}}
```
- Split Out: 목록 하나 → 항목 여러 개 (1 → N). 그 사이 노드는 **항목마다** 실행된다. Aggregate: 다시 목록 하나로 (N → 1).
- 목록이 비면 Split Out 뒤로 아무것도 흐르지 않아 응답이 없다 → 앞에 If(`count > 0`)를 두고 빈 경우는 따로 응답한다.

### Edit Fields (Set) · Merge (나눈 갈래 모으기)
```json
{"name": "Mark check", "type": "n8n-nodes-base.set", "typeVersion": 3.4, "position": [1600, 200],
 "parameters": {"assignments": {"assignments": [
   {"id": "a0", "name": "owner", "value": "={{ $json.owner }}", "type": "string"},
   {"id": "a1", "name": "task", "value": "={{ $json.task }}", "type": "string"},
   {"id": "a2", "name": "due", "value": "={{ $json.due }}", "type": "string"},
   {"id": "a3", "name": "needs_check", "value": "={{ $json.owner === '미정' || $json.due === '미정' }}", "type": "boolean"}]}, "options": {}}}
```
```json
{"name": "Join results", "type": "n8n-nodes-base.merge", "typeVersion": 3, "position": [700, 300], "parameters": {"numberInputs": 2}}
```
- Set은 **적은 칸만** 남긴다.
- 한 노드에서 두 노드로 **함께** 보내려면 `main` 첫 칸에 둘을 넣는다 (갈래 나누기). Merge로 다시 모은다. 다음 Code에서 `$('Summarize').first().json.output`처럼 이름으로 읽는다.

## 6. 연결 (`connections`)

```json
{
  "Meeting webhook": {"main": [[{"node": "Has notes?", "type": "main", "index": 0}]]},
  "Has notes?": {"main": [[{"node": "Summarize", "type": "main", "index": 0}, {"node": "Extract actions", "type": "main", "index": 0}], [{"node": "Reject empty", "type": "main", "index": 0}]]},
  "Summary model": {"ai_languageModel": [[{"node": "Summarize", "type": "ai_languageModel", "index": 0}]]},
  "Summarize": {"main": [[{"node": "Join results", "type": "main", "index": 0}]]},
  "Extract actions": {"main": [[{"node": "Join results", "type": "main", "index": 1}]]}
}
```
- 키는 **보내는 노드 이름**, 안의 `node`는 받는 노드 이름. If의 `main`은 `[ [true 쪽], [false 쪽] ]`.
- Chat model은 `ai_languageModel`로 **Agent에** 연결한다 (`main` 아님).
- Merge로 들어가는 연결은 `index`가 입력 번호 (0, 1, 2 …).

## 7. 표현식 주의

- 표현식은 `=`로 시작한다: `"={{ $json.body.notes }}"`. `=`가 없으면 그냥 글자로 남는다.
- `{{ }}` 안에서 객체를 만들 때 `}}`가 붙지 않게 띄어 쓴다: `"={{ { count: $json.count } }}"`
- 다른 노드 뒤에서 웹훅 입력은 `$('Meeting webhook').first().json.body`로 읽는다 (`$json`은 바로 앞 노드 결과).

## 8. 테스트 파일 (`cases/*.json`)

```json
{
  "webhook": "my-meeting",
  "cases": [
    {"name": "주간 회의", "request": "requests/weekly.json",
     "expect": {"status": 200, "equals": {"count": 4, "actions.0.owner": "이준호"}, "contains": {"actions.0.due": ["금요일"]}}},
    {"name": "직접 쓴 요청", "body": {"title": "x", "notes": ""}, "expect": {"status": 400}}
  ]
}
```
- 필드 이름은 점으로 내려간다: `actions.0.owner` = `actions` 첫 항목의 `owner`.
- `equals`: 값이 같아야 함 · `contains`: 목록 중 **하나라도** 들어 있어야 함 (배열·객체는 JSON 글자로 바꿔 찾음) · `not_contains`: 하나도 없어야 함 · `status`: HTTP 코드(기본 200)
- `uv run tools/flow.py test <파일> --repeat 3`: LLM 답은 매번 조금씩 다르므로 3번 이상 돌려 본다.
- **테스트를 통과시키려고 테스트 파일의 기대 결과를 바꾸지 않는다.** 기대 결과가 틀렸다고 생각되면 사람에게 묻는다.

## 9. 하지 말 것

- `tools/`, `requests/`, `reference/`, 이 파일(`AGENTS.md`)을 고치지 않는다 (요청받은 경우만).
- n8n 컨테이너를 지우거나 `docker compose down`을 하지 않는다. `~/day65-n8n`(n8n 설치·비밀값)을 읽거나 고치지 않는다. Credential을 새로 만들지 않는다.
- `.env`나 API 키를 읽어서 출력하지 않는다.
