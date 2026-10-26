# 환경 · 외부 서비스 · 인증 · 비용

원본 요구는 Slack · Email · Jira · Notion · Database · API 연동을 말합니다. 3일 안에 21명이 모두 실제 회사 계정을 만들고 승인받기는 어렵고, 실제 서비스의 키 · 개인정보가 섞일 위험도 큽니다. 그래서 **같은 역할을 하는 연습용 서비스(데이터 API)**를 기본으로 쓰고, 실제 서비스 연동은 가산으로 둡니다. 설계서에는 "실제 운영이라면 무엇으로 바꾸나"를 함께 적습니다.

## 1. 환경 (64~79일차와 같음)

| 항목 | 값 |
| --- | --- |
| 워크플로우 | n8n 2.42.6 (65일차 설치, `http://localhost:5678`) |
| LLM | OpenAI `gpt-4.1-mini`, Credential `OpenAI (.env)` (id `openAiCourse0001`). **Ollama는 쓰지 않습니다** |
| 임베딩 | OpenAI `text-embedding-3-large` (같은 Credential, 71일차) |
| 연습용 서비스 | 데이터 API (`http://data-api:8800` · 터미널에서 `http://localhost:8800`), 단위 프로젝트 판: `~/aio-01d4-stu/Last3Mon/80/data-api` |
| 도구 | `tools/flow.py` (check · push · call · test · bench · fault · llm · ops · doctor, 모두 `-v`) |
| 코드 작성 | CLI 코딩 에이전트 (codex · claude · agy), 팀 저장소의 `AGENTS.md`를 따름 ([09-AGENT-WORKING-RULES](09-AGENT-WORKING-RULES.md)) |
| 실습 키트 | `~/aio-01d4-stu/Last3Mon/80` (공통 시나리오 · 템플릿 · 도구, 80일차 전에 `git pull`) |

**첫날 확인**

```bash
cd ~/aio-01d4-stu && git pull
cd ~/aio-01d4-stu/Last3Mon/65/n8n && docker compose start
cd ~/aio-01d4-stu/Last3Mon/80/data-api && docker compose up -d --force-recreate
cd ~/aio-01d4-stu/Last3Mon/80 && uv run tools/flow.py doctor        # 마지막 줄 ready
```

### 팀 안에서 n8n을 어떻게 나누나

각자 노트북의 n8n은 따로입니다. 다른 사람의 n8n에서 내 워크플로우는 보이지 않습니다.

| 방식 | 하는 법 | 언제 |
| --- | --- | --- |
| **저장소로 나누기 (기본)** | 워크플로우 JSON을 팀 저장소에 두고, 각자 `git pull` → `flow.py push`로 자기 n8n에 올림 | 늘 |
| 시연용 한 대 | 발표 · 최종 시험은 리드의 노트북 한 대에서 | 82일차 |
| 모듈 나누기 | 70일차처럼 하위 워크플로우(웹훅 또는 Execute Workflow)로 나눠 사람마다 한 파일 | 큰 워크플로우 |

워크플로우 이름 · 웹훅 경로 앞에 팀 이름을 붙입니다 (`team1-support`, `team1-index`). 같은 n8n에 여러 팀 것이 올라가도 겹치지 않습니다.

## 2. 외부 서비스를 무엇으로 대신하나

| 원본 요구의 서비스 | 하는 일 | 연습용 (데이터 API) | 실제 운영이라면 |
| --- | --- | --- | --- |
| **Slack** (문의 받기) | 직원 메시지 수신 | 팀 Webhook `POST /webhook/<팀>-support` (본문에 `channel`, `user`) | Slack Trigger 노드 (OAuth 앱, 이벤트 구독) |
| **Slack · Email** (알림) | 담당자 · 관리자에게 알림 | `POST /alerts` `{"workflow", "node", "message", "severity", ...}` → `GET /alerts`로 확인 | Slack 메시지 노드, Send Email (SMTP) |
| **Jira** (티켓) | 이관 티켓 생성 · 조회 | `POST /tickets` `{"key", "title", "requester", "category", "priority"}` (같은 `key`는 중복으로 막음), `GET /tickets-created` | Jira Software 노드 (API Token · OAuth) |
| **Notion** (지식 문서) | 지식베이스 | `GET /docs`, `GET /docs/<name>` (규정 문서 8개, 마크다운) + 팀이 더한 문서 | Notion 노드, Confluence |
| **Database** (기록 · 상태) | 실행 기록 · 캐시 · 대기열 | `POST /logs`, `/cache/<key>`, `POST /dlq` (실패 대기열) | Postgres · MySQL 노드 |
| **API** (업무 시스템) | 접수 건 · 직원 정보 | `GET /tickets/<id>?requester=` (남의 건이면 403), `GET /employees/<이름>`, `GET /faq?q=` | 사내 API (HTTP Request + Credential) |
| 장애 연습 | 외부 서비스가 느리거나 멈춤 | 고장 스위치 `flow.py fault faq\|tickets slow\|error\|flaky`, `flow.py llm down\|up` | 실제로는 일어남 |

