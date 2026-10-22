# AGENTS.md · n8n RAG(검색·응답) 작업 규칙 (71일차 실습 폴더)

이 파일은 **CLI 코딩 에이전트**(Codex, Claude Code, Antigravity 등)가 이 폴더에서 n8n 워크플로우를 만들 때 따르는 규칙입니다. 사람도 읽을 수 있게 썼습니다. 70일차 규칙과 같고, 3절이 오늘 만드는 **색인 · 검색 · 규정 Q&A의 계약**, 5절에 **벡터 저장소 · 임베딩 노드**가 더해졌습니다.

## 1. 작업 순서 (항상 이 순서)

1. 요청을 읽고, 만들 워크플로우의 **입력 · 노드 순서 · 결과 모양**을 3~5줄로 먼저 정리해 보여 준다. RAG면 **문서 → 청크 → 검색 → 답** 각 단계의 입력·결과도 함께 보여 준다.
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
| 데이터 API | n8n 안에서 `http://data-api:8800`, 터미널에서 `http://localhost:8800` (**71일차 판** `Last3Mon/71/data-api`: FAQ · 접수 현황 · 규정 문서) |
| 임베딩 | OpenAI `text-embedding-3-large` (같은 Credential) |
| 벡터 저장소 | n8n **메모리** 저장소, 이름(memoryKey) `my_policy_docs`. **n8n이 재시작되면(push 할 때마다) 지워진다** → 색인을 다시 (`call my-index`) |

## 3. 오늘 만드는 것의 계약 (요청에 다른 말이 없으면 이대로)

| 무엇 | 파일 · 웹훅 | 입력 (본문) | 결과 |
| --- | --- | --- | --- |
| 색인 | `my-work/index.json` · `POST /webhook/my-index` | `chunking`: `"section"`(기본) 또는 글자 수(숫자) | `{"indexed_chunks", "chunking"}` |
| 검색 | `my-work/search.json` · `POST /webhook/my-search` | `question`(필수), `top_k`(기본 3) | `{"question", "hits": [{"rank", "source", "title", "score", "text"}], "top_score", "indexed"}` |
| 규정 Q&A | `my-work/policy-qa.json` · `POST /webhook/my-policy-qa` | `question`(필수), `min_score`(기본 0.33) | `{"route", "answer", "sources", "cited", "top_score"}` |

- 규정 문서: `GET /docs` → `{"docs": [{"name", "title"}]}` 8개, `GET /docs/<name>` → `{"name", "title", "text"}` (마크다운, `## ` 섹션). `name`이 `source`가 된다 (예: `password-policy`).
- `route`: `자동 답변` 또는 `담당자 연결`. 답 안의 출처는 문서 제목 `[비밀번호·계정 보안 규정]`처럼 보여 준다. `cited`는 답이 실제로 인용한 문서 `name` 목록.
- 관련도 기준: 검색 1등 점수(`top_score`)가 `min_score`보다 낮으면 LLM을 부르지 않고 `담당자 연결` (수업 준비 측정: 규정 질문 0.46~0.62, 규정 밖 0.20~0.26).

## 4. 워크플로우 파일 규칙

```json
{
  "name": "71 Policy QA (my)",
  "nodes": [ ... ],
  "connections": { ... },
  "settings": { "executionOrder": "v1" }
}
```

- 파일 하나에 워크플로우 하나. `id`는 쓰지 않아도 된다 (`push`가 파일 이름으로 정한다).
- 노드 `name`은 영어로, 워크플로우 안에서 겹치지 않게. 노드마다 `type`, `typeVersion`, `position: [x, y]`, `parameters`가 필요하다.
- **API 키를 JSON에 쓰지 않는다.** LLM 노드는 위 Credential id만 쓴다.
- 웹훅은 `POST`, `responseMode: "responseNode"`, 결과는 Respond to Webhook 노드로 보낸다.
- 요청 본문은 `$json.body.question`처럼 `body` 아래에 있다.

## 5. 검증된 노드 (n8n 2.42.6에서 실행 확인)

아래 `type`/`typeVersion`을 그대로 쓴다. 다른 노드가 필요하면 써도 되지만 `flow.py check`가 이 n8n에 있는지 확인한다.

### Webhook · If · Respond to Webhook
```json
{"name": "Question webhook", "type": "n8n-nodes-base.webhook", "typeVersion": 2, "position": [0, 300],
 "parameters": {"httpMethod": "POST", "path": "my-policy-qa", "responseMode": "responseNode", "options": {}}}
```
```json
{"name": "Has question?", "type": "n8n-nodes-base.if", "typeVersion": 2.2, "position": [200, 300],
 "parameters": {"conditions": {"options": {"caseSensitive": true, "leftValue": "", "typeValidation": "strict", "version": 2},
   "conditions": [{"id": "c1", "leftValue": "={{ $json.body.question }}", "rightValue": "",
     "operator": {"type": "string", "operation": "notEmpty", "singleValue": true}}], "combinator": "and"}, "options": {}}}
```
- If 출력 0번이 true, 1번이 false. 조건을 둘 넣으면 `combinator: "and"`. 불리언은 `"leftValue": "={{ $json.passed }}", "operator": {"type": "boolean", "operation": "true", "singleValue": true}`.
```json
{"name": "Send result", "type": "n8n-nodes-base.respondToWebhook", "typeVersion": 1.1, "position": [2600, 300],
 "parameters": {"respondWith": "json", "responseBody": "={{ $json }}", "options": {}}}
```
- 오류 응답: `"responseBody": "{ \"error\": \"question is required\" }"`, `"options": {"responseCode": 400}`

