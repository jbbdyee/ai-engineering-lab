# AGENTS.md · n8n 사용량·비용 관리 작업 규칙 (75일차 실습 폴더)

이 파일은 **CLI 코딩 에이전트**(Codex, Claude Code, Antigravity 등)가 이 폴더에서 n8n 워크플로우를 만들 때 따르는 규칙입니다. 사람도 읽을 수 있게 썼습니다. 74일차 규칙과 같고, 3절이 오늘 만드는 **비용이 보이는 헬프데스크 · 비용 보고서의 계약**, 5절에 **토큰이 보이는 LLM 호출(HTTP) · 단가 · 사용량 기록 · 예산 · 한도 · 질문 길이 상한** 노드가 더해졌습니다.

## 1. 작업 순서 (항상 이 순서)

1. 요청을 읽고, 만들 워크플로우의 **입력 · 노드 순서 · 결과 모양**을 3~5줄로 먼저 정리해 보여 준다. 비용 요청이면 **LLM 호출이 몇 번, 어느 모델로, 무엇을 보내는지**도 함께 보여 준다.
2. 워크플로우 JSON을 `my-work/<이름>.json`에 쓴다. 이미 있으면 그 파일을 고친다 (새 파일을 만들지 않는다).
3. `uv run tools/flow.py check my-work/<이름>.json` → 오류(✘)가 없을 때까지 고친다.
4. 끝나면 한국어로 짧게 보고한다: 바꾼 노드, check 결과, 그리고 사람이 실행할 명령 두 줄.
   ```bash
   uv run tools/flow.py push my-work/<이름>.json
   uv run tools/flow.py test cases/<요청에 나온 테스트 파일>.json -v
   ```
5. **push와 test는 사람이 실행해 결과를 확인한다.** 사람이 "네가 push·test까지 해"라고 하면 직접 실행해도 된다 (push는 약 10초, n8n이 잠깐 재시작됨). **테스트는 실제 OpenAI 호출이라 돈이 든다.** 같은 테스트를 여러 번 반복하지 않는다.
6. 사람이 실패 보고서(`runs/*.json`)를 알려 주면 실패한 케이스의 요청·응답을 읽고 원인을 설명한 뒤 고친다. **같은 곳을 3번 고쳐도 실패하면 멈추고** 다른 방법을 제안한다.
7. 문서(`my-work/*.md`)를 써 달라는 요청이면 워크플로우를 만들지 않고 문서만 쓴다.

## 2. 환경 (바꾸지 말 것)

| 항목 | 값 |
| --- | --- |
| n8n | 2.42.6, 65일차 공식 설치 `~/day65-n8n` (Docker 프로젝트 `day65-n8n`, 컨테이너 보통 `day65-n8n-n8n-1`), 브라우저 http://localhost:5678 |
| n8n 켜고 끄기 | `~/aio-01d4-stu/Last3Mon/65/n8n`에서 `docker compose start/stop` (사람이 함, Ollama 컨테이너는 없음) |
| 게시된 웹훅 주소 | 밖에서 `http://localhost:5678/webhook/<path>` |
| OpenAI Credential | id `openAiCourse0001`, name `OpenAI (.env)`. 모델 이름: `gpt-4.1-mini`, `gpt-5.4-nano` (같은 Credential). `gpt-4.1-nano`는 OpenAI가 더 이상 받지 않음 |
| 다른 Credential | 쓰지 않음 (Ollama 등 없음) |
| 데이터 API | n8n 안에서 `http://data-api:8800`, 터미널에서 `http://localhost:8800` (**75일차 판** `Last3Mon/75/data-api`: 74일차 + 단가 · 사용량 기록 · 예산 · 한도) |
| 비교 기준 | `reference/baseline-cost.json` (웹훅 `base-cost`), `reference/lab02-example3-nano-answer.json` (웹훅 `nano-answer`). 고치지 않는다 |

### 데이터 API (75일차 판)

