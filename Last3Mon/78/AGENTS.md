# AGENTS.md · n8n 데이터 품질 검사 작업 규칙 (78일차 실습 폴더)

이 파일은 **CLI 코딩 에이전트**(Codex, Claude Code, Antigravity 등)가 이 폴더에서 n8n 워크플로우를 만들 때 따르는 규칙입니다. 사람도 읽을 수 있게 썼습니다. 77일차 규칙과 같고, 3절에 오늘 만드는 **검사 · 가져오기 · 스키마 검사 · 품질 보고서의 계약**과 **품질 규칙(오류 코드)**, 5절에 검사 · 격리 노드가 더해졌습니다.

## 1. 작업 순서 (항상 이 순서)

1. 요청을 읽고, 만들 워크플로우의 **입력 · 노드 순서 · 결과 모양**을 3~5줄로 먼저 정리해 보여 준다. 규칙 요청이면 **규칙(무엇을 보고 어떤 코드를 붙이는지)** 을 먼저 표로 보여 준다.
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
| 데이터 API | n8n 안에서 `http://data-api:8800`, 터미널에서 `http://localhost:8800` (**78일차 판** `Last3Mon/78/data-api`: 77일차 + 격리함 · 스키마 · 품질 기록) |
| 비교 기준 · 제공 | `reference/baseline-faq-check.json` (`base-faq-check`, 팀이 지난달 급히 만든 검사 — 빈 값만 봄) · `reference/baseline-faq-import.json` (`base-faq-import`, 모든 줄을 그대로 넣던 가져오기). **고치지 않는다** (비교용) |

### 데이터 API (78일차 판, 오늘 쓰는 것)

| 요청 | 응답 |
| --- | --- |
| `GET /faq-all` | `{"count", "faqs": [{"id", "title", "keywords", "answer"}]}` — 지금 FAQ 전체 (처음 6개 + 더한 것) |
| `POST /faq/add` 본문 `{"id", "title", "keywords", "answer"}` | FAQ 한 줄 더하기 (같은 id면 바꿈) |
| `POST /quarantine` 본문 `{"items": [{"batch", "row": {...}, "errors": [...]}]}` | 격리함에 넣기. 같은 배치 · 같은 줄 id(`row.id`, 없으면 `row.email`, `row.ticket_id`)면 바꿈 |
| `GET /quarantine` (`POST /quarantine/list`) | `{"size", "items": [{"row_id", "batch", "row", "errors", "at"}]}` |
| `POST /quarantine/remove` 본문 `{"ids": ["FAQ-209"]}` | 격리함에서 빼기 |
| `GET /schemas` (`POST /schemas/list`) | `{"schemas": ["employee", "faq", "ticket"]}` |
| `GET /schemas/<name>` | 데이터 스키마 `{"name", "key", "fields"}`, 없으면 404 |
| `POST /quality-log` 본문 `{"batch", "dataset", "total", "valid", "quarantined", "rejected", "score", "codes"}` | 품질 기록 한 줄 |
| `GET /quality-log` (`POST /quality-log/list`) | `{"count", "items": [...]}` 넣은 순서 |
| `POST /alerts` · `GET /alerts` | 알림 (76일차와 같음) |
| `POST /faq-reset` · `/quarantine-clear` · `/quality-log-clear` · `/alerts-clear` | 처음으로 (**사람이** · 테스트가, `flow.py quality --reset`) |

### 배치 (오늘 들어오는 데이터)

```json
{"batch": "B-2", "items": [{"id": "FAQ-201", "title": "회의실 예약", "keywords": ["회의실", "예약"], "answer": "사내 포털의 ..."}]}
```
- `requests/faq-batch-1.json`(13줄) · `faq-batch-2.json`(10줄) · `faq-batch-3.json`(6줄) · `faq-batch-2-fixed.json`(고친 2줄) · `faq-edges.json`(경계 10줄) · `faq-batch-1-loose.json` · `faq-batch-2-limit-0.1.json` · `faq-batch-2-strict.json`(같은 배치 + `max_invalid_ratio`).
- `employees-new.json`(CSV 9줄, `{"schema": "employee", "batch", "csv"}`) · `tickets-new.json`(목록 9줄, `{"schema": "ticket", "batch", "items"}`).

