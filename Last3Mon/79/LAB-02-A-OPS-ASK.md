# Lab 02 · 질문 답변 · 고르고, 막고, 숫자를 확인하기

> **강사용 정답본** · 학생 저장소에는 수업이 끝난 뒤 올립니다. 학생용 문제는 [LAB-02-Q-OPS-ASK.md](LAB-02-Q-OPS-ASK.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과는 2026-11-01 정답 워크플로우 1회 실행 값입니다 (LLM `gpt-4.1-mini` · temperature 0, 답 글은 실행마다 다를 수 있음). 명령 · 출력 전부: [answers/LAB-TEST-RESULT.md](answers/LAB-TEST-RESULT.md).

## 예제 1 · 요청문 예

```text
my-work/ops-ask.json 을 새로 만들어 줘. 웹훅 POST my-ops-ask, 본문 question, 이름 "79 Ops ask (my)".
Route(Code): AGENTS.md 3절 영역별 낱말 목록으로 맞은 낱말이 가장 많은 영역, 같으면 표의 앞 영역, 하나도 없으면 unknown. router 는 "keyword".
Known area?(IF): unknown 이면 LLM 을 부르지 않고 바로 거절 {refused: true, reason: "out_of_scope"}.
Get facts: 사실을 다시 세지 말고 HTTP POST http://localhost:5678/webhook/my-ops-facts 로 부른다. Pick facts(Code): 사실 중 그 영역만 (overview 면 전부).
Answer(AI Agent + gpt-4.1-mini, temperature 0): 한국어 2~3문장, 받은 사실의 숫자만. 결과 {question, area, router, refused: false, reason: null, answer}. 기대 결과 cases/lab02.json.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | 앞 | 같은 수면 표의 순서로 하나를 정함 — 늘 같은 답 |
| ② | `out_of_scope` | 운영과 상관없는 질문은 LLM을 부르지 않고 거절 |
| ③ | `my-ops-facts` | 사실을 두 곳에서 세지 않음 (Lab 01과 같은 숫자) |
| ④ | 그 영역만 | 필요 없는 숫자를 주면 LLM이 엉뚱한 숫자를 씀 |

정답: [reference/lab02-example1-ask.json](reference/lab02-example1-ask.json)

| 11/01 결과 | |
| --- | --- |
| 고치기 전 (`answers/09`, 기준 챗봇에 같은 테스트) | **0/6** · 점심 메뉴 추천, **"DLQ 1번 작업을 다시 실행해 드리겠습니다"**, 카나리 질문에 오류율 · 알림까지 섞음 |
| 고친 뒤 (`answers/10`) | **3/6** · 오류율 · parked · 운영 밖 거절(0.1초) ✔, 작업 요청이 `dlq`로 가서 "#1은 대기 중"(틀림), `numbers_ok` 없음 |

## 예제 2 · 요청문 예

```text
my-work/ops-ask.json 에 거절과 숫자 확인을 더해 줘.
Route 에서 작업 요청(AGENTS.md 3절 낱말: 다시 돌려 · 지워 · 꺼 줘 · 배포해 · 되돌려 …)이 있으면 영역 action.
Action?(IF): action 이면 LLM 앞에서 바로 거절 {refused: true, reason: "read_only", answer: "운영 도우미는 읽기만 합니다 …"}.
Check numbers(Code): 답의 숫자가 모두 그 영역 사실 안에 있는지 (값 · ×100 · 반올림 · 글자 속 숫자, 버전 1.2.0 은 통째로) 보고 numbers_ok, 없는 숫자는 unknown_numbers.
숫자 확인은 LLM 이 아니라 Code. 앞의 칸은 그대로. 기대 결과 cases/lab02.json 전체.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `action` | 작업 요청은 영역이 아니라 따로 표시 |
| ② | `read_only` | AGENTS.md 3절 거절 이유. 테스트가 이 글자를 봄 |
| ③ | 통째로 | 1.2.0을 1 · 2 · 0으로 쪼개면 '없는 숫자'로 오판 |
| ④ | Code | LLM에게 'LLM의 숫자가 맞나'를 묻지 않음 (77일차 숫자 확인) |

정답: [reference/lab02-example2-ask.json](reference/lab02-example2-ask.json)

| 11/01 결과 | |
| --- | --- |
| 고치기 전 | **3/6** (예제 1 그대로) |
| 고친 뒤 (`answers/11`) | **6/6** · 작업 요청 거절 0.0초 (LLM 없음), 비용 92.01 · 릴리스 62.5 `numbers_ok: true` |

- 풀이 때: 숫자 확인은 "지어낸 숫자"만 잡는다 — 예제 1의 "#1은 대기 중"(1은 사실에 있는 숫자)은 못 잡음.

## 예제 3 · 결과 (에이전트 없이, `answers/12`)

| 질문 | 낱말 라우터 | 운영자에게 |
| --- | --- | --- |
| 에러 많이 났어? | runs | 좋음 |
| 장애 났어? | 거절 | 불편 |
| 알림이랑 DLQ | alerts (표의 앞) | 반쪽 — "DLQ 정보는 없습니다" |
| 카나리 꺼 줘 | 작업 거절 | 안전 |
| 배포 상태 요약해 줘 | overview (2 > 1) | 넓음 |
| AI 쓰는 데 얼마나 나갔어? | 거절 | 불편 |

- **6/6** = 규칙대로. 낱말 라우터는 모르면 거절하는 쪽으로 실패 (안전 · 불편).

## 과제 1 · 요청문 예

```text
my-work/ops-ask.json 에 LLM 라우터를 더해 줘.
낱말 라우터가 unknown 일 때만 Classify(AI Agent + gpt-4.1-mini, temperature 0)가 영역 하나 또는 none 을 고른다. 지시문에 영역 목록과 뜻, "Reply with only the area word".
Read class(Code): 받은 글에서 영문자만 남겨 영역 목록에 있으면 그 영역, 아니면 unknown. router 는 "llm".
그래도 unknown 이면 거절 (out_of_scope). 작업 요청 거절은 LLM 라우터보다 앞에 그대로.
낱말이 맞으면 LLM 을 부르지 않는다. 앞의 칸은 그대로. 기대 결과 cases/lab02-challenge.json, cases/lab02.json 도.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | 만 | 낱말이 맞으면 빠르고 늘 같음 — LLM은 모자랄 때만 |
| ② | `unknown` | LLM이 목록에 없는 말을 하면 운영 밖으로 |
| ③ | 앞 | 작업 요청이 LLM 라우터로 가면 안 됨 (막는 쪽으로) |
| ④ | 부르지 않는다 | `router: keyword` — 비용 · 시간 · 흔들림이 없음 |

정답: [answers/79-lab02-challenge-llm-router.json](answers/79-lab02-challenge-llm-router.json)

| 11/01 결과 | |
| --- | --- |
| 고치기 전 (`answers/13`) | **1/5** · 낱말 없는 셋 거절, 점심은 `keyword` |
| 고친 뒤 (`answers/14`) | **5/5** · AI 비용 `cost` 92.01% (4.9초) · 남은 접수 `dlq` 3건 · 새 판 `release` 62.5%, 점심 `llm` 거절, 낱말 질문은 `keyword`. `lab02` 6/6, `lab02-phrasing` **4/6** (장애 · AI 비용이 이제 답함 — 기대가 옛 규칙) |

- 풀이 때: DLQ 답 "2건은 대기 · 1건은 주차"는 **거꾸로**인데 `numbers_ok: true`. 기능을 바꾸면 테스트의 기대도 사람이 고친다 (phrasing 4/6).

## 과제 2 · 요청문 예

```text
my-work/ops-ask.json 에 감사 기록을 더해 줘.
갈래 셋(작업 거절 · 운영 밖 · 답) 모두, 응답하기 전에 POST http://data-api:8800/audit 한 줄 {kind: "ops-ask", question, area, router, refused, reason, numbers_ok} (거절이면 numbers_ok null).
감사 HTTP 노드 뒤의 응답은 그 노드의 출력이 아니라 앞 노드의 결과를 다시 읽어 보낸다 (응답 모양은 그대로).
/audit 은 덧붙이기만 하는 기록이고, 다른 상태는 바꾸지 않는다. neverError 를 켜서 감사가 실패해도 답은 나간다.
기대 결과 cases/lab02-challenge2.json, lab02 · lab02-challenge 도.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | 셋 | 거절도 기록해야 '누가 무엇을 시키려 했나'가 남음 |
| ② | 앞 노드 | HTTP 노드의 출력은 데이터 API의 응답 (78일차 `Result again`과 같음) |
| ③ | 바꾸지 않는다 | 감사는 덧붙이기만 — 읽기 전용 원칙의 예외는 이것 하나 |
| ④ | 답은 나간다 | 감사 저장소가 멈췄다고 운영자가 답을 못 받으면 안 됨 |

정답: [answers/79-lab02-challenge2-audit.json](answers/79-lab02-challenge2-audit.json)

| 11/01 결과 | |
| --- | --- |
| 고치기 전 (`answers/15`) | **4/5** · 응답은 맞고 감사 기록 0줄 |
| 고친 뒤 (`answers/16`) | **5/5** · 기록 3줄 (`read_only` · `keyword` / `out_of_scope` · `llm` / `runs` · `numbers_ok: true`), 응답 그대로. `lab02` 6/6 · `lab02-challenge` 5/5 |
