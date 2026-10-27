# AGENTS.md · n8n 모델·Prompt·Workflow 버전 관리 작업 규칙 (74일차 실습 폴더)

이 파일은 **CLI 코딩 에이전트**(Codex, Claude Code, Antigravity 등)가 이 폴더에서 n8n 워크플로우를 만들 때 따르는 규칙입니다. 사람도 읽을 수 있게 썼습니다. 73일차 규칙과 같고, 3절이 오늘 만드는 **버전이 붙은 헬프데스크 · 릴리스 점검의 계약**, 5절에 **릴리스 정보 · 지시문 저장소 · 기본 지시문 · 응답 코드로 가르기 · 카나리 · 점검 기록** 노드가 더해졌습니다.

## 1. 작업 순서 (항상 이 순서)

1. 요청을 읽고, 만들 워크플로우의 **입력 · 노드 순서 · 결과 모양**을 3~5줄로 먼저 정리해 보여 준다. 버전 요청이면 **무엇이 워크플로우 안에 남고, 무엇이 밖(데이터 API)으로 나가는지**도 함께 보여 준다.
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
| OpenAI Credential | id `openAiCourse0001`, name `OpenAI (.env)`. 모델 이름: `gpt-4.1-mini`, `gpt-5.4-nano` (같은 Credential) |
| 다른 Credential | 쓰지 않음 (Ollama 등 없음) |
| 데이터 API | n8n 안에서 `http://data-api:8800`, 터미널에서 `http://localhost:8800` (**74일차 판** `Last3Mon/74/data-api`: 73일차 + 지시문 저장소 + 릴리스 + 점검 기록 · 배포 정책) |
| 비교용 파일 | `reference/helpdesk-v1.json` (`rel-v1`), `reference/helpdesk-v2.json` (`rel-v2`), 고치지 않는다 |

### 데이터 API (74일차 판)

| 요청 | 응답 |
| --- | --- |
| `GET /prompts/helpdesk` | `{"name", "versions": ["p1", "p2", "p3"]}` |
| `GET /prompts/helpdesk/<버전>` | `{"name", "version", "text"}` (지시문 글자) · 없으면 **404** `{"error": "prompt not found"}` · 고장 스위치 `prompts`가 `error`면 **500**, `slow`면 8초 늦게 |
| `GET /releases/helpdesk` | `{"name", "active": "1.0.0", "canary": null \| {"release", "percent"}, "require_gate": false, "releases": {"1.0.0": {"prompt_version", "model", "note"}, ...}}` |
| `POST /releases/helpdesk` | `{"active": "1.1.0"}` · `{"canary": {"release": "1.1.0", "percent": 50}}` · `{"canary": null}` (**사람이** `flow.py release`로). 배포 정책이 켜져 있으면 마지막 점검 기록이 `promote`인 릴리스만, 아니면 **409** `{"error": "not gated", "release", "last_gate"}` |
| `POST /releases/helpdesk/policy` | `{"require_gate": true \| false}` (**사람이** `flow.py release helpdesk --require-gate on`) |
| `POST /releases/helpdesk/reset` | 처음 상태로 (active 1.0.0, 카나리 없음, 정책 꺼짐. 점검 기록은 남음) |
| `POST /gates/helpdesk` | 점검 기록 한 줄 `{"release", "verdict": "promote" \| "rollback", "passed", "total", "source", ...}` → `{"stored": true, "count"}` (Lab 03 과제 2, `flow.py gate`도 남김) |
| `GET /gates/helpdesk` · `POST /gates/helpdesk/clear` | `{"name", "gates": [{"t", ...}]}` · 비우기 `{"cleared"}` |
| `POST /admin/fault` | `{"prompts": "ok" \| "slow" \| "error"}` (`faq` · `tickets`도, 72일차와 같음) · `flow.py fault prompts error` |
| `GET /faq?q=` · `GET /tickets/<id>?requester=` · `/audit` | 72 · 73일차와 같음 |