## 3. 오늘 만드는 것의 계약과 품질 규칙

| 무엇 | 파일 · 웹훅 | 입력 (본문) | 결과 |
| --- | --- | --- | --- |
| FAQ 검사 | `my-work/faq-check.json` · `POST /webhook/my-faq-check` | 배치 | `{"batch", "total", "valid", "invalid", "rows": [{"id", "ok", "errors", "warnings"}], "codes"}`, `items`가 목록이 아니면 **400**. (Lab 01 과제 2) `fix_list` · `message` 더함 |
| FAQ 가져오기 | `my-work/faq-import.json` · `POST /webhook/my-faq-import` | 배치 (+ 선택 `max_invalid_ratio`, 기본 0.3) | `{"batch", "total", "imported", "quarantined", "rejected", "score", "max_invalid_ratio", "codes", "imported_ids", "quarantined_ids"}`, 배치를 거절하면 **422** `{"error": "batch rejected", "batch", "invalid_ratio", "max_invalid_ratio", "codes"}`. (Lab 02 과제 2) 둘 다 `llm_calls` 더함 |
| 스키마 검사 | `my-work/check.json` · `POST /webhook/my-check` | `{"schema", "batch", "items"}` 또는 `{"schema", "batch", "csv"}` | `{"schema", "batch", "total", "valid", "invalid", "rows": [{"row", "key", "ok", "errors"}], "codes"}`, 모르는 스키마면 **400**. (Lab 03 과제 2) 검사마다 품질 기록 한 줄 |
| 품질 보고서 | `my-work/quality-report.json` · `POST /webhook/my-quality-report` | `{"dataset"}`(선택) | 아래 |

### FAQ 품질 규칙 (오류 코드)

| 코드 | 규칙 |
| --- | --- |
| `id_format` | `id`가 `FAQ-` + 숫자 3자리가 아님 |
| `title_missing` · `title_too_long` | 제목이 비었음 · 40자 넘음 |
| `keywords_missing` | 키워드가 목록이 아니거나 비었음 |
| `answer_missing` · `answer_too_short` · `answer_too_long` | 답이 비었음 · 10자 미만 · 300자 넘음 |
| `duplicate_in_batch` | 같은 배치 안에서 앞에 나온 `id` (두 번째부터) |
| `pii` | 답에 휴대전화 번호(`010-1234-5678` · `01012345678` 꼴, `-` · `.` · 공백 없어도) 또는 메일 주소. 사무실 번호(`02-123-4567`)는 아님 |
| `external_link` | 답에 `http(s)://` 링크가 있는데 호스트가 **정확히** `intra.example.com`이 아님 (`intra.example.com.evil.io`는 바깥) |
| `exists_id` · `same_title` | (Lab 01 과제) 이미 있는 FAQ와 `id` · 제목이 같음 |
| `keyword_used:<낱말>` | (Lab 01 과제, **경고**) 이미 있는 FAQ가 쓰는 키워드 — 통과는 시킴 |
| `llm_mismatch` | (Lab 02) 규칙은 통과했지만 LLM이 "답이 제목의 질문에 답하지 않음"으로 판정 |

- 줄은 `errors`가 비었을 때만 `ok`. `warnings`는 통과에 영향이 없다.
- 공백만 있는 값은 빈 값으로 본다. 글자 수는 앞뒤 공백을 뺀 뒤 센다 (제목 40자 · 답 10자는 통과).

### 고침 목록 (Lab 01 과제 2)

| 필드 | 정의 |
| --- | --- |
| `fix_list` | 통과하지 못한 줄만 줄 순서대로 `[{"row" (1부터), "id", "codes" (그 줄의 errors), "fix": [코드마다 아래 말]}]` |
| `message` | `"<batch>: <total>줄 중 <valid>줄 통과, <invalid>줄 고칠 것"` |

