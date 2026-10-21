# AGENTS.md · n8n 역할 협업 워크플로우 작업 규칙 (69일차 실습 폴더)

이 파일은 **CLI 코딩 에이전트**(Codex, Claude Code, Antigravity 등)가 이 폴더에서 n8n 워크플로우를 만들 때 따르는 규칙입니다. 사람도 읽을 수 있게 썼습니다. 68일차 규칙과 같고, 3절이 오늘 만드는 **역할(작성자 · 검토자 · 공지 팀)의 계약**입니다.

## 1. 작업 순서 (항상 이 순서)

1. 요청을 읽고, 만들 워크플로우의 **입력 · 노드 순서 · 결과 모양**을 3~5줄로 먼저 정리해 보여 준다. 역할이 여럿이면 **역할 → 입력 → 결과** 표도 함께 보여 준다.
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

## 3. 오늘 만드는 역할의 계약 (요청에 다른 말이 없으면 이대로)

역할마다 **워크플로우 하나, 웹훅 하나**. 공지 팀(`my-notice`)은 작성자·검토자를 **HTTP로 부른다.**

| 역할 | 파일 · 웹훅 | 입력 (요청 본문) | 결과 |
| --- | --- | --- | --- |
| 작성자 | `my-work/writer.json` · `POST /webhook/my-writer` | `request`, `facts`(필수, 없으면 400), 고칠 때 `previous_draft`, `feedback` | `{"draft": "..."}` |
| 검토자 | `my-work/reviewer.json` · `POST /webhook/my-reviewer` | `facts`, `draft` (둘 다 필수, 없으면 400) | `{"passed": true, "codes": [], "issues": [{"code", "detail"}]}` |
| 공지 팀 | `my-work/notice.json` · `POST /webhook/my-notice` | `request`, `facts`(필수), `author` | `{"route", "published", "rounds", "notice", "codes", ...}` |

- 검토 코드: `missing_fact`(사실의 날짜·시간이 초안에 없음), `personal_info`(전화번호·메일 주소), `too_long`(600자 넘음), `unsupported_claim`(사실에 없는 약속·보상·연락처).
- `route` 값: `게시 가능`, `수정 후 게시 가능`, `담당자 확인`. `published`는 `true`/`false` (불리언).
- 다른 사람의 역할 워크플로우(예: `reference/lab02-start-reviewer.json`)를 써도 웹훅과 계약이 같으면 공지 팀은 그대로 동작한다.

## 4. 워크플로우 파일 규칙

```json
{
  "name": "69 Notice team (my)",
  "nodes": [ ... ],
  "connections": { ... },
  "settings": { "executionOrder": "v1" }
}
```

- 파일 하나에 워크플로우 하나. `id`는 쓰지 않아도 된다 (`push`가 파일 이름으로 정한다).
- 노드 `name`은 영어로, 워크플로우 안에서 겹치지 않게. 노드마다 `type`, `typeVersion`, `position: [x, y]`, `parameters`가 필요하다.
- **API 키를 JSON에 쓰지 않는다.** LLM 노드는 위 Credential id만 쓴다.
- 웹훅은 `POST`, `responseMode: "responseNode"`, 결과는 Respond to Webhook 노드로 보낸다.
- 요청 본문은 `$json.body.facts`, `$json.body.draft`처럼 `body` 아래에 있다.

## 5. 검증된 노드 (n8n 2.42.6에서 실행 확인)

아래 `type`/`typeVersion`을 그대로 쓴다. 다른 노드가 필요하면 써도 되지만 `flow.py check`가 이 n8n에 있는지 확인한다.