| 릴리스 | 지시문 | 모델 | 내용 |
| --- | --- | --- | --- |
| 1.0.0 | p1 | gpt-4.1-mini | 첫 릴리스 |
| 1.1.0 | p2 | gpt-4.1-mini | FAQ 답 끝에 출처 번호 `[FAQ-003]` |
| 1.2.0 | p3 | gpt-4.1-mini | 답을 한 문장으로 짧게 |
| 2.0.0 | p2 | gpt-5.4-nano | 더 작은 모델 (모델만 바뀜) |
| 2.1.0 | **p9** | gpt-4.1-mini | 저장소에 없는 지시문을 가리킴 (Lab 02 과제 2의 망가진 릴리스) |

## 3. 오늘 만드는 것의 계약 (요청에 다른 말이 없으면 이대로)

| 무엇 | 파일 · 웹훅 | 입력 (본문) | 결과 |
| --- | --- | --- | --- |
| 헬프데스크 | `my-work/helpdesk.json` · `POST /webhook/my-helpdesk` (처음은 `reference/helpdesk-v1.json`을 복사) | `question`(필수), `user`, `release`(있으면 그 릴리스로 고정 — 후보 시험용) | `{"route", "answer", "sources", "version": {"release", "prompt_version", "model", "channel", "prompt_source"}}` |
| 릴리스 점검 | `my-work/release-check.json` · `POST /webhook/my-release-check` | `release`(필수) | `{"release", "passed", "total", "failed", "seconds", "verdict": "promote" \| "rollback"}` |

- `version.channel`: `stable`(active) · `canary`(카나리 대상) · `pinned`(본문 `release`로 고정). `version.prompt_source`: 지시문을 저장소에서 가져왔으면 `registry`, 저장소가 멈춰 기본 지시문으로 답했으면 `fallback`.
- 없는 릴리스를 고정하면 HTTP 400 `{"error": "unknown release", "release", "known": [...]}`.
- **저장소가 멈추면(500 · 2초 넘음) 기본 지시문으로 답한다** (Lab 01 과제 2). 기본 지시문은 p1과 같은 글을 워크플로우 안에 둔다.
- **저장소가 404면(릴리스가 없는 지시문을 가리킴) 기본 지시문으로 넘어가지 않고** HTTP 400 `{"error": "release broken", "release", "prompt_version"}` (Lab 02 과제 2).
- 릴리스 점검(Lab 03 과제 2): 판단 뒤 `POST http://data-api:8800/gates/helpdesk`에 기록하고 결과에 `recorded: true|false`. **워크플로우가 배포(`/releases`에 POST)하지 않는다.**
- **카나리 대상 규칙**: `user` 이름 글자 코드의 합 % 100 이 `percent`보다 작으면 카나리. 같은 사람은 늘 같은 쪽. (`flow.py release helpdesk`가 대상 직원을 보여 줌)
- 고정(`release`) > 카나리 > active 순서로 정한다.

## 4. 워크플로우 파일 규칙

```json
{
  "name": "74 IT helpdesk (my)",
  "nodes": [ ... ],
  "connections": { ... },
  "settings": { "executionOrder": "v1" }
}
```

- 파일 하나에 워크플로우 하나. 노드 `name`은 영어로, 겹치지 않게. 노드마다 `type`, `typeVersion`, `position`, `parameters`.
- **API 키를 JSON에 쓰지 않는다.** LLM 노드는 위 Credential id만 쓴다.
- 웹훅은 `POST`, `responseMode: "responseNode"`, 결과는 Respond to Webhook 노드로.
- 요청 본문은 `$json.body.question`처럼 `body` 아래. 다른 노드 뒤에서는 `$('Question webhook').first().json.body`.

## 5. 검증된 노드 (n8n 2.42.6에서 실행 확인)

### 릴리스 정보 (Set) · 모델 이름을 표현식으로
```json
{"name": "Release info", "type": "n8n-nodes-base.set", "typeVersion": 3.4, "position": [440, 300],
 "parameters": {"assignments": {"assignments": [
   {"id": "r1", "name": "release", "value": "1.0.0", "type": "string"},
   {"id": "r2", "name": "prompt_version", "value": "p1", "type": "string"},
   {"id": "r3", "name": "model", "value": "gpt-4.1-mini", "type": "string"}]}, "options": {}}}
```
```json
{"name": "Answer model", "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi", "typeVersion": 1.2, "position": [1100, 520],
 "parameters": {"model": {"__rl": true, "mode": "id", "value": "={{ $('Release info').first().json.model }}"}, "options": {"temperature": 0}},
 "credentials": {"openAiApi": {"id": "openAiCourse0001", "name": "OpenAI (.env)"}}}
```

