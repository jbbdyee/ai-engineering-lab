# AGENTS.md · n8n 템플릿·모듈 작업 규칙 (70일차 실습 폴더)

이 파일은 **CLI 코딩 에이전트**(Codex, Claude Code, Antigravity 등)가 이 폴더에서 n8n 워크플로우를 만들 때 따르는 규칙입니다. 사람도 읽을 수 있게 썼습니다. 69일차 규칙과 같고, 3절이 오늘 만드는 **공지 키트 · 규칙 검사 모듈 · SMS의 계약**, 5절에 **모듈(Sub-workflow) 노드**가 더해졌습니다.

## 1. 작업 순서 (항상 이 순서)

1. 요청을 읽고, 만들 워크플로우의 **입력 · 노드 순서 · 결과 모양**을 3~5줄로 먼저 정리해 보여 준다. 모듈을 쓰면 **모듈 → 입력 → 결과 → 쓰는 곳** 표도 함께 보여 준다.
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
| 게시된 웹훅 주소 | 밖에서 `http://localhost:5678/webhook/<path>`, **n8n 안에서도** `http://localhost:5678/webhook/<path>` (같은 컨테이너) |
| OpenAI Credential | id `openAiCourse0001`, name `OpenAI (.env)`, 모델 `gpt-4.1-mini` |
| 다른 Credential | 쓰지 않음 (Ollama 등 없음, LLM은 모두 위 OpenAI Credential) |
| 데이터 API | 오늘은 쓰지 않음 (67일차 `Last3Mon/67/data-api`는 켜 두어도 됨) |

## 3. 오늘 만드는 것의 계약 (요청에 다른 말이 없으면 이대로)

| 무엇 | 파일 · 부르는 법 | 입력 | 결과 |
| --- | --- | --- | --- |
| 공지 키트 | `my-work/notice-kit.json` · `POST /webhook/my-notice-kit` | `kind`(필수), `facts`(필수), `request` | `{"kind", "route", "published", "notice", "codes"}` |
| 규칙 검사 모듈 | `my-work/rule-check.json` · **Execute Workflow** (id `modRuleCheck01`) | `facts`, `draft`, `max_length`(숫자), `required_phrases`(목록) | `{"passed", "codes", "issues"}` |
| 모듈 시험용 웹훅 | `my-work/rule-check-test.json` · `POST /webhook/my-rule-check` | 모듈 입력과 같음 (본문) | 모듈 결과 그대로 |
| SMS | `my-work/sms.json` · `POST /webhook/my-sms` | `facts`(필수) | `{"sms", "published", "codes"}` |

- 공지 종류 `kind`: `maintenance`(점검), `security`(보안), `training`(교육). 종류마다 다른 것(머리말, 최대 길이, 꼭 넣을 문장, 주의)은 **설정 표 한 곳**(`Kind settings` Code 노드)에만 둔다.
- 검사 코드: `missing_fact`(사실의 날짜·시간이 없음), `personal_info`(전화번호·메일 주소), `too_long`(`max_length` 넘음), `missing_phrase`(꼭 넣을 문장이 없음).
- 모듈 파일에는 `id`를 **직접** 쓴다 (`"id": "modRuleCheck01"`). 부르는 쪽은 이 id로 부른다. `push`는 파일의 id를 그대로 쓴다.

## 4. 워크플로우 파일 규칙

```json
{
  "name": "70 Notice kit (my)",
  "nodes": [ ... ],
  "connections": { ... },
  "settings": { "executionOrder": "v1" }
}
```

- 파일 하나에 워크플로우 하나. `id`는 쓰지 않아도 된다 (`push`가 파일 이름으로 정한다). **모듈만** `id`를 직접 쓴다 (3절).
- 노드 `name`은 영어로, 워크플로우 안에서 겹치지 않게. 노드마다 `type`, `typeVersion`, `position: [x, y]`, `parameters`가 필요하다.
- **API 키를 JSON에 쓰지 않는다.** LLM 노드는 위 Credential id만 쓴다.
- 웹훅은 `POST`, `responseMode: "responseNode"`, 결과는 Respond to Webhook 노드로 보낸다.
- 요청 본문은 `$json.body.kind`, `$json.body.facts`처럼 `body` 아래에 있다. 모듈 안에서는 입력이 `$json.facts`처럼 바로 있다 (`body` 없음).

## 5. 검증된 노드 (n8n 2.42.6에서 실행 확인)

아래 `type`/`typeVersion`을 그대로 쓴다. 다른 노드가 필요하면 써도 되지만 `flow.py check`가 이 n8n에 있는지 확인한다.

