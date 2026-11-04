# Lab 01 · 운영 사실 · 흩어진 출처를 한 장으로

> **강사용 정답본** · 학생 저장소에는 수업이 끝난 뒤 올립니다. 학생용 문제는 [LAB-01-Q-OPS-FACTS.md](LAB-01-Q-OPS-FACTS.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 실습을 5개로 늘린 뒤 정답 워크플로우를 학생 순서대로 2026-11-01에 1회씩 실행한 값입니다 (강사 Mac). 운영 아침 상태 · 실행 기록이 같으므로 누가 돌려도 같습니다. 명령 · 출력 전부: [answers/LAB-TEST-RESULT.md](answers/LAB-TEST-RESULT.md).

## 예제 1 · 결과 (에이전트 없이, `answers/01`)

| 출처 | `morning` | 기준 대시보드 | 빠진 것 · 틀린 것 |
| --- | --- | --- | --- |
| 실행 기록 | (지난주 357) | **666** · 3.153… | 기간을 넘기지 않음, 백분율 · 반올림 없음 |
| 알림 | 6 · 높음 3 | 6 | 높음 · 이유 |
| DLQ | 3 · parked 2 | 3 | **parked** |
| 품질 | 4줄 · 격리 1 | 없음 | 출처를 안 읽음 |
| 비용 | $0.073604 / $0.08 | 금액 둘 | 비율 · 1위 |
| 릴리스 | 1.1.0 + 카나리 1.2.0 20% | 없음 | **카나리** |

- 풀이 때: "틀린 숫자보다 없는 칸이 위험하다" — 기준만 보면 카나리 · parked(오늘 가장 급한 둘)를 모름.

## 예제 2 · 요청문 예

```text
my-work/ops-facts.json 을 새로 만들어 줘. 웹훅 POST my-ops-facts, 이름 "79 Ops facts (my)".
Get logs(POST http://data-api:8800/logs/query) 에 본문의 from · to 를 넘기고, 비면 2026-10-26 · 2026-10-30 (지난주).
그 뒤 Get alerts · Get DLQ · Get quality · Get quarantine · Get usage · Get budget · Get release 를 한 줄로 잇고, Make facts(Code) 하나에서 AGENTS.md 3절 "사실" 표대로 모은다.
runs 는 77일차 정의 그대로 (error_rate 4자리 · p95 는 ceil(p × n)번째 · 0건이면 0), top_failure 는 (노드, 메시지) 묶음 1위 또는 null.
기간은 실행 기록에만 쓰고, 알림 · DLQ · 품질 · 비용 · 릴리스는 지금 상태. 숫자는 Code 가 세고 LLM 은 쓰지 않는다.
데이터 API 에 바꾸는 요청은 보내지 않는다 (읽기만). 기대 결과 cases/lab01.json.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `my-ops-facts` | AGENTS.md 3절 계약 · 테스트 파일의 `webhook` |
| ② | `2026-10-26 · 2026-10-30` | 운영 회의는 지난주를 봄 — 기준 대시보드는 기간 없이 666을 셈 |
| ③ | 실행 기록에만 | 알림 · DLQ · 비용은 '지금' 상태 — 기간을 대면 오히려 틀림 (예제 3) |
| ④ | 바꾸는 요청 | 운영 도우미는 읽기만. `/logs/query`는 읽기 |

정답: [reference/lab01-example2-facts.json](reference/lab01-example2-facts.json)

| 11/01 결과 | |
| --- | --- |
| 고치기 전 (`answers/02`, 기준에 같은 테스트) | **0/5** · 666 · 3.153…, 높음 · parked · 품질 · 릴리스 칸 없음 |
| 고친 뒤 (`answers/03`) | **5/5** · 357 · 0.0588 · 2598 · 실패 1위 16, 알림 6 · 3, DLQ 3 · 2 · 1, 품질 0.6583, 비용 0.9201 · `test-bot` 0.3699, 카나리 62.5% 대 7.73%, 0.1초 |

## 예제 3 · 결과 (에이전트 없이, `answers/04`)

| 기간 | 실행 | 다시 묻는 비율 | 지금 숫자 |
| --- | --- | --- | --- |
| 두 주 | 666 · 21 · 0.0315 | 7.73% · 62.5% | 그대로 |
| 10/26 | 70 · 16 · 0.2286 | `null` · `null` (그날 두 판이 없음 — 10/28부터) | 그대로 |
| 빈 주 | 0 · 0 · p95 0 · 실패 1위 `null` | `null` · `null` | 그대로 |
| 기간 없음 | 357 (지난주) | 7.73% · 62.5% | 그대로 |

- **5/5.** 풀이 때: 0("없었다")과 `null`("모른다")의 차이 → 과제 1의 "카나리 비교 불가 = 노랑".

## 과제 1 · 요청문 예

```text
my-work/ops-facts.json 의 Make facts 에 영역별 상태를 더해 줘.
AGENTS.md 3절 "상태" 표대로 health {runs, alerts, dlq, quality, cost, release} 를 red · yellow · green 으로. red 를 yellow 보다 먼저 본다.
release 는 카나리가 있고 두 비율이 모두 있고 canary_repeat_rate 가 active 의 2배를 넘으면 red, 카나리만 있으면 yellow.
red · yellow 는 그 색인 영역을 runs, alerts, dlq, quality, cost, release 순서로, overall 은 red 가 있으면 red, 아니면 yellow 가 있으면 yellow, 아니면 green.
상태 판정은 LLM 이 아니라 Code. 앞의 사실은 그대로. 기대 결과 cases/lab01-challenge.json, cases/lab01.json 도.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | 먼저 | 빨강 조건과 노랑 조건이 둘 다 맞으면 빨강 |
| ② | 2배 | 다시 묻는 비율 62.5%가 1.1.0(7.73%)의 두 배를 넘음 → 카나리 문제 |
| ③ | `runs, alerts, dlq, quality, cost, release` | 목록이 늘 같은 순서여야 테스트 · 브리핑이 같음 |
| ④ | Code | 정해진 규칙 — LLM에게 판정시키면 날마다 다름 |

정답: [answers/79-lab01-challenge-health.json](answers/79-lab01-challenge-health.json)

| 11/01 결과 | |
| --- | --- |
| 고치기 전 (`answers/05`) | **0/5** · 칸 없음 |
| 고친 뒤 (`answers/06`) | **5/5** · 🔴 runs · dlq · release, 🟡 alerts · quality · cost, 첫 주 빨강은 dlq 하나, 예산 $1이면 비용 🟢, parked 처리하면 DLQ 🟡. `lab01` 5/5 |

## 과제 2 · 요청문 예

```text
my-work/ops-facts.json 이 출처 하나가 멈춰도 답하게 해 줘.
Get logs 를 뺀 HTTP 노드에 neverError 를 켜고, Make facts 에서 출처의 응답 모양을 본다 (alerts 목록 · DLQ items · quality items 와 quarantine size · usage cost_usd 와 budget daily_usd 가 숫자 · release active).
답하지 않은 영역은 사실을 null, sources_down 에 영역 이름, health 는 unknown, unknown 목록에.
overall 은 red 가 있으면 red, 아니면 yellow 나 unknown 이 있으면 yellow, 아니면 green — 모르는 것을 초록으로 말하지 않는다.
응답은 언제나 HTTP 200. 앞의 칸은 그대로. 기대 결과 cases/lab01-challenge2.json, lab01 · lab01-challenge · lab01-period 도.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `neverError` | 켜지 않으면 출처 하나의 500이 워크플로우 전체를 멈춤 |
| ② | `null` | 0이 아니라 '모름' — 0이면 '비용이 0'으로 읽힘 |
| ③ | `unknown` | 모르는 영역이 있으면 적어도 노랑 |
| ④ | `200` | 다른 다섯 영역의 사실은 쓸 수 있으므로 |

정답: [answers/79-lab01-challenge2-sources.json](answers/79-lab01-challenge2-sources.json)

| 11/01 결과 | |
| --- | --- |
| 고치기 전 (`answers/07`) | **0/3** · 사용량 출처가 멈추면 **500** (사실 전체가 없음) |
| 고친 뒤 (`answers/08`) | **3/3** · 200, `cost: null` · `sources_down: ["cost"]` · `health.cost: "unknown"`, 빨강 셋 그대로, 출처가 돌아오면 🟡 0.9201. `lab01` · `lab01-challenge` · `lab01-period` 5/5 |

- 풀이 때: 비용을 0으로 적었다면 🟢(실제는 92%) — "모르는 것을 좋게 말하는 대시보드가 가장 위험하다".