| 요청 | 응답 |
| --- | --- |
| `GET /prices` | `{"currency": "USD", "unit": "per 1M tokens", "models": {"gpt-4.1-mini": {"input": 0.4, "output": 1.6}, "gpt-5.4-nano": {"input": 0.2, "output": 1.25}}}` |
| `POST /usage` | 본문 `{"items": [{"request_id", "user", "step", "model", "prompt_tokens", "completion_tokens", "cost_usd", "route"}]}` (LLM 호출 하나에 항목 하나) → `{"stored": <항목 수>, "total"}` · 고장 스위치 `usage`가 `error`면 **500**, `slow`면 8초 뒤 **503**(저장하지 않음) |
| `GET /usage/summary` | `{"requests"(request_id 수), "calls", "prompt_tokens", "completion_tokens", "cost_usd", "by_model", "by_user", "by_route"}` (`by_*`마다 `calls` · `prompt_tokens` · `completion_tokens` · `cost_usd`) |
| `GET /usage/user/<이름>?window=60` | `{"user", "window", "count"}` — 그 사람의 최근 N초 요청 수 (이동 창) |
| `GET /budget` | `{"daily_usd", "used_usd", "remaining_usd", "over", "user_limit_per_min", "max_question_chars"}` (`used_usd`는 기록된 `cost_usd`의 합) |
| `POST /budget` · `/budget/reset` · `/usage-clear` | 예산 · 한도 바꾸기 · 처음으로(`data/budget.json`: $1.0 · 20번/분 · 500자) · 기록 비우기 (**사람이** `flow.py budget` · `usage --clear`로, 테스트가 `before` · `after`로) |
| `POST /admin/fault` | `{"usage": "ok" \| "slow" \| "error"}` (`faq` · `tickets` · `prompts`도) · `flow.py fault usage error` |
| `GET /faq?q=` · `GET /tickets/<id>?requester=` | 72~74일차와 같음 (접수 건에는 `assignee` · `contact`도 있음) |
| `/prompts` · `/releases` · `/gates` · `/audit` · `/cache` | 72~74일차와 같음 (오늘 쓰지 않음) |

## 3. 오늘 만드는 것의 계약 (요청에 다른 말이 없으면 이대로)

| 무엇 | 파일 · 웹훅 | 입력 (본문) | 결과 |
| --- | --- | --- | --- |
| 헬프데스크 | `my-work/cost.json` · `POST /webhook/my-cost` (처음은 `reference/baseline-cost.json`을 복사) | `question`(필수), `user` | `{"route", "answer", "sources", "llm_calls", "usage": {"prompt_tokens", "completion_tokens", "by_step": {"<단계>": {"model", "prompt_tokens", "completion_tokens", "cost_usd"}}}, "cost_usd", "recorded", "trimmed", "question_chars"}` |
| 비용 보고서 | `my-work/cost-report.json` · `POST /webhook/my-cost-report` | `requests_per_day`(없으면 지금 요청 수), `workdays`(기본 22), `what_if_model`(있으면) | `{"requests", "calls", "cost_usd", "avg_usd", "by_model": {"<모델>": cost}, "top_user", "projected_month_usd", "daily_budget_usd", "remaining_usd", "over_budget", "what_if": {"model", "cost_usd", "saving_usd", "projected_month_usd"}}` |

- `cost_usd` = Σ(입력 토큰 × input 단가 + 출력 토큰 × output 단가) / 1,000,000, 단계마다 **그 단계 모델의 단가**로. 단가는 **`/prices`에서** 읽는다 (워크플로우에 숫자를 쓰지 않는다). 소수 8자리에서 반올림.
- `route`: `자동 답변` · `한도 초과`(하루 예산을 넘음 — LLM 없이 FAQ · 접수 원문, `llm_calls` 0 · `cost_usd` 0) · `잠시 후`(사용자별 1분 한도를 넘음 — HTTP 429, `retry_after: 60`).
- `recorded`(Lab 01 과제 2): 기록 API가 `stored` ≥ 1을 돌려주면 true. 기록이 실패 · 3초 넘게 걸려도 **답은 그대로 보낸다.**
- `trimmed` · `question_chars`(Lab 02 과제 2): 질문이 `/budget`의 `max_question_chars`보다 길면 앞 `floor(상한 × 0.4)`자 + `' … '` + 뒤 나머지 글자만 LLM · FAQ 검색에 쓴다. `question_chars`는 원래 글자 수.
- 순서: 사용자별 한도(가장 앞) → 단가 · 질문 줄이기 → FAQ · 접수 조회 → 하루 예산 → 규칙 분류 → (모를 때만) LLM 분류 → 답 LLM → 기록.
- 비용 보고서의 금액은 소수 6자리에서 반올림 (반올림은 마지막에). `projected_month_usd = (cost_usd ÷ requests) × requests_per_day × workdays`. `top_user`는 비용이 가장 큰 사람. 보고서는 **LLM을 쓰지 않는다.**
- what-if: 기록된 모든 호출의 입력 · 출력 토큰 합을 `what_if_model`의 단가로 다시 계산. `saving_usd = cost_usd − what_if.cost_usd`. 단가표에 없는 모델이면 HTTP 400 `{"error": "unknown model", "model", "known": [...]}`. `what_if_model`이 없으면 `what_if`도 없다.

## 4. 워크플로우 파일 규칙

```json
{
  "name": "75 IT helpdesk (my)",
  "nodes": [ ... ],
  "connections": { ... },
  "settings": { "executionOrder": "v1" }
}
```