설계서의 "외부 연동 노드" 표에는 **연습용과 실제 운영용을 둘 다** 적습니다 (인증 방식 · 오류 코드 · 한도가 다르기 때문). 연습용에서 정상 동작을 보이고, 실제 서비스로 바꿀 때 바뀌는 곳을 표시하면 됩니다.

### 실제 서비스를 쓰고 싶은 팀 (가산)

- 팀 공용 **무료 · 연습용 계정**만 씁니다 (회사 · 개인 업무 계정 금지).
- 키 · 토큰은 **n8n Credential에만** 넣습니다. 워크플로우 JSON · 문서 · 스크린샷 · 저장소에 보이면 안 됩니다. 커밋 전에 `tscan staged`(73일차).
- 실제 서비스가 안 되는 날(계정 승인 지연 · 한도)을 대비해 **연습용으로도 똑같이 돌게** 둡니다 (Switch 하나로 바꿀 수 있게).
- 시연 전날까지 되지 않으면 연습용으로 시연합니다. 평가에서 불리하지 않습니다.

## 3. 인증 (원본 요구: OAuth · API Key와 에러 처리)

| 어디 | 연습용에서 하는 것 | 설계서에 쓸 것 |
| --- | --- | --- |
| 팀 Webhook (들어오는 문) | Webhook 노드 Authentication = **Header Auth**, Credential에 팀 키 (요청 머리글 `X-Team-Key`) | 키가 없거나 틀리면 401 (n8n이 돌려줌), 운영은 Slack 서명 검증 · SSO |
| 데이터 API (나가는 호출) | 단위 프로젝트 판은 `/tickets` · `/alerts` 등 "외부 서비스" 경로에 `X-Api-Key`를 요구 → HTTP Request의 Header Auth Credential | 키가 틀리면 401 → 재시도하지 않고 중단 + 알림 |
| OpenAI | 기존 Credential `OpenAI (.env)` | 키 만료 · 한도 초과(429) 때의 처리 |
| 실제 서비스 (가산) | 해당 노드의 OAuth2 · API Token Credential | 토큰 만료 → 재인증 알림 |

- **401 · 403은 다시 해도 안 됩니다.** 재시도하지 말고 멈추고 알립니다. 429 · 5xx · timeout만 재시도합니다 ([06-RELIABILITY-AND-SECURITY](06-RELIABILITY-AND-SECURITY.md) 1절).
- Header Auth 키를 걸면 `flow.py call` · `test`도 키를 보내야 합니다: `FLOW_WEBHOOK_KEY=<팀 키> uv run tools/flow.py test ...` (단위 프로젝트 판 `flow.py`).

## 4. 비용과 호출 한도

- 모든 팀이 강사의 OpenAI 키 하나를 함께 씁니다. **한 팀이 반복 시험을 크게 돌리면 다른 팀도 느려지고 한도에 걸릴 수 있습니다.**
- 시나리오 반복은 3회까지, `bench`는 `-n 5`까지를 기본으로 합니다. 더 필요하면 강사에게 말합니다.
- LLM을 부르기 전에 끝낼 수 있는 것(400 · 차단 · 권한 없음 · 캐시)은 앞에서 끝냅니다 (72 · 73 · 75일차). 결과서에 요청당 LLM 호출 수(`agents`나 실행 기록)를 적으면 비용 설명이 됩니다.
- 사용량은 75일차처럼 `POST /usage`로 남기면 `GET /usage/summary`로 팀별로 볼 수 있습니다 (가산).

## 5. 데이터 API를 되돌리기

| 상황 | 명령 |
| --- | --- |
| 만든 티켓 · DLQ · 알림 비우기 | `uv run tools/flow.py ops --reset` |
| 고장 스위치 끄기 | `uv run tools/flow.py fault all ok` |
| LLM 멈춤 연습 되돌리기 | `uv run tools/flow.py llm up` |
| 전부 처음으로 | `cd ~/aio-01d4-stu/Last3Mon/80/data-api && docker compose up -d --force-recreate` |

> 데이터 API는 상태를 메모리에 둡니다. 다시 켜면 만든 티켓 · 로그 · 캐시가 사라집니다. 결과서에 쓸 기록은 `runs/`의 보고서 파일로 남깁니다.