### Webhook · If · Respond to Webhook
```json
{"name": "Kit webhook", "type": "n8n-nodes-base.webhook", "typeVersion": 2, "position": [0, 300],
 "parameters": {"httpMethod": "POST", "path": "my-notice-kit", "responseMode": "responseNode", "options": {}}}
```
```json
{"name": "Has facts?", "type": "n8n-nodes-base.if", "typeVersion": 2.2, "position": [200, 300],
 "parameters": {"conditions": {"options": {"caseSensitive": true, "leftValue": "", "typeValidation": "strict", "version": 2},
   "conditions": [{"id": "c1", "leftValue": "={{ $json.body.facts }}", "rightValue": "",
     "operator": {"type": "string", "operation": "notEmpty", "singleValue": true}}], "combinator": "and"}, "options": {}}}
```
- If 출력 0번이 true, 1번이 false. 조건을 둘 넣으면 `combinator: "and"`. 불리언은 `"leftValue": "={{ $json.passed }}", "operator": {"type": "boolean", "operation": "true", "singleValue": true}`.
```json
{"name": "Send result", "type": "n8n-nodes-base.respondToWebhook", "typeVersion": 1.1, "position": [2600, 300],
 "parameters": {"respondWith": "json", "responseBody": "={{ $json }}", "options": {}}}
```
- 오류 응답: `"responseBody": "{ \"error\": \"kind and facts are required\" }"`, `"options": {"responseCode": 400}`. 값이 들어간 오류는 `"responseBody": "={{ JSON.stringify({ error: 'unknown kind', kinds: $json.kinds }) }}"`

