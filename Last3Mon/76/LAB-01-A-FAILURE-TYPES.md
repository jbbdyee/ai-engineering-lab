# Lab 01 · 실패를 겪어 보고, 항목마다 처리하고, 중복 없이 다시 해 보기

> **강사용 정답본** · 학생 저장소에 올리지 않습니다. 학생용 문제는 [LAB-01-Q-FAILURE-TYPES.md](LAB-01-Q-FAILURE-TYPES.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 실습을 5개로 늘린 뒤 정답 워크플로우를 학생 순서대로 2026-10-29에 1회씩 실행한 값입니다 (강사 Mac, 분류 `gpt-4.1-mini`). 명령 · 출력 전부: [answers/LAB-TEST-RESULT.md](answers/LAB-TEST-RESULT.md).

## 예제 1 · 결과 (에이전트 없이, `answers/01`)

| 한 일 | 사용자가 본 것 | 실제로 생긴 것 |
| --- | --- | --- |
| 정상 3건 | 200 · `processed: 3` (5.2초) | 접수 건 3 (T-2001~2003) |
| 빈 글이 섞인 3건 | **500** · `Error in workflow` | 접수 건 **2** (1번째 · 3번째) |
| `flaky` · 2건 | 500 | 0 (재시도 없음) |
| 정상 3건을 다시 | 200 · 새 번호 3개 | 접수 건 8 · VPN 문의가 T-2001 · T-2006 **둘** (키 `10057-0` → `10060-0`) |

- 풀이 때: "500을 받은 사용자는 무엇을 하나?" → 다시 보냄 → 2건이 또 생김. 500은 "아무것도 안 됨"이 아닙니다.

## 예제 2 · 요청문 예

```text
my-work/intake.json (baseline 을 복사한 것) 의 웹훅 경로를 my-intake 로, 이름을 "76 Intake (my)" 로 바꿔 줘.
requests 가 목록이 아니면 400 {"error": "requests must be a list"}.
항목마다 id · user · text 를 확인해서, 빠진 것이 있으면 LLM 과 API 로 보내지 말고 status rejected 와 이유("text is required" 등)로.
Create ticket 노드에 timeout 3000ms, 재시도 3 번, 간격 300ms, 그리고 실패해도 다음으로 가게 onError continueRegularOutput .
접수 건의 key 는 요청의 id (실행 번호가 아님).
처리한 갈래와 거절한 갈래를 Merge 로 모아 AGENTS.md 3절 결과 모양으로, HTTP 200 .
기대 결과 cases/lab01.json.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `3` | 조건 표 "3번" (`maxTries`는 첫 시도를 포함한 수) |
| ② | `continueRegularOutput` | 실패한 항목이 `error`를 가진 채 다음 Code로 (AGENTS.md 5절) |
| ③ | 요청의 `id` | 같은 문의를 다시 보내도 바뀌지 않는 것. `$execution.id`는 실행마다 바뀜 (예제 1의 `10057` → `10060`) |
| ④ | `200` | 부분 성공. 일부가 실패해도 항목마다 상태로 알림 |

정답: [reference/lab01-example2-intake.json](reference/lab01-example2-intake.json)

| 10/29 결과 | |
| --- | --- |
| 고치기 전 (`answers/02`, 기준에 같은 테스트) | **0/6** · 결과 모양이 달라 `null`, 접수 건 6 (중복), 빈 글 · 목록 아님 · `flaky` 모두 500 |
| 고친 뒤 (`answers/03`) | **6/6** · 다시 보낸 3건 `duplicates: 3`, `flaky` 2건 재시도로 성공 (2.4초), 빈 글만 `rejected` (1.7초) |

## 예제 3 · 결과 (에이전트 없이, `answers/04`)

| 고장 | 시간 | 결과 | 이유 |
| --- | --- | --- | --- |
| `flaky` | 2.4초 | `created: 2` | 첫 시도 500 → 두 번째 성공 |
| `error` | 3.4초 | `failed: 3` | `500 - tickets service is failing (fault switch)` 세 번 |
| `slow` | **12.4초** | `failed: 3` | `timeout of 3000ms exceeded` 세 번 |
| 8초 뒤 접수 건 | | **5** (2 + 3) | 실패라던 R-101~103이 늦게 만들어짐. 시도 9번 · 키가 같아 3건 |
| 다시 보냄 | 2.9초 | `duplicates: 3` | 키가 이미 있음 |

- 이 예제의 답 두 가지: ① 재시도는 **잠깐의 실패에만** 약이고, 멈춤 · 느림에는 시간만 늘린다 (`tretry --deadline`으로 이어짐). ② 시간 초과는 **"모름"**이다 — `failed`라고 말한 것이 만들어져 있다. 그래서 시간 초과 뒤 재시도 · 재처리에는 멱등 키가 꼭 있어야 한다 (Lab 03 예제 3).

## 과제 1 · 요청문 예

```text
my-work/intake.json 에서 Classify(AI Agent) 노드가 실패해도 워크플로우가 멈추지 않게 onError continueRegularOutput 로 해 줘.
Parse 에서 그 항목에 error 가 있거나 output 이 JSON 이 아니면 category "미분류", priority "보통" 으로.
결과의 unclassified 에 미분류로 접수한 수를 세어 줘. 나머지는 그대로.
기대 결과 cases/lab01-challenge.json, cases/lab01.json 도 그대로 통과.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `continueRegularOutput` | `Create ticket`과 같은 값. 실패한 항목이 다음으로 |
| ② | `error` | 실패한 항목은 `output` 대신 `error`를 가짐 |
| ③ | `미분류` | 팀장의 말 |
| ④ | `unclassified` | AGENTS.md 3절 결과 모양 |

정답: [answers/76-lab01-challenge-fallback.json](answers/76-lab01-challenge-fallback.json)

| 10/29 결과 | |
| --- | --- |
| 고치기 전 (`answers/05`) | **1/3** · `llm down`에서 0.8초에 500, 접수 0 |
| 고친 뒤 (`answers/06`) | **3/3** · `created: 3, unclassified: 3` (0.9초), `lab01` 6/6 |

- 풀이 때: 72일차 "간단 답변"과 같은 생각(덧붙인 일은 줄여서라도 핵심 일을 끝냄)이고, `unclassified` 수가 "얼마나 줄였는지를 숨기지 않기"라는 점을 짚습니다.

## 과제 2 · 요청문 예

```text
my-work/intake.json 에서 requests 가 목록이어도 10 건이 넘으면 HTTP 400 {"error": "too many requests (max 10)"} 로, 하나도 처리하지 말아 줘.
목록이 아닐 때의 400 글은 그대로 "requests must be a list".
Check items 에서 같은 요청 안에 같은 id 가 또 나오면 두 번째부터 rejected, 이유 "duplicate id in this request".
앞에서 본 id 는 Set 에 기억해 둔다. 나머지 규칙(빠진 칸 거절 · 재시도 · 키 · 미분류)은 그대로.
기대 결과 cases/lab01-challenge2.json, cases/lab01.json · lab01-challenge.json 도 통과.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `10` | "10건까지만" — 10은 받고 11부터 400 |
| ② | `두` | 처음 나온 것은 받음 |
| ③ | `duplicate id in this request` | 조건 표 그대로 (테스트가 `duplicate id`를 찾음) |
| ④ | `Set` | 본 id를 빨리 찾는 모음 (배열 `includes`도 되지만 Set이 알맞음) |

정답: [answers/76-lab01-challenge2-rules.json](answers/76-lab01-challenge2-rules.json) (`Is a list?`의 조건에 `length <= 10`, `Reject body`의 글을 두 경우로)

| 10/29 결과 | |
| --- | --- |
| 고치기 전 (`answers/07`) | **1/4** · 같은 id: `created: 3, duplicates: 1` (분류 세 번), 11건: **11.0초**에 200 · 접수 건 13 |
| 고친 뒤 (`answers/08`) | **4/4** · 같은 id 두 번째만 `rejected`, 11건 **0.2초**에 400 · 접수 건 2 그대로, `lab01` 6/6 · `lab01-challenge` 3/3 |

## 2교시에 볼 것

| 볼 것 | 막혔을 때 한마디 |
| --- | --- |
| 재시도 설정을 `parameters` 안에 씀 | "`check`가 알려 준 대로 노드 바로 아래로" (`flow.py check`가 오류로 잡음) |
| 거절한 항목이 결과에 없음 | "Merge 두 번째 입력(`index: 1`)" |
| `duplicates`가 0 | "키가 실행 번호인지 요청 id인지" |
| `failed`와 `created`가 엉뚱한 항목에 | "Mark results가 `Parse`의 `.all()`과 같은 순서인지" |
| `slow` 케이스를 오래 기다림 | "정상. 12초가 바로 이 예제의 숫자" |
| 같은 id를 멱등 키로 충분하다고 함 | "결과가 세 건이라고 말하고 분류를 세 번 했다" |
