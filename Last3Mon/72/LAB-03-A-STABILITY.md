# Lab 03 · 멈춰도 답하게

> **강사용 정답본** · 학생 저장소에 올리지 않습니다. 학생용 문제는 [LAB-03-Q-STABILITY.md](LAB-03-Q-STABILITY.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 정답 워크플로우를 2026-10-18에 1회씩 실행한 값입니다 (강사 Mac, gpt-4.1-mini).
> 10/24에 실습을 5개로 늘리며 정답을 학생 순서대로 다시 돌렸습니다 (45단계). 명령 · `-v` 출력 전부와 codex 프롬프트: [answers/LAB-TEST-RESULT.md](answers/LAB-TEST-RESULT.md).

## 예제 1 · 고치기 전 (캐시 단계 워크플로우)

| 상황 | 결과 |
| --- | --- |
| FAQ 느림 (8초) | **9.0초** 기다린 뒤 `자동 답변` (사용자는 9초를 기다림) |
| FAQ 오류 (500) | 0.1초 만에 **HTTP 500** `Error in workflow` |
| 캐시에 있는 질문 + FAQ 오류 | 0.1초, `cached: true` (캐시 확인이 FAQ 앞에 있어서 이미 됨) |
| `cases/lab03.json` | 2/4 |

## 예제 1 · 요청문 예

```text
my-work/helpdesk.json 의 Search FAQ 와 Get ticket 에 options.timeout 2000, 노드 설정 retryOnFail true, maxTries 2, waitBetweenTries 500,
onError continueErrorOutput 을 넣어 줘. 두 노드의 오류 출력(main 1번)은 Data down(Set: route 담당자 연결, answer "사내 데이터 시스템이 응답하지 않아 담당자에게 연결합니다.", reason data_api_down)
→ Send data down(Respond). Get ticket 은 404 를 받아야 하니 neverError 는 그대로 둔다. 기대 결과 cases/lab03.json, lab02 도 통과.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `2000` | 2초를 ms로 |
| ② | `2` | 처음 + 다시 한 번. 최악 2 × 2000 + 500 = 4.5초로 느림 케이스 안 |
| ③ | `continueErrorOutput` | 실패하면 두 번째(오류) 출력으로 (AGENTS.md 5절) |
| ④ | `neverError` | 404(없는 번호)를 보통 결과로 받기 |

정답: [reference/lab03-example1-resilient.json](reference/lab03-example1-resilient.json)

| 수업 준비 때 결과 | |
| --- | --- |
| `cases/lab03.json` | 4/4 · FAQ 느림 **4.6초** `담당자 연결` · FAQ 오류 **0.6초** `담당자 연결` · 캐시 0.1초 |

- **바로잡음 (10/24):** 수업 준비 때 여기에 "`neverError` 때문에 접수 API 500이어도 실패로 보지 않는다"고 적었는데, 시험 워크플로우로 재 보니 이 n8n(2.42.6)에서 `neverError`는 **4xx만** 보통 결과로 받고 500은 재시도 뒤 오류 출력으로 갑니다 ([AGENTS.md](AGENTS.md) 5절 표). 대신 404도 재시도를 해서, 이 정답에서 VPN 질문의 `data_ms`가 605ms입니다 (예제 2 단계 32~76ms). 둘 다 예제 3에서 다룹니다.

## 예제 2 · 요청문 예

```text
my-work/helpdesk.json 의 Classify 와 Answer Agent 에 onError continueErrorOutput 을 넣고, 두 노드의 오류 출력을 Simple answer(Code) → Send simple answer 로 이어 줘.
Simple answer: 질문에 접수 번호가 있고 Get ticket 결과에 status 가 있으면 route 간단 답변, "<번호> 접수 건은 현재 '<status>' 상태입니다. <note>".
FAQ 결과가 있으면 route 간단 답변, 첫 FAQ answer + " (자동 답변 기능을 잠시 쓸 수 없어 FAQ 원문으로 안내합니다.)", sources [그 id].
아니면 route 담당자 연결. 모두 llm_calls 0, reason llm_down. 기대 결과 cases/lab03-llm-down.json.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `간단 답변` | LLM 없이 데이터 그대로 답하는 `route` (두 곳 같음) |
| ② | 자동 답변 기능을 잠시 쓸 수 없어 FAQ 원문으로 안내합니다. | 평소 답이 아니라는 안내 (문장은 학생이 정해도 됨) |
| ③ | `담당자 연결` | 데이터로도 답할 수 없을 때 사람에게 |
| ④ | `llm_down` | AGENTS.md 3절 Lab 03 `reason` 중 LLM이 멈춘 경우 |

정답: [reference/lab03-example2-llm-fallback.json](reference/lab03-example2-llm-fallback.json)

| 수업 준비 때 결과 | |
| --- | --- |
| 고치기 전 (`lab03-llm-down`) | 1/4 · 세 질문 모두 **HTTP 500** (빈 질문 400만 통과) |
| 고친 뒤 | 4/4 · VPN 2.4초 `간단 답변` · 접수 0.3초 `간단 답변` · 점심 1.1초 `담당자 연결` |
| `llm up` 뒤 `lab03` | 4/4 |

- `flow.py llm down`은 `Last3Mon/65/n8n/register-credentials.sh`를 틀린 키로 실행합니다. n8n 재시작 없이 바로 적용되고, `llm up`도 바로 돌아왔습니다.

## 예제 3 · 요청문 예

```text
my-work/helpdesk.json 의 Get ticket 응답 설정에 fullResponse 와 neverError 를 켜 줘 (결과가 {statusCode, body}).
Get ticket 보통 출력 다음에 Ticket check(Code): ticket = statusCode 500 이상이면 {} 아니면 body, ticket_status = statusCode,
tickets_down = statusCode 500 이상이고 질문에 접수 번호(/T-?\d{4}/i)가 있을 때만 true.
→ Tickets down?(If) true → Tickets down(Set: route 담당자 연결, category ticket, answer "접수 현황 시스템이 응답하지 않아 담당자에게 연결합니다. 잠시 뒤 다시 물어봐 주세요.", reason tickets_down, llm_calls 0) → Send tickets down
  false → 지금 흐름(After data …).
$('Get ticket').first().json 을 읽던 곳은 모두 $('Ticket check').first().json.ticket 으로 바꾼다. 기대 결과 cases/lab03-ticket.json, lab03.json, lab03-llm-down.json 도 통과.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `fullResponse` | `{statusCode, body}`를 통째로 받기 (AGENTS.md 5절 표 셋째 줄) |
| ② | `500 이상` | 서버 고장 범위. 404는 고장이 아님 (두 곳 같음) |
| ③ | `tickets_down` | AGENTS.md 3절 `reason` 중 접수 API만 멈춘 경우 |
| ④ | `$('Ticket check').first().json.ticket` | 이제 접수 건은 `Ticket check`의 `ticket` 칸에 |

정답: [reference/lab03-example3-ticket-down.json](reference/lab03-example3-ticket-down.json) (예제 2 정답에 `fullResponse` + 노드 4개: Ticket check · Tickets down? · Tickets down · Send tickets down)

| 10/24 결과 (`cases/lab03-ticket.json`) | 고치기 전 (예제 2 정답) | 고친 뒤 |
| --- | --- | --- |
| 평소 접수 현황 | ✔ | ✔ 2.4초 |
| 접수 API 500 · 접수 질문 | ✘ `reason: data_api_down` (0.6초) | ✔ `tickets_down`, 0.1초 |
| 접수 API 500 · VPN 질문 | ✘ **`담당자 연결`** (0.6초) | ✔ `자동 답변`, 1.1초, "인증서" |
| 없는 번호 (404) | ✔ | ✔ 1.3초 |
| 합 | 2/4 | 4/4, `lab03` 4/4, `lab03-llm-down` 4/4 |

- 고친 뒤 VPN 질문의 `data_ms` 38ms (예제 1 정답 605ms). 404 재시도가 사라졌기 때문입니다.
- 풀이 때 짚을 것: "오류 출력은 어느 질문인지 모른다" → 실패를 보통 결과로 받아 워크플로우가 판단.

## 과제 1 · 요청문 예

```text
my-work/health.json 을 새로 만들어 줘 (웹훅 my-health, AGENTS.md 3절).
Start(Code t0) → Check data API(GET http://data-api:8800/health, timeout 2000, onError continueRegularOutput, alwaysOutputData)
→ Check FAQ(GET /faq?q=vpn, 같은 설정) → Check LLM(Agent "Reply with the single word OK.", onError continueRegularOutput, alwaysOutputData;
  모델 options timeout 8000, maxRetries 0) → Summarize(Code): data_api = status ok, faq = results 가 배열, llm = output 에 ok.
  failed = 거짓인 것 이름. status: 모두 참 ok, data_api 나 llm 중 하나라도 참이면 degraded, 아니면 down. seconds.
기대 결과 cases/lab03-challenge.json.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `continueRegularOutput` | 실패해도 **보통** 출력으로 다음 점검에 (두 곳 같음) |
| ② | `status` 가 `ok` | `/health`가 평소 돌려주는 `{"status":"ok"}` |
| ③ | `output` 에 `ok` | "OK."처럼 대문자 · 마침표가 붙어도 참이 되게 소문자로 비교 |
| ④ | `data_api` 나 `llm` 중 하나라도 참이면 `degraded` | 일부는 된다 = 둘 중 하나는 살아 있음 (학생 기준을 적어도 됨) |

정답: [answers/72-lab03-challenge-health.json](answers/72-lab03-challenge-health.json)

| 수업 준비 때 결과 (`cases/lab03-challenge.json` 4/4) | |
| --- | --- |
| 평소 | `ok`, 2.2초 |
| FAQ 오류 | `degraded`, `checks.faq: false`, 0.8초 |
| FAQ 느림 (8초) | `degraded`, 2.8초 (timeout 2초에서 끊고 계속) |
| LLM 멈춤 | `degraded`, `checks.llm: false`, 0.6초 |

10/24 다시 돌린 결과: `lab03-challenge` 4/4 · 평소 `ok` 2.2초 · FAQ 오류 `degraded` 1.0초 · FAQ 느림 3.0초 · LLM 멈춤 0.4초.

## 과제 2 · 요청문 예

```text
my-work/helpdesk.json 에 FAQ 차단기를 더해 줘 (AGENTS.md 3절 캐시 키 표).
Cached? false → Breaker check(GET http://data-api:8800/cache/breaker-faq, neverError) → Breaker open?(value 있음)
  true → Breaker open(Set: route 담당자 연결, answer "사내 데이터 시스템이 응답하지 않아 담당자에게 연결합니다.", reason breaker_open, llm_calls 0) → Send breaker open
  false → Search FAQ.
Search FAQ 의 오류 출력 → Open breaker(POST /cache/breaker-faq {value:{open:true, since: Date.now()}, ttl 30}, neverError) → Data down.
닫는 노드는 만들지 않는다 (ttl 30초가 지나면 데이터 API가 지움). 기대 결과 cases/lab03-challenge2.json, lab03.json 도 통과.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `breaker-faq` | 캐시 키 표 마지막 줄 (두 곳 같음) |
| ② | `breaker_open` | AGENTS.md 3절 `reason` 중 차단기가 열린 경우 |
| ③ | `30` | 초. 조건 표 · 캐시 키 표의 ttl |
| ④ | `Data down` | 이번 사용자에게는 예제 1의 정해진 답 |

정답: [answers/72-lab03-challenge2-breaker.json](answers/72-lab03-challenge2-breaker.json) (예제 3 정답에 노드 5개: Breaker check · Breaker open? · Breaker open · Send breaker open · Open breaker)

| 10/24 결과 (`cases/lab03-challenge2.json`) | 고치기 전 (예제 3 정답) | 고친 뒤 |
| --- | --- | --- |
| 평소 | ✔ 1.3초 | ✔ 2.7초 (push 직후) |
| FAQ 느림 · 처음 | ✔ 4.6초 `data_api_down` | ✔ 4.8초 `data_api_down` |
| FAQ 느림 · 다음 질문 | ✘ **4.6초** `data_api_down` | ✔ **0.1초** `breaker_open` |
| 되살아남 (캐시 비움) | ✔ 1.2초 | ✔ 1.1초 |
| 합 | 3/4 | 4/4, `lab03` 4/4 |

- 손으로 30초 닫힘을 보여 줄 때: `fault faq slow` → `call` 둘 → `curl -s localhost:8800/cache/breaker-faq` → 30초 뒤 `call` (다시 4초대, 다시 열림) → `fault all ok`.
- 이야기 거리: 차단기 상태를 워크플로우 밖(캐시)에 둔 까닭 — 웹훅 실행은 요청마다 새로 시작.