### Webhook · If · Respond to Webhook
```json
{"name": "Notice webhook", "type": "n8n-nodes-base.webhook", "typeVersion": 2, "position": [0, 300],
 "parameters": {"httpMethod": "POST", "path": "my-notice", "responseMode": "responseNode", "options": {}}}
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
- 오류 응답: `"responseBody": "{ \"error\": \"facts are required\" }"`, `"options": {"responseCode": 400}`

### AI Agent + OpenAI chat model (작성자, 검토자의 LLM 판단, 정리자)
```json
{"name": "Writer agent", "type": "@n8n/n8n-nodes-langchain.agent", "typeVersion": 3.1, "position": [420, 300],
 "parameters": {"promptType": "define", "text": "=요청: {{ $('Writer webhook').first().json.body.request }}\n사실:\n{{ $('Writer webhook').first().json.body.facts }}",
   "options": {"systemMessage": "You are the writer of company IT notices, in Korean. ... Return only the notice text.", "maxIterations": 2}}}
```
```json
{"name": "OpenAI chat model", "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi", "typeVersion": 1.2, "position": [380, 520],
 "parameters": {"model": {"__rl": true, "mode": "id", "value": "gpt-4.1-mini"}, "options": {"temperature": 0}},
 "credentials": {"openAiApi": {"id": "openAiCourse0001", "name": "OpenAI (.env)"}}}
```
- Agent의 결과는 `$json.output`(글자). JSON을 달라고 해도 **글자**로 오므로 다음 Code 노드에서 `JSON.parse` 한다 (앞뒤 ```` ``` ````를 지우고, 실패하면 빈 값).
- Chat model 노드 하나는 Agent **하나**에 연결한다. Agent가 둘이면 model 노드도 둘 (`Title model`, `Chat model`).

### Code (JavaScript) · 규칙 검사
```json
{"name": "Rule checks", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [420, 300],
 "parameters": {"jsCode": "const body = $('Review webhook').first().json.body;\nconst issues = [];\nif (String(body.draft ?? '').length > 600) issues.push({ code: 'too_long', detail: '600자 넘음' });\nreturn [{ json: { rule_issues: issues } }];"}}
```
- 반드시 `[{ json: {...} }]` 배열을 돌려준다. 앞 노드는 `$('노드 이름').first().json`.
- 매번 같은 답이어야 하는 검사(날짜·시간이 있나, 전화번호, 길이)는 Code로. LLM은 뜻을 봐야 하는 검사(사실에 없는 약속)만.

### HTTP Request (다른 역할 부르기)
```json
{"name": "Review draft", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [640, 300],
 "parameters": {"method": "POST", "url": "http://localhost:5678/webhook/my-reviewer", "sendBody": true, "specifyBody": "json",
   "jsonBody": "={{ JSON.stringify({ facts: $('Notice webhook').first().json.body.facts, draft: $json.draft }) }}",
   "options": {"timeout": 60000, "response": {"response": {"neverError": true}}}}}
```
- `neverError: true`가 없으면 부른 역할이 400·404·500을 돌려줄 때 **워크플로우 전체가 멈춘다** (응답 500).
- 응답 본문이 그대로 다음 노드의 `$json`이 된다 (`$json.draft`, `$json.passed` …).
- 같은 역할을 두 번 부를 때(고쳐 쓰기)는 노드를 하나 더 둔다 (`Revise draft`, `Review again`). **고리(loop)로 되돌리지 않는다** (끝없이 돌 수 있음).

### Edit Fields (Set) · Merge (나눈 갈래 모으기)
```json
{"name": "Approved", "type": "n8n-nodes-base.set", "typeVersion": 3.4, "position": [1300, 160],
 "parameters": {"assignments": {"assignments": [
   {"id": "a0", "name": "route", "value": "게시 가능", "type": "string"},
   {"id": "a1", "name": "published", "value": true, "type": "boolean"},
   {"id": "a2", "name": "notice", "value": "={{ $('Write draft').first().json.draft }}", "type": "string"},
   {"id": "a3", "name": "steps", "value": "={{ [\"writer\", \"reviewer\"] }}", "type": "array"}]}, "options": {}}}
```
```json
{"name": "Join editors", "type": "n8n-nodes-base.merge", "typeVersion": 3, "position": [2620, 200], "parameters": {"numberInputs": 2}}
```
- 한 노드에서 두 노드로 **함께** 보내려면 `main` 첫 칸에 둘을 넣는다 (Fork). Merge로 다시 모은다 (Join). 다음 Code에서 `$('Make title').first().json.output`처럼 이름으로 읽는다.