### 지시문 저장소 (HTTP) → Agent의 systemMessage
```json
{"name": "Get prompt", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [660, 300],
 "parameters": {"url": "=http://data-api:8800/prompts/helpdesk/{{ $('Release info').first().json.prompt_version }}", "options": {}}}
```
```json
{"name": "Answer", "type": "@n8n/n8n-nodes-langchain.agent", "typeVersion": 3.1, "position": [1100, 300],
 "parameters": {"promptType": "define", "text": "=질문: {{ $('Question webhook').first().json.body.question }}\nFAQ: ...\n접수 건: ...",
   "options": {"systemMessage": "={{ $('Get prompt').first().json.text }}", "maxIterations": 1}}}
```

### 지시문 저장소가 멈추면 (Lab 01 과제 2)
- `Get prompt`에 `"options": {"timeout": 2000}`, 노드에 `"onError": "continueErrorOutput"`. `main`은 `[ [성공 쪽], [실패 쪽] ]`.
- 성공 쪽 `Registry prompt`(Set, `text` = `={{ $json.text }}`), 실패 쪽 `Fallback prompt`(Set, `text` = p1과 같은 글). 둘 다 `Search FAQ`로.
- 읽을 때: `"systemMessage": "={{ $('Registry prompt').isExecuted ? $('Registry prompt').first().json.text : $('Fallback prompt').first().json.text }}"`.

### 응답 코드로 가르기 (Lab 02 과제 2)
```json
{"name": "Get prompt", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [1320, 300], "onError": "continueErrorOutput",
 "parameters": {"url": "=http://data-api:8800/prompts/helpdesk/{{ $('Pick release').first().json.prompt_version }}",
   "options": {"timeout": 2000, "response": {"response": {"neverError": true, "fullResponse": true}}}}}
```
- `fullResponse`면 다음 노드가 `$json.statusCode` · `$json.body`를 받는다. `neverError`면 404 · 500도 성공 쪽으로 온다 (시간 초과만 실패 쪽).
- 다음 Code에서 `statusCode`가 200 · 404 · 그 밖으로 가르고, If(문자열 `equals`)로 400 갈래.

### 릴리스 고르기 (HTTP → Code → If)
```json
{"name": "Get release", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [440, 300],
 "parameters": {"url": "http://data-api:8800/releases/helpdesk", "options": {}}}
```
```json
{"name": "Pick release", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [660, 300],
 "parameters": {"jsCode": "const body = $('Question webhook').first().json.body;\nconst r = $json;\nlet release = r.active, channel = 'stable';\nif (body.release) { release = String(body.release); channel = 'pinned'; }\nconst info = r.releases?.[release];\n...\nreturn [{ json: { ok: Boolean(info), release, channel, prompt_version: info?.prompt_version, model: info?.model } }];"}}
```
- 이름 글자 코드의 합: `[...name].reduce((sum, ch) => sum + ch.codePointAt(0), 0) % 100`.

### HTTP로 내 웹훅 부르기 (릴리스 점검) — 항목마다 한 번
```json
{"name": "Ask helpdesk", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [660, 300],
 "parameters": {"method": "POST", "url": "http://localhost:5678/webhook/my-helpdesk", "sendBody": true, "specifyBody": "json",
   "jsonBody": "={{ JSON.stringify({ question: $json.question, user: $json.user, release: $json.release }) }}",
   "options": {"response": {"response": {"neverError": true}}, "timeout": 30000}}}
```
- 앞 Code가 항목 6개를 돌려주면 HTTP 노드가 항목마다 한 번씩 부른다. 다음 Code에서 `$input.all()`과 `$('Golden questions').all()`을 같은 순서로 맞춰 읽는다.

### 점검 기록 (Lab 03 과제 2)
```json
{"name": "Record gate", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [880, 300], "onError": "continueRegularOutput",
 "parameters": {"method": "POST", "url": "http://data-api:8800/gates/helpdesk", "sendBody": true, "specifyBody": "json",
   "jsonBody": "={{ JSON.stringify({ release: $json.release, verdict: $json.verdict, passed: $json.passed, total: $json.total, failed: $json.failed, source: 'my-release-check' }) }}",
   "options": {"timeout": 3000, "response": {"response": {"neverError": true}}}}}
```
- 기록이 실패해도 판단은 보낸다 (`continueRegularOutput`). 다음 Respond에서 `$('Judge').first().json`에 `recorded: $json.stored === true`를 더한다.