| 코드 | `fix`의 말 |
| --- | --- |
| `id_format` | id를 FAQ-숫자 3자리로 (예: FAQ-104) |
| `title_missing` · `title_too_long` | 제목을 써 주세요 · 제목을 40자 이내로 줄여 주세요 |
| `keywords_missing` | 키워드를 하나 이상 넣어 주세요 |
| `answer_missing` · `answer_too_short` · `answer_too_long` | 답을 써 주세요 · 답을 10자 이상으로 써 주세요 · 답을 300자 이내로 줄여 주세요 |
| `duplicate_in_batch` | 같은 배치에 같은 id가 또 있습니다. 하나만 남겨 주세요 |
| `pii` | 개인 전화번호 · 메일 주소를 빼고 IT 포털 안내로 바꿔 주세요 |
| `external_link` | 바깥 링크 대신 사내 주소(intra.example.com)를 써 주세요 |
| `exists_id` | 이미 있는 id입니다. 새 id를 쓰거나, 고치려는 것이면 FAQ 담당자에게 알려 주세요 |
| `same_title` | 같은 제목의 FAQ가 이미 있습니다. 제목을 바꾸거나 기존 FAQ와 합쳐 주세요 |

### 가져오기 게이트

| 단계 | 규칙 |
| --- | --- |
| 배치 게이트 | `invalid / total`이 **기준을 넘으면** 배치 전체를 거절 (422, 아무것도 넣지 않음). 기준은 본문의 `max_invalid_ratio`, 없으면 **0.3**. 같으면 통과. 응답에 쓴 기준 `max_invalid_ratio`를 함께, `invalid_ratio`는 소수 4자리 |
| 줄 게이트 | 통과한 줄만 `/faq/add`, 나머지는 **이유와 함께** `/quarantine` |
| LLM 검사 (Lab 02 예제 2) | 규칙을 통과한 줄만 LLM에게 (비용 · 75일차) |
| `score` | `imported / total`, 소수 4자리 (거절된 배치는 0) |
| `llm_calls` (Lab 02 과제 2) | LLM 검사에 보낸 줄 수 (= 규칙을 통과한 줄 수). 거절된 배치는 0 |
| 품질 기록 · 알림 (Lab 02 과제) | 배치마다 `/quality-log` 한 줄 (거절도), 거절이면 알림 `reason: "batch_rejected"`, `score < 0.9`면 알림 `reason: "low_quality"` |

### 스키마 (`/schemas/<name>`)

```json
{"name": "employee", "key": "email", "fields": {
  "name": {"type": "string", "required": true, "max": 20},
  "dept": {"type": "enum", "required": true, "values": ["영업팀", "재무팀", "인사팀", "개발팀", "IT팀", "총무팀"]},
  "email": {"type": "email", "required": true}, "phone": {"type": "phone", "required": false}, "joined": {"type": "date", "required": true}}}
```

| 타입 | 확인 | 코드 |
| --- | --- | --- |
| 모든 필드 | `required`인데 비었음 | `missing:<필드>` |
| `string` | `min` · `max` 글자 수 | `too_short:<필드>` · `too_long:<필드>` |
| `enum` | `values` 안에 있나 | `not_allowed:<필드>` |
| `email` · `phone` · `date` · `pattern` | 형식 (`0\d{1,2}-\d{3,4}-\d{4}`, 실제 있는 날짜 `YYYY-MM-DD`, 스키마의 정규식) | `bad_format:<필드>` |
| `list` | 목록인가, `min_items` · `max_items` | `bad_format` · `too_few` · `too_many:<필드>` |
| 키 (`key`) | 배치 안에서 두 번째부터 | `duplicate_in_batch` |

- CSV는 첫 줄이 열 이름, 쉼표로 나눔 (따옴표 없음). `row`는 1부터 (열 이름 줄 제외).

### 품질 보고서 (`my-quality-report`)