## 6. 연결 (`connections`)

```json
{
  "Has facts?": {"main": [[{"node": "Write draft", "type": "main", "index": 0}], [{"node": "Reject empty", "type": "main", "index": 0}]]},
  "Passed?": {"main": [[{"node": "Approved", "type": "main", "index": 0}], [{"node": "Revise draft", "type": "main", "index": 0}]]},
  "Final notice": {"main": [[{"node": "Make title", "type": "main", "index": 0}, {"node": "Make chat message", "type": "main", "index": 0}]]},
  "Make title": {"main": [[{"node": "Join editors", "type": "main", "index": 0}]]},
  "Make chat message": {"main": [[{"node": "Join editors", "type": "main", "index": 1}]]},
  "Title model": {"ai_languageModel": [[{"node": "Make title", "type": "ai_languageModel", "index": 0}]]}
}
```
- 키는 **보내는 노드 이름**, 안의 `node`는 받는 노드 이름. If의 `main`은 `[ [true 쪽], [false 쪽] ]`.
- Chat model은 `ai_languageModel`, Tool은 `ai_tool`로 **Agent에** 연결한다 (`main` 아님).
- Merge로 들어가는 연결은 `index`가 입력 번호 (0, 1, 2 …).

## 7. 표현식 주의

- 표현식은 `=`로 시작한다: `"={{ $json.body.facts }}"`. `=`가 없으면 그냥 글자로 남는다.
- `{{ }}` 안에서 객체를 만들 때 `}}`가 붙지 않게 띄어 쓴다: `"={{ JSON.stringify({ draft: $json.draft }) }}"`
- HTTP 뒤 노드에서 웹훅 입력은 `$('Notice webhook').first().json.body`로 읽는다 (`$json`은 바로 앞 노드 결과).

## 8. 테스트 파일 (`cases/*.json`)

```json
{
  "webhook": "my-notice",
  "cases": [
    {"name": "연락처가 든 사실", "request": "requests/notice-phone.json",
     "expect": {"status": 200, "equals": {"published": true, "codes": []}, "contains": {"route": ["게시 가능"]},
                "not_contains": {"notice": ["010-1234-5678"]}}},
    {"name": "직접 쓴 요청", "body": {"facts": ""}, "expect": {"status": 400}},
    {"name": "다른 웹훅으로", "webhook": "my-reviewer", "body": {"facts": "...", "draft": "..."}, "expect": {"equals": {"passed": true}}}
  ]
}
```
- 필드 이름은 점으로 내려간다: `issues.0.code` = `issues` 첫 항목의 `code`.
- `equals`: 값이 같아야 함 · `contains`: 목록 중 **하나라도** 들어 있어야 함 (배열·객체는 JSON 글자로 바꿔 찾음) · `not_contains`: 하나도 없어야 함 · `status`: HTTP 코드(기본 200)
- `uv run tools/flow.py test <파일> -v --repeat 3`: LLM 답은 매번 조금씩 다르므로 3번 이상 돌려 본다. `-v`(`--verbose`)는 케이스마다 보낸 요청 JSON과 받은 응답 JSON을 화면에 보여 준다 (보고서 `runs/*.json`에도 같은 것이 남음).
- **테스트를 통과시키려고 테스트 파일의 기대 결과를 바꾸지 않는다.** 기대 결과가 틀렸다고 생각되면 사람에게 묻는다.

## 9. 하지 말 것

- `tools/`, `requests/`, `reference/`, 이 파일(`AGENTS.md`)을 고치지 않는다 (요청받은 경우만).
- 한 역할의 일을 다른 역할 안에서 다시 만들지 않는다 (공지 팀이 직접 초안을 쓰거나 검토하지 않고, 작성자·검토자를 부른다).
- n8n 컨테이너를 지우거나 `docker compose down`을 하지 않는다. `~/day65-n8n`(n8n 설치·비밀값)을 읽거나 고치지 않는다. Credential을 새로 만들지 않는다.
- `.env`나 API 키를 읽어서 출력하지 않는다.
