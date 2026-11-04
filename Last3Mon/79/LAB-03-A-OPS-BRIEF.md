# Lab 03 · 브리핑과 평가 · 먼저 볼 것을 정하고, 도우미를 시험하기

> **강사용 정답본** · 학생 저장소에는 수업이 끝난 뒤 올립니다. 학생용 문제는 [LAB-03-Q-OPS-BRIEF.md](LAB-03-Q-OPS-BRIEF.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과는 2026-11-01 정답 워크플로우 1회 실행 값입니다. 명령 · 출력 전부: [answers/LAB-TEST-RESULT.md](answers/LAB-TEST-RESULT.md).

## 예제 1 · 요청문 예

```text
my-work/ops-brief.json 을 새로 만들어 줘. 웹훅 POST my-ops-brief, 이름 "79 Ops brief (my)".
Get facts: HTTP POST http://localhost:5678/webhook/my-ops-facts (본문 from · to 그대로). 상태도 사실에서 그대로 쓴다 (다시 판정하지 않음).
Make brief(Code): actions = red 다음 yellow 의 앞 3개, 영역마다 AGENTS.md 3절 표의 할 일 글자 그대로.
markdown: 제목 · 전체 · | 영역 | 상태 | 숫자 | 표 (🔴 · 🟡 · 🟢, 숫자 칸은 3절 표의 꼴) · "## 먼저 볼 것".
LLM 은 쓰지 않는다. 결과 {overall, red, yellow, actions, markdown}. 기대 결과 cases/lab03.json.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | 그대로 | 상태 판정은 한 곳(사실) — 브리핑이 다시 판정하면 어긋남 |
| ② | `3` | 아침에 먼저 볼 것은 셋까지 |
| ③ | 먼저 볼 것 | 테스트 · 다음 단계가 이 제목을 찾음 |
| ④ | 쓰지 않는다 | 표와 할 일은 규칙 — 늘 같은 브리핑 |

정답: [reference/lab03-example1-brief.json](reference/lab03-example1-brief.json)

| 11/01 결과 | |
| --- | --- |
| 고치기 전 (`answers/17`) | **0/4** · 404 |
| 고친 뒤 (`answers/18`) | **4/4** · 🔴, 먼저 볼 것 실행 · DLQ · 릴리스, 표 `\| DLQ \| 🔴 \| 3건 (parked 2) \|`, DLQ를 비우면 셋째에 알림. LLM 없음 |

## 예제 2 · 요청문 예

```text
my-work/ops-brief.json 에 LLM 요약을 더해 줘.
Summarize(AI Agent + gpt-4.1-mini, temperature 0): 사실 JSON 과 actions 만 주고 한국어 3문장 — 전체 상태 · 가장 급한 곳 · 먼저 할 일. 사실에 없는 숫자 · 원인은 쓰지 않는다.
Check summary(Code): 요약의 숫자가 사실 안에 있는지 Lab 02 예제 2 와 같은 방법으로 보고 numbers_ok.
markdown 끝에 "## 요약" 과 요약 글. 표 · 먼저 볼 것은 Code 가 만든 그대로 (LLM 이 고치지 않음).
기대 결과 cases/lab03-llm.json, cases/lab03.json 도.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `3` | 아침 회의용 세 문장 |
| ② | `numbers_ok` | 요약의 숫자도 확인 (지어낸 숫자 찾기) |
| ③ | 요약 | 테스트가 `## 요약`을 찾음 |
| ④ | 고치지 않음 | LLM은 요약 글만 — 숫자 표는 Code |

정답: [reference/lab03-example2-brief.json](reference/lab03-example2-brief.json)

| 11/01 결과 | |
| --- | --- |
| 고치기 전 (`answers/19`) | **0/2** · `summary` 없음 |
| 고친 뒤 (`answers/20`) | **2/2** · 세 문장 "… 가장 긴급한 문제는 'Search FAQ' … 16건 …", `numbers_ok: true`, 1~3.5초. `lab03` 4/4 |

- 풀이 때: 요약은 먼저 볼 것 셋 중 하나만 말함 → 표 · 순서는 Code가.

## 예제 3 · 결과 (에이전트 없이, `answers/21`)

| 사람이 한 일 | 빨강 | 먼저 볼 것 | 고친 것인가 |
| --- | --- | --- | --- |
| (처음) | runs · dlq · release | 실행 · DLQ · 릴리스 | |
| parked 둘 | runs · release | 실행 · 릴리스 · 알림 | 그렇다 |
| 카나리 끔 | runs | 실행 · 알림 · DLQ | 위험을 멈춤 (1.2.0은 그대로) |
| 예산 0.2 | runs | 실행 · 알림 · DLQ | 한도를 바꿈 (쓴 돈은 그대로) |

- **5/5.** 풀이 때: "초록이 된 까닭을 함께 말한다" (77일차 SLO와 같음).

## 과제 1 · 요청문 예

```text
my-work/ops-eval.json 을 새로 만들어 줘. 웹훅 POST my-ops-eval, 본문 {cases: [{question, area, refused, numbers}]}, 이름 "79 Ops eval (my)".
cases 가 비었으면 HTTP 400. Split cases(Code)로 케이스를 아이템으로 나누고, HTTP 노드 하나가 아이템마다 my-ops-ask 를 부른다.
Score(Code): 케이스마다 area 같음 · refused 같음 · numbers 중 하나가 답에 있음 · 거절이 아니면 numbers_ok — 넷 다 맞으면 통과.
score = 통과 / 전체 (소수 4자리), failed 에는 통과 못 한 케이스와 어느 것이 틀렸나 (area_ok · refused_ok · number_ok · grounded · answer).
기대 결과 cases/lab03-challenge.json.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `400` | 빈 평가는 '모두 통과(0/0)'가 아니라 잘못된 요청 |
| ② | 넷 다 | 영역만 맞고 숫자가 틀리면 통과가 아님 |
| ③ | `4` | 0.875처럼 |
| ④ | `answer` | 왜 틀렸는지 사람이 읽어 보게 |

정답: [answers/79-lab03-challenge-eval.json](answers/79-lab03-challenge-eval.json)

| 11/01 결과 | |
| --- | --- |
| 고치기 전 (`answers/22`) | **0/3** · 404 |
| 고친 뒤 (`answers/23`) | **3/3** · 골든 8/8 · score 1 (3.9초), 틀린 기대는 `area_ok: false`로 잡음, 빈 목록 400 |

## 과제 2 · 요청문 예

```text
my-work/ops-eval.json 에 평가 관문을 더해 줘.
본문 min_score (없으면 0.9) 와 비교해 gate = score 가 min_score 이상이면 "pass", 아니면 "fail". 결과에 min_score · gate.
fail 이면 POST http://data-api:8800/alerts {workflow: "ops-eval", severity: "medium", reason: "eval_below", score, min_score, message}.
알림을 보내도 응답은 평가 결과 그대로. 앞의 칸은 그대로. 기대 결과 cases/lab03-challenge2.json, cases/lab03-challenge.json 도.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `0.9` | AGENTS.md 3절 기본 기준 |
| ② | 이상 | 같으면 통과 (78일차 게이트와 같은 경계) |
| ③ | `eval_below` | 테스트가 이 이유로 알림을 찾음 |
| ④ | 그대로 | 알림은 곁가지 |

정답: [answers/79-lab03-challenge2-gate.json](answers/79-lab03-challenge2-gate.json)

| 11/01 결과 | |
| --- | --- |
| 고치기 전 (`answers/24`) | **0/4** · `gate` 없음, 알림 0 |
| 고친 뒤 (`answers/25`) | **4/4** · 기본 0.9 pass, 골든 0.8 pass, 틀린 기대 0 fail → `eval_below` 알림 1건. `lab03-challenge` 3/3 |

- 풀이 때: 수업 준비 때 "실패 → 알림" 뒤에 "알림이 몇 건?"을 두니 도우미가 **7건**이라 답해 평가가 0점 — 평가가 남긴 알림이 다음 평가를 바꿈. 케이스 순서를 바꿈.