### HTTP Request · Split Out (문서 가져오기)
```json
{"name": "List docs", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [200, 300], "parameters": {"url": "http://data-api:8800/docs", "options": {}}}
```
```json
{"name": "One item per doc", "type": "n8n-nodes-base.splitOut", "typeVersion": 1, "position": [400, 300], "parameters": {"fieldToSplitOut": "docs", "options": {}}}
```
```json
{"name": "Get doc", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [600, 300], "parameters": {"url": "=http://data-api:8800/docs/{{ $json.name }}", "options": {}}}
```

### Code (청크 만들기 · 결과 모양)
```json
{"name": "Make chunks", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [800, 300],
 "parameters": {"jsCode": "const chunks = [];\nfor (const item of $input.all()) {\n  const { name, title, text } = item.json;\n  text.split(/\\n(?=## )/).slice(1).forEach((piece, i) => chunks.push({ json: { source: name, title, chunk: i + 1, text: `${title}\\n${piece}` } }));\n}\nreturn chunks;"}}
```
- 여러 항목을 돌려주면 다음 노드가 항목마다 처리한다. 청크 글 앞에 문서 제목을 붙이면 검색이 문서를 더 잘 찾는다.
- Code 노드 안에는 `URL` 클래스가 없다.

### Vector Store (메모리) · Embeddings · Loader — 색인
```json
{"name": "Store chunks", "type": "@n8n/n8n-nodes-langchain.vectorStoreInMemory", "typeVersion": 1.3, "position": [1020, 300],
 "parameters": {"mode": "insert", "memoryKey": {"__rl": true, "mode": "list", "value": "my_policy_docs", "cachedResultName": "my_policy_docs"}, "clearStore": true}}
```
```json
{"name": "Embeddings", "type": "@n8n/n8n-nodes-langchain.embeddingsOpenAi", "typeVersion": 1.2, "position": [960, 520],
 "parameters": {"model": "text-embedding-3-large", "options": {}}, "credentials": {"openAiApi": {"id": "openAiCourse0001", "name": "OpenAI (.env)"}}}
```
```json
{"name": "Chunk loader", "type": "@n8n/n8n-nodes-langchain.documentDefaultDataLoader", "typeVersion": 1.1, "position": [1120, 520],
 "parameters": {"jsonMode": "expressionData", "jsonData": "={{ $json.text }}", "textSplittingMode": "simple",
   "options": {"metadata": {"metadataValues": [{"name": "source", "value": "={{ $json.source }}"}, {"name": "title", "value": "={{ $json.title }}"}]}}}}
```
- `clearStore: true`: 색인할 때마다 비우고 다시 넣는다 (같은 청크가 두 번 들어가지 않게).
- Loader의 `textSplittingMode: "simple"`은 거의 나누지 않는다. **청크는 앞의 Code가 정한다.**
- 색인 뒤 개수는 Code에서 `$('Make chunks').all().length`로 센다.

### Vector Store (메모리) — 검색
```json
{"name": "Search policies", "type": "@n8n/n8n-nodes-langchain.vectorStoreInMemory", "typeVersion": 1.3, "position": [420, 300],
 "parameters": {"mode": "load", "memoryKey": {"__rl": true, "mode": "list", "value": "my_policy_docs", "cachedResultName": "my_policy_docs"},
   "prompt": "={{ $json.body.question }}", "topK": "={{ $json.body.top_k ?? 3 }}", "includeDocumentMetadata": true},
 "alwaysOutputData": true}
```
- 결과는 항목 여러 개: `$json.document.pageContent`(글), `$json.document.metadata.source`, `$json.score`(0~1, 클수록 가까움). 같은 `Embeddings` 노드를 `ai_embedding`으로 연결한다.
- `alwaysOutputData: true`: 저장소가 비어도 빈 항목 하나가 나와 워크플로우가 멈추지 않는다. 다음 Code에서 `item.json.document`가 있는 항목만 쓴다.

### AI Agent + OpenAI chat model (근거로 답하기, 질문 다시 쓰기)
```json
{"name": "Answer from policies", "type": "@n8n/n8n-nodes-langchain.agent", "typeVersion": 3.1, "position": [1080, 200],
 "parameters": {"promptType": "define", "text": "=질문: {{ $json.question }}\n\n규정 발췌:\n{{ $json.context }}",
   "options": {"systemMessage": "Answer only from the numbered policy excerpts ... write the excerpt number like [2] ...", "maxIterations": 2}}}
```
```json
{"name": "OpenAI chat model", "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi", "typeVersion": 1.2, "position": [1040, 420],
 "parameters": {"model": {"__rl": true, "mode": "id", "value": "gpt-4.1-mini"}, "options": {"temperature": 0}},
 "credentials": {"openAiApi": {"id": "openAiCourse0001", "name": "OpenAI (.env)"}}}
```
- Agent의 결과는 `$json.output`(글자). 발췌 번호 `[2]`는 다음 Code에서 문서 제목으로 바꾼다.