| 필드 | 정의 |
| --- | --- |
| `count` · `batches` | 품질 기록 줄 수 · `[{"batch", "score", "rejected", "total"}]` 넣은 순서 (`dataset`을 주면 그 데이터셋만) |
| `avg_score` | `score` 평균, 소수 4자리 (0건이면 0) |
| `worst_batch` | `score`가 가장 낮은 배치 (같으면 먼저 나온 것, 없으면 `null`) |
| `rejected_batches` | 거절된 배치 수 |
| `top_codes` | 모든 기록의 `codes`를 더해 `[{"code", "count"}]`, 많은 순 (같으면 코드 글자순) |
| `trend` | 마지막 `score` − 첫 `score`가 0.05 넘으면 `좋아짐`, −0.05 미만이면 `나빠짐`, 아니면(또는 1건 이하) `그대로` |
| `by_dataset` (Lab 03 과제 2) | 모든 기록을 `dataset`마다 `{"count", "avg_score", "worst_batch", "top_code"}` (처음 나온 순서, `top_code`는 `top_codes`의 첫 코드 또는 `null`) |
| `worst_dataset` (Lab 03 과제 2) | `avg_score`가 가장 낮은 데이터셋 (같으면 먼저 나온 것, 없으면 `null`) |

### 검사도 기록 (Lab 03 과제 2)

- `my-check`는 검사가 끝나면 `/quality-log`에 한 줄: `{"batch", "dataset": <schema>, "total", "valid", "quarantined": invalid, "rejected": false, "score": valid / total (소수 4자리, 0줄이면 0), "codes"}`. 응답은 검사 결과 그대로.

## 4. 워크플로우 파일 규칙

```json
{"name": "78 FAQ check (my)", "nodes": [ ... ], "connections": { ... }, "settings": { "executionOrder": "v1" }}
```

- 파일 하나에 워크플로우 하나. 노드 `name`은 영어로, 겹치지 않게. **API 키를 JSON에 쓰지 않는다.**
- **규칙은 Code가 확인한다.** LLM은 규칙으로 알 수 없는 것(답이 질문에 맞나)만, 규칙을 통과한 줄에만.
- 검사 결과의 `rows`는 들어온 줄과 **같은 순서 · 같은 수**.

## 5. 검증된 노드 (n8n 2.42.6에서 실행 확인)

### 본문 확인 (IF) → 줄마다 규칙 (Code)
```json
{"name": "Is a list?", "type": "n8n-nodes-base.if", "typeVersion": 2.2, "position": [220, 300],
 "parameters": {"conditions": {"options": {"caseSensitive": true, "leftValue": "", "typeValidation": "loose", "version": 2},
   "conditions": [{"id": "c1", "leftValue": "={{ Array.isArray($json.body.items) }}", "rightValue": "",
     "operator": {"type": "boolean", "operation": "true", "singleValue": true}}], "combinator": "and"}, "options": {}}}
```
```json
{"name": "Check rows", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [440, 300],
 "parameters": {"jsCode": "const body = $('Check webhook').first().json.body;\nconst seen = new Set();\nconst rows = body.items.map((r) => {\n  const errors = [];\n  ...\n  return { id: String(r?.id ?? ''), ok: errors.length === 0, errors, warnings: [] };\n});\n...\nreturn [{ json: { batch: body.batch ?? '', total: rows.length, valid, invalid: rows.length - valid, rows, codes } }];"}}
```

### 다른 내 웹훅을 부르기 (가져오기 → 검사)
```json
{"name": "Run check", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [220, 300],
 "parameters": {"method": "POST", "url": "http://localhost:5678/webhook/my-faq-check", "sendBody": true, "specifyBody": "json",
   "jsonBody": "={{ JSON.stringify($json.body) }}", "options": {"timeout": 30000, "response": {"response": {"neverError": true}}}}}
```
- 400 · 422도 오류로 멈추지 않고 본문을 받는다 (`neverError`). 다음 IF에서 `Array.isArray($json.rows)`로 갈라 본다.