- 파일 하나에 워크플로우 하나. 노드 `name`은 영어로, 겹치지 않게. 노드마다 `type`, `typeVersion`, `position`, `parameters`.
- **API 키를 JSON에 쓰지 않는다.** OpenAI는 Credential id로만 부른다 (아래 5절의 `predefinedCredentialType`).
- 웹훅은 `POST`, `responseMode: "responseNode"`, 결과는 Respond to Webhook 노드로.
- 요청 본문은 `$json.body.question`처럼 `body` 아래. 다른 노드 뒤에서는 `$('Question webhook').first().json.body`.

## 5. 검증된 노드 (n8n 2.42.6에서 실행 확인)

### 토큰이 보이는 LLM 호출 — HTTP Request로 OpenAI를 직접
AI Agent 노드는 답 글자만 돌려주고 **토큰 수를 주지 않는다.** 오늘은 HTTP Request로 OpenAI를 불러 응답의 `usage`를 쓴다.
```json
{"name": "Answer", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [1320, 300],
 "parameters": {"method": "POST", "url": "https://api.openai.com/v1/chat/completions",
   "authentication": "predefinedCredentialType", "nodeCredentialType": "openAiApi",
   "sendBody": true, "specifyBody": "json",
   "jsonBody": "={{ JSON.stringify({ model: 'gpt-4.1-mini', temperature: 0, max_completion_tokens: 200, messages: [{ role: 'system', content: \"You are ...\" }, { role: 'user', content: '질문: ' + $('Question webhook').first().json.body.question }] }) }}",
   "options": {"timeout": 60000}},
 "credentials": {"openAiApi": {"id": "openAiCourse0001", "name": "OpenAI (.env)"}}}
```
- 결과: `$json.choices[0].message.content`(답 글자), `$json.usage.prompt_tokens`, `$json.usage.completion_tokens`.
- `max_completion_tokens`: 답(출력 토큰)의 상한. 너무 작으면 답이 잘린다. **`gpt-5.4-nano`는 `max_tokens`를 받지 않는다** (HTTP 400 `Unsupported parameter`). 두 모델 모두 `max_completion_tokens`로 쓴다 (`check`가 `max_tokens`를 찾아 알려 줌).
- 노드 이름을 단계 이름과 맞추면(`Classify` · `Answer` · `Review`) 마지막 Code에서 `$('Answer').first().json.usage`로 모으기 쉽다.

### 단가 · 예산 · 한도 (HTTP)
```json
{"name": "Get prices", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [440, 300], "parameters": {"url": "http://data-api:8800/prices", "options": {}}}
```
```json
{"name": "Get budget", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [440, 300], "parameters": {"url": "http://data-api:8800/budget", "options": {}}}
```
```json
{"name": "Recent requests", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [660, 300],
 "parameters": {"url": "=http://data-api:8800/usage/user/{{ encodeURIComponent($('Question webhook').first().json.body.user ?? '') }}?window=60", "options": {}}}
```

### 단계마다 비용 (Code)
```javascript
const prices = $('Get prices').first().json.models;
const p = prices[s.model] ?? { input: 0, output: 0 };
row.cost_usd = Math.round((row.prompt_tokens * p.input + row.completion_tokens * p.output) / 1e6 * 1e8) / 1e8;
```

### 사용량 기록 (HTTP POST, 항목 여러 개)
```json
{"name": "Record usage", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [2000, 300],
 "parameters": {"method": "POST", "url": "http://data-api:8800/usage", "sendBody": true, "specifyBody": "json",
   "jsonBody": "={{ JSON.stringify({ items: Object.entries($json.usage.by_step).map(([step, row]) => ({ request_id: $execution.id, user: $('Question webhook').first().json.body.user ?? '', step, model: row.model, prompt_tokens: row.prompt_tokens, completion_tokens: row.completion_tokens, cost_usd: row.cost_usd, route: $json.route })) }) }}",
   "options": {"response": {"response": {"neverError": true}}}}}
```
- `$execution.id`: 이번 실행의 번호 (한 요청의 여러 LLM 호출을 묶는 `request_id`).
- `neverError`면 기록 API의 4xx · 5xx 응답도 성공 쪽으로 온다. 시간 초과 · 연결 실패는 노드 설정 `onError`로 다룬다 (노드 바로 아래, `parameters` 밖).
- 기록 노드 다음에는 결과를 다시 꺼내 응답한다: `return [{ json: $('Build result').first().json }];`

### 429 응답
```json
{"name": "Too many", "type": "n8n-nodes-base.respondToWebhook", "typeVersion": 1.1, "position": [1100, 820],
 "parameters": {"respondWith": "json", "responseBody": "={{ JSON.stringify({ route: '잠시 후', answer: '...', retry_after: 60, llm_calls: 0, cost_usd: 0 }) }}", "options": {"responseCode": 429}}}
```