### Edit Fields (Set) — 담당자 연결
```json
{"name": "Not in policies", "type": "n8n-nodes-base.set", "typeVersion": 3.4, "position": [1080, 520],
 "parameters": {"assignments": {"assignments": [
   {"id": "a0", "name": "route", "value": "담당자 연결", "type": "string"},
   {"id": "a1", "name": "answer", "value": "규정에서 답을 찾지 못했습니다. IT 문의 창구로 연결해 드릴게요.", "type": "string"},
   {"id": "a2", "name": "cited", "value": "={{ [] }}", "type": "array"}]}, "options": {}}}
```

## 6. 연결 (`connections`)

```json
{
  "Make chunks": {"main": [[{"node": "Store chunks", "type": "main", "index": 0}]]},
  "Embeddings": {"ai_embedding": [[{"node": "Store chunks", "type": "ai_embedding", "index": 0}]]},
  "Chunk loader": {"ai_document": [[{"node": "Store chunks", "type": "ai_document", "index": 0}]]},
  "Relevant?": {"main": [[{"node": "Answer from policies", "type": "main", "index": 0}], [{"node": "Not in policies", "type": "main", "index": 0}]]},
  "OpenAI chat model": {"ai_languageModel": [[{"node": "Answer from policies", "type": "ai_languageModel", "index": 0}]]}
}
```
- 키는 **보내는 노드 이름**, 안의 `node`는 받는 노드 이름. If의 `main`은 `[ [true 쪽], [false 쪽] ]`.
- Chat model은 `ai_languageModel`, Embeddings는 `ai_embedding`, Loader는 `ai_document`로 연결한다 (`main` 아님).

## 7. 표현식 주의

- 표현식은 `=`로 시작한다: `"={{ $json.body.question }}"`. `=`가 없으면 그냥 글자로 남는다.
- `{{ }}` 안에서 객체를 만들 때 `}}`가 붙지 않게 띄어 쓴다: `"={{ JSON.stringify({ draft: $json.draft }) }}"`
- 다른 노드 뒤에서 웹훅 입력은 `$('Question webhook').first().json.body`로 읽는다 (`$json`은 바로 앞 노드 결과).

## 8. 테스트 파일 (`cases/*.json`)

```json
{
  "webhook": "my-search",
  "before": [{"webhook": "my-index", "request": "requests/index-section.json"}],
  "cases": [
    {"name": "비밀번호 길이", "request": "requests/q-password-length.json",
     "expect": {"equals": {"hits.0.source": "password-policy"}, "contains": {"hits.0.text": ["12자"]}}},
    {"name": "직접 쓴 질문", "body": {"question": "", "top_k": 3}, "expect": {"status": 400}},
    {"name": "다른 웹훅으로", "webhook": "my-policy-qa", "body": {"question": "점심 메뉴"}, "expect": {"equals": {"route": "담당자 연결"}}}
  ]
}
```
- `before`: 케이스보다 먼저 한 번 부른다 (메모리 저장소를 다시 채우는 색인). `--no-before`면 건너뛴다 (내가 다른 설정으로 색인해 둔 것을 그대로 쓸 때).
- 필드 이름은 점으로 내려간다: `hits.0.source` = `hits` 첫 항목의 `source`.
- `equals`: 값이 같아야 함 · `contains`: 목록 중 **하나라도** 들어 있어야 함 (배열·객체는 JSON 글자로 바꿔 찾음) · `not_contains`: 하나도 없어야 함 · `status`: HTTP 코드(기본 200)
- `uv run tools/flow.py test <파일> -v --repeat 3`: LLM 답은 매번 조금씩 다르므로 3번 이상 돌려 본다. `-v`(`--verbose`)는 케이스마다 보낸 요청 JSON과 받은 응답 JSON을 화면에 보여 준다 (보고서 `runs/*.json`에도 같은 것이 남음). `call ... -v`도 보낸 요청 JSON을 응답 위에 함께 보여 준다.
- **테스트를 통과시키려고 테스트 파일의 기대 결과를 바꾸지 않는다.** 기대 결과가 틀렸다고 생각되면 사람에게 묻는다.

## 9. 하지 말 것

- `tools/`, `data-api/`, `requests/`, `reference/`, 이 파일(`AGENTS.md`)을 고치지 않는다 (요청받은 경우만). 규정 문서(`data-api/data/docs`)를 고쳐서 테스트를 통과시키지 않는다.
- 답을 검색 결과 밖의 지식으로 쓰지 않는다 (규정에 없으면 없다고 하고 담당자 연결).
- n8n 컨테이너를 지우거나 `docker compose down`을 하지 않는다. `~/day65-n8n`(n8n 설치·비밀값)을 읽거나 고치지 않는다. Credential을 새로 만들지 않는다.
- `.env`나 API 키를 읽어서 출력하지 않는다.