### 줄을 나눠 저장하기 — 한 줄로 (분기 없이)
```json
{"name": "Store row", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [1320, 300],
 "parameters": {"method": "POST", "url": "={{ $json.ok ? 'http://data-api:8800/faq/add' : 'http://data-api:8800/quarantine' }}",
   "sendBody": true, "specifyBody": "json",
   "jsonBody": "={{ JSON.stringify($json.ok ? $json.row : { items: [{ batch: $json.batch, row: $json.row, errors: $json.errors }] }) }}",
   "options": {"response": {"response": {"neverError": true}}}}}
```
- 앞의 Code가 줄마다 아이템 하나(`{id, ok, errors, row, batch}`)를 내면 HTTP 노드는 **아이템마다** 한 번씩 부른다. 주소를 표현식으로 고르면 IF로 갈라 다시 합칠(Merge) 필요가 없다.
- 그 뒤 요약 Code는 `$('Decide').all()`처럼 **저장 전 노드**에서 줄을 다시 읽는다 (HTTP 노드의 출력은 API 응답이다).
- 수업 준비 때: IF로 두 갈래(넣기 · 격리)로 나눴다가 Merge로 합치니, LLM 검사를 더한 뒤 격리 갈래가 두 번 실행되면서 `$('Bad rows').all()`이 **마지막 실행만** 보여 격리 수가 틀렸다. 한 줄로 바꿔 해결.

### LLM 검사 (규칙을 통과한 줄만)
- `Only passed`(Code: `return $input.all().filter((i) => i.json.ok);`) → AI Agent(`Judge`) + OpenAI chat model → `Decide`(Code).
- 지시문: `{"match": true|false, "reason"}` JSON만. `Decide`는 `$('Judge').all()[i]`를 `Only passed`의 i번째 줄과 맞추고, 읽을 수 없으면 `match: false`.
- Agent의 `onError`는 `continueRegularOutput` (LLM 오류여도 그 줄을 격리로 보내고 계속).

## 6. 연결 · 7. 표현식

- 72~77일차와 같다. 다른 노드 뒤에서 웹훅 입력은 `$('Import webhook').first().json.body`.
- 테스트에서 목록 안은 숫자로 내려간다: `rows.2.errors`, `items.1.score`, `top_codes.0.code`.

## 8. 테스트 파일 (`cases/*.json`)

```json
{"webhook": "my-faq-import", "before": [{"url": "http://localhost:8800/faq-reset", "body": {}}], "cases": [
  {"name": "나쁜 배치는 통째로 거절", "request": "requests/faq-batch-1.json", "expect": {"status": 422}},
  {"name": "격리함", "url": "http://localhost:8800/quarantine/list", "body": {}, "expect": {"contains": {"items": "\"pii\""}}}
]}
```
- `before`의 `"allow_fail": true`: 일부러 거절되는 배치를 미리 넣을 때 (Lab 03 과제).
- 기대 결과는 3절 규칙대로 배치 파일을 확인한 값입니다. **테스트를 통과시키려고 기대 결과나 배치 파일을 바꾸지 않는다.** 규칙이 다르다고 생각되면 사람에게 묻는다.

## 9. 하지 말 것

- `tools/`, `data-api/`(스키마 포함), `requests/`, `reference/`, 이 파일을 고치지 않는다 (요청받은 경우만).
- 워크플로우 안에서 `/faq-reset` · `/quarantine-clear` · `/quality-log-clear` · `/alerts-clear` · 고장 스위치를 부르지 않는다.
- 나쁜 줄을 고쳐서(빈 제목을 채우는 등) 넣지 않는다. **고치는 것은 사람**, 워크플로우는 막고 알린다.
- n8n 컨테이너를 지우거나 `docker compose down`을 하지 않는다. `~/day65-n8n`을 읽거나 고치지 않는다. Credential을 새로 만들지 않는다. `.env`나 API 키를 출력하지 않는다.