### 그 밖 (72~74일차와 같음)
- Webhook · If · Code · Search FAQ(HTTP `/faq`, 쿼리 `q`) · Get ticket(HTTP `/tickets`, `neverError`) · Respond to Webhook.
- 지나가지 않았을 수 있는 노드는 `$('노드').isExecuted`로 확인한 뒤 읽는다 (규칙으로 분류를 건너뛸 때): `const ran = (n) => { try { return $(n).isExecuted; } catch (e) { return false; } };`
- 오류 응답: `"responseBody": "={{ $json }}"`, `"options": {"responseCode": 400}`. Code 노드는 HTTP 상태를 정하지 못하므로 If로 갈라 Respond로.

## 6. 연결 (`connections`)

```json
{
  "Within budget?": {"main": [[{"node": "Rule classify", "type": "main", "index": 0}], [{"node": "Over budget", "type": "main", "index": 0}]]},
  "Answer": {"main": [[{"node": "Build result", "type": "main", "index": 0}]]}
}
```
- 키는 **보내는 노드 이름**, 안의 `node`는 받는 노드 이름. If의 `main`은 `[ [true 쪽], [false 쪽] ]`.
- HTTP로 부르는 LLM은 보통 노드라 `main`으로 잇는다 (`ai_languageModel` 아님).

## 7. 표현식 주의

- 표현식은 `=`로 시작한다. `JSON.stringify({ ... })` 안의 글자에 `'`가 있으면 깨지기 쉽다 — 지시문은 `"`로 감싸거나 앞 노드(Set)에 두고 읽는다. `{{ }}` 안에서 객체를 만들 때 `}}`가 붙지 않게 띄어 쓴다.
- 숫자 계산은 Code에서. 반올림: `Math.round(x * 1e8) / 1e8` (보고서는 `1e6`).

## 8. 테스트 파일 (`cases/*.json`)

```json
{
  "webhook": "my-cost",
  "before": [{"url": "http://localhost:8800/usage-clear", "body": {}}],
  "cases": [
    {"name": "VPN · 비용 상한", "request": "requests/faq-vpn.json",
     "expect": {"equals": {"llm_calls": 1}, "range": {"cost_usd": [0.000001, 0.0002]}, "contains": {"answer": ["인증서"]}}},
    {"name": "요약 확인", "url": "http://localhost:8800/usage/summary", "body": {}, "expect": {"equals": {"requests": 1}}}
  ]
}
```
- `range`: 숫자가 `[최소, 최대]` 안. `url`: 웹훅 대신 그 주소에 POST (데이터 API 확인용).
- `equals` · `contains` · `not_contains` · `status` · `max_seconds`, `before` · `after`는 72~74일차와 같다. 점이 들어간 키(`gpt-4.1-mini`)는 경로로 못 읽으니 `contains`로 JSON 글자를 찾는다.
- 줄 끝의 `· 자동 답변 · 1 call · $0.000156`은 결과의 `route` · `llm_calls` · `cost_usd`다.
- `uv run tools/flow.py test <파일> -v`: 케이스마다 요청 · 응답 JSON. `--webhook nano-answer`: 같은 파일을 다른 웹훅에. **모든 명령이 `-v`를 받는다** (74일차와 같음).
- `uv run tools/flow.py usage [--clear]` · `budget [--daily 0.001] [--per-min 2] [--chars 2000] [--reset]` · `fault usage error|slow|ok` (사람이).
- **테스트를 통과시키려고 테스트 파일의 기대 결과를 바꾸지 않는다.** 기대 결과가 틀렸다고 생각되면 사람에게 묻는다.

## 9. 하지 말 것

- `tools/`, `data-api/`, `requests/`, `reference/`, 이 파일(`AGENTS.md`)을 고치지 않는다 (요청받은 경우만). 단가(`prices.json`) · 예산(`budget.json`)은 사람이 정한다.
- 워크플로우 안에서 `/budget`, `/usage-clear`, `/admin/fault`에 POST 하지 않는다 (예산 · 기록 비우기 · 고장 스위치는 사람이).
- 비용을 줄이려고 **답의 내용 검사(테스트의 `contains`)를 없애지 않는다.** 단가를 워크플로우에 숫자로 쓰지 않는다.
- n8n 컨테이너를 지우거나 `docker compose down`을 하지 않는다. `~/day65-n8n`(n8n 설치·비밀값)을 읽거나 고치지 않는다. Credential을 새로 만들지 않는다.
- `.env`나 API 키를 읽어서 출력하지 않는다.