### AI Agent + OpenAI chat model (작성자)
```json
{"name": "Writer agent", "type": "@n8n/n8n-nodes-langchain.agent", "typeVersion": 3.1, "position": [420, 300],
 "parameters": {"promptType": "define", "text": "=제목 머리말: {{ $('Kind settings').first().json.prefix }}\n사실:\n{{ $('Kit webhook').first().json.body.facts }}",
   "options": {"systemMessage": "You are the writer of company IT notices, in Korean. ... Return only the notice text.", "maxIterations": 2}}}
```
```json
{"name": "OpenAI chat model", "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi", "typeVersion": 1.2, "position": [380, 520],
 "parameters": {"model": {"__rl": true, "mode": "id", "value": "gpt-4.1-mini"}, "options": {"temperature": 0}},
 "credentials": {"openAiApi": {"id": "openAiCourse0001", "name": "OpenAI (.env)"}}}
```
- Agent의 결과는 `$json.output`(글자). JSON을 달라고 해도 **글자**로 오므로 다음 Code 노드에서 `JSON.parse` 한다 (앞뒤 ```` ``` ````를 지우고, 실패하면 빈 값).

### Code (JavaScript) · 설정 표
```json
{"name": "Kind settings", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [420, 300],
 "parameters": {"jsCode": "const KINDS = {\n  maintenance: { prefix: '[점검 안내]', max_length: 600, required_phrases: [] },\n  security: { prefix: '[보안 안내]', max_length: 500, required_phrases: ['IT팀은 절대 비밀번호를 묻지 않습니다.'] }\n};\nconst kind = String($('Kit webhook').first().json.body.kind ?? '');\nreturn [{ json: { kind, ...KINDS[kind] } }];"}}
```
- 반드시 `[{ json: {...} }]` 배열을 돌려준다. 뒤 노드는 `$('Kind settings').first().json.max_length`처럼 읽는다.
- 매번 같은 답이어야 하는 검사(날짜·시간, 전화번호, 길이, 꼭 넣을 문장)는 Code로. Code 노드 안에는 `URL` 클래스가 없다 (주소는 글자로 나눈다).

### Execute Workflow Trigger (모듈의 시작)
```json
{"name": "When called by another workflow", "type": "n8n-nodes-base.executeWorkflowTrigger", "typeVersion": 1.1, "position": [0, 300],
 "parameters": {"inputSource": "workflowInputs", "workflowInputs": {"values": [
   {"name": "facts", "type": "string"}, {"name": "draft", "type": "string"},
   {"name": "max_length", "type": "number"}, {"name": "required_phrases", "type": "array"}]}}}
```
- 모듈의 **마지막 노드 결과**가 부른 쪽으로 돌아간다 (Respond to Webhook 없음).
- 모듈도 `push`로 게시한다 (웹훅이 없다는 `!` 경고는 정상).

### Execute Workflow (모듈 부르기)
```json
{"name": "Rule check module", "type": "n8n-nodes-base.executeWorkflow", "typeVersion": 1.2, "position": [1280, 300],
 "parameters": {"workflowId": {"__rl": true, "mode": "id", "value": "modRuleCheck01"},
   "workflowInputs": {"mappingMode": "defineBelow",
     "value": {"facts": "={{ $('Kit webhook').first().json.body.facts }}", "draft": "={{ $json.draft }}",
               "max_length": "={{ $('Kind settings').first().json.max_length }}", "required_phrases": "={{ $('Kind settings').first().json.required_phrases }}"},
     "matchingColumns": [],
     "schema": [{"id": "facts", "displayName": "facts", "required": false, "defaultMatch": false, "display": true, "canBeUsedToMatch": true, "type": "string", "removed": false},
                {"id": "draft", "...": "facts와 같은 모양"}, {"id": "max_length", "type": "number", "...": ""}, {"id": "required_phrases", "type": "array", "...": ""}],
     "attemptToConvertTypes": false, "convertFieldsToString": true},
   "options": {}}}
```
- `schema`에 모듈 입력을 **모두** 적는다 (`type`은 Trigger와 같게). 결과는 다음 노드의 `$json`.
- 모듈을 웹훅 없이 따로 시험하려면 **시험용 웹훅 워크플로우**(웹훅 → Execute Workflow → Respond)를 하나 둔다.

## 6. 연결 (`connections`)

```json
{
  "Kit webhook": {"main": [[{"node": "Has kind and facts?", "type": "main", "index": 0}]]},
  "Has kind and facts?": {"main": [[{"node": "Kind settings", "type": "main", "index": 0}], [{"node": "Reject empty", "type": "main", "index": 0}]]},
  "OpenAI chat model": {"ai_languageModel": [[{"node": "Writer agent", "type": "ai_languageModel", "index": 0}]]},
  "Build draft": {"main": [[{"node": "Rule check module", "type": "main", "index": 0}]]},
  "When called by another workflow": {"main": [[{"node": "Rule checks", "type": "main", "index": 0}]]}
}
```
- 키는 **보내는 노드 이름**, 안의 `node`는 받는 노드 이름. If의 `main`은 `[ [true 쪽], [false 쪽] ]`.
- Chat model은 `ai_languageModel`, Tool은 `ai_tool`로 **Agent에** 연결한다 (`main` 아님).

## 7. 표현식 주의

- 표현식은 `=`로 시작한다: `"={{ $json.body.facts }}"`. `=`가 없으면 그냥 글자로 남는다.
- `{{ }}` 안에서 객체를 만들 때 `}}`가 붙지 않게 띄어 쓴다: `"={{ JSON.stringify({ draft: $json.draft }) }}"`
- 다른 노드 뒤에서 웹훅 입력은 `$('Kit webhook').first().json.body`로 읽는다 (`$json`은 바로 앞 노드 결과).

## 8. 테스트 파일 (`cases/*.json`)

```json
{
  "webhook": "my-notice-kit",
  "cases": [
    {"name": "보안 · 꼭 넣을 문장", "request": "requests/kit-security.json",
     "expect": {"status": 200, "equals": {"kind": "security", "codes": []}, "contains": {"notice": ["비밀번호를 묻지 않습니다"]}}},
    {"name": "직접 쓴 요청", "body": {"kind": "maintenance", "facts": ""}, "expect": {"status": 400}},
    {"name": "모듈 시험", "webhook": "my-rule-check", "request": "requests/module-good.json", "expect": {"equals": {"passed": true}}}
  ]
}
```
- 필드 이름은 점으로 내려간다: `issues.0.code` = `issues` 첫 항목의 `code`.
- `equals`: 값이 같아야 함 · `contains`: 목록 중 **하나라도** 들어 있어야 함 (배열·객체는 JSON 글자로 바꿔 찾음) · `not_contains`: 하나도 없어야 함 · `status`: HTTP 코드(기본 200)
- `uv run tools/flow.py test <파일> -v --repeat 3`: LLM 답은 매번 조금씩 다르므로 3번 이상 돌려 본다. `-v`(`--verbose`)는 케이스마다 보낸 요청 JSON과 받은 응답 JSON을 화면에 보여 준다 (보고서 `runs/*.json`에도 같은 것이 남음). `call ... -v`도 보낸 요청 JSON을 응답 위에 함께 보여 준다.
- **테스트를 통과시키려고 테스트 파일의 기대 결과를 바꾸지 않는다.** 기대 결과가 틀렸다고 생각되면 사람에게 묻는다.

## 9. 하지 말 것

- `tools/`, `requests/`, `reference/`, `samples/`, 이 파일(`AGENTS.md`)을 고치지 않는다 (요청받은 경우만).
- 모듈이 있으면 같은 검사를 호출하는 쪽에 다시 쓰지 않는다 (복사 대신 모듈 호출).
- 모듈의 입력·결과 이름을 바꾸거나 지우지 않는다. 바꿔야 하면 **새 id로 새 버전**을 만들고 사람에게 알린다.
- n8n 컨테이너를 지우거나 `docker compose down`을 하지 않는다. `~/day65-n8n`(n8n 설치·비밀값)을 읽거나 고치지 않는다. Credential을 새로 만들지 않는다.
- `.env`나 API 키를 읽어서 출력하지 않는다.