### 그 밖 (72 · 73일차와 같음)
- Webhook · If · Respond to Webhook · Search FAQ(HTTP `/faq`) · Get ticket(HTTP `/tickets`, `neverError`) · Code.
- 오류 응답: `"responseBody": "={{ JSON.stringify({ error: 'unknown release', release: $json.release, known: $json.known }) }}"`, `"options": {"responseCode": 400}`.

## 6. 연결 (`connections`)

```json
{
  "Known release?": {"main": [[{"node": "Get prompt", "type": "main", "index": 0}], [{"node": "Reject release", "type": "main", "index": 0}]]},
  "Answer model": {"ai_languageModel": [[{"node": "Answer", "type": "ai_languageModel", "index": 0}]]}
}
```
- 키는 **보내는 노드 이름**, 안의 `node`는 받는 노드 이름. If의 `main`은 `[ [true 쪽], [false 쪽] ]`.

## 7. 표현식 주의

- 표현식은 `=`로 시작한다. `{{ }}` 안에서 객체를 만들 때 `}}`가 붙지 않게 띄어 쓴다.
- 모델 이름 · 지시문을 표현식으로 읽을 때 앞 노드 이름이 정확해야 한다 (`$('Release info')`, `$('Pick release')`).

## 8. 테스트 파일 · 게이트

```json
{
  "webhook": "my-helpdesk",
  "before": [{"url": "http://localhost:8800/releases/helpdesk/reset", "body": {}}],
  "cases": [
    {"name": "후보 1.1.0", "body": {"question": "VPN ...", "user": "이준호", "release": "1.1.0"},
     "expect": {"equals": {"version.release": "1.1.0", "version.channel": "pinned"}, "contains": {"answer": ["[FAQ-003]"]}}},
    {"name": "배포 뒤", "before": [{"url": "http://localhost:8800/releases/helpdesk", "body": {"active": "1.1.0"}}],
     "request": "requests/faq-vpn.json", "expect": {"equals": {"version.channel": "stable"}}}
  ]
}
```
- `uv run tools/flow.py test <파일> -v --set release=1.1.0`: 모든 요청 본문에 `release`를 더한다 (후보 시험). `-v`는 케이스마다 요청 · 응답 JSON을 보여 준다. **모든 명령이 `-v`를 받는다** (73일차와 같음).
- `uv run tools/flow.py gate <파일> --set release=1.1.0 --min-pass 1.0 --max-p95 3`: 통과율과 p95로 PASS/FAIL (종료 코드 0/1). 결과를 `/gates/helpdesk`에 남긴다 (`--no-record`면 남기지 않음).
- `before` · `after` 단계에 `"status": 409`를 적으면 그 응답 코드를 기대한다 (예: 정책이 배포를 거절하는지).
- `--no-before`: 파일 맨 위 `before`를 건너뛴다 (Lab 03 예제 3, 카나리를 끈 뒤 다시 잴 때).
- `uv run tools/flow.py diff a.json b.json [--full]`: 두 워크플로우의 노드 · 설정 · 연결 차이.
- **테스트를 통과시키려고 테스트 파일의 기대 결과를 바꾸지 않는다.** 기대 결과가 틀렸다고 생각되면 사람에게 묻는다.

## 9. 하지 말 것

- `tools/`, `data-api/`, `requests/`, `reference/`, 이 파일(`AGENTS.md`)을 고치지 않는다 (요청받은 경우만). 지시문 파일(`data-api/data/prompts/`)과 `releases.json`은 사람이 정한다.
- 워크플로우 안에서 `/releases/...`에 POST 하지 않는다 (배포 · 되돌리기는 사람이 `flow.py release`로).
- n8n 컨테이너를 지우거나 `docker compose down`을 하지 않는다. `~/day65-n8n`(n8n 설치·비밀값)을 읽거나 고치지 않는다. Credential을 새로 만들지 않는다.
- `.env`나 API 키를 읽어서 출력하지 않는다.
