# Lab 03 · 고치고, 다시 돌려 재고, 보고하기

> **강사용 정답본** · 학생 저장소에는 수업이 끝난 뒤 올립니다. 학생용 문제는 [LAB-03-Q-IMPROVE-AND-REMEASURE.md](LAB-03-Q-IMPROVE-AND-REMEASURE.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 2026-10-31 정답 워크플로우 1회 실행 값입니다. 오늘 실습 기록의 시간(ms)은 실행마다 다릅니다. 명령 · 출력 전부: [answers/LAB-TEST-RESULT.md](answers/LAB-TEST-RESULT.md).

## 예제 1 · 요청문 예

```text
my-work/helpdesk.json (제공 helpdesk-live 를 복사한 것) 의 Search FAQ 노드만 고쳐 줘.
options.timeout 을 1000 에서 3000 으로, 그리고 retryOnFail true, maxTries 2, waitBetweenTries 300 (parameters 밖, 노드 바로 아래).
그래도 실패하면 지금처럼 오류 출력(onError continueErrorOutput)으로 Failed → Log Failed 에 기록한다.
다른 노드와 로그 모양(steps 포함)은 그대로. 기대 결과 cases/replay-after.json (FAQ 가 1.2초 느린 동안 10/10), cases/lab03.json.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `3000` | 느릴 때 FAQ가 1.2초 — 1초에 끊으면 모두 실패. 로그의 평소 `faq_ms`는 20~40ms |
| ② | `true` | 잠깐의 끊김은 한 번 더 (72 · 76일차) |
| ③ | `continueErrorOutput` | 실패도 로그에 남겨야 다음 주 보고서에 보임 |
| ④ | 그대로 | 로그 모양이 바뀌면 보고서의 정의가 깨짐 |

정답: [reference/lab03-example1-helpdesk-fixed.json](reference/lab03-example1-helpdesk-fixed.json) · FAQ: `requests/faq-wifi.json` (사람이 `faq/add`)

| 10/31 결과 | |
| --- | --- |
| 고치기 전 (`answers/17`) | `replay-before` 10/10(200만 봄) · 기록 **10건 모두 오류** (`Search FAQ`, 약 1030ms) · `lab03` **3/4** ("답하지 못한 주제 없음"은 0건이라 우연히 ✔) |
| 고친 뒤 (`answers/18`) | `replay-after` **10/10** (모두 자동 답변, 와이파이 `CORP-WIFI`, 한 건 2.3~4.5초) · `lab03` **4/4** · `ops` before 10 · after 10 · FAQ-007 |

- 풀이 때: timeout만 · FAQ만 고쳤다면 각각 무엇이 ✘인가 (FAQ만: 10 오류, timeout만: 와이파이 5개 담당자 연결).

## 예제 2 · 요청문 예

```text
my-work/log-report.json 의 Compute metrics 에 unanswered_rate 와 slo 를 더해 줘.
unanswered_rate = "담당자 연결" 수 / total (소수 4자리).
기준 limits 는 기본 error_rate 0.01 · p95_ms 3000 · unanswered_rate 0.02, 웹훅 본문에 slo 가 있으면 그 값으로 덮어쓴다 (본문은 $('Report webhook').first().json.body).
지표가 기준보다 크면 그 이름을 breaches 에 넣고, slo = {ok: breaches 가 비었으면 true, breaches, limits}.
앞의 지표는 그대로. 기대 결과 cases/lab03-slo.json.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `0.01` | AGENTS.md 3절 기본 기준 (오류율 1%) |
| ② | `3000` | p95 3초 |
| ③ | 크면 | 같으면 지킨 것 (`>`) |
| ④ | 비었으면 true | 어긴 지표가 하나도 없을 때만 지킴 |

정답: [reference/lab03-example2-slo.json](reference/lab03-example2-slo.json)

| 10/31 결과 | |
| --- | --- |
| 고치기 전 (`answers/19`) | **0/4** · 칸 없음 |
| 고친 뒤 (`answers/20`) | **4/4** · 둘째 주 `[error_rate, unanswered_rate]` (0.0476), 첫 주 `[unanswered_rate]`, 기준 0.06이면 지킴. 고친 뒤 기록 오류 0 · 답 못 함 0, **p95 3560 > 3000 → `[p95_ms]`**. `lab02-challenge` 5/5 |

## 예제 3 · 결과 (에이전트 없이, `answers/21`)

| 기록 | FAQ | 오류 | FAQ 단계 p50 · p95 | 답 단계 p50 | 전체 p95 | SLO |
| --- | --- | --- | --- | --- | --- | --- |
| `before` | 느림 | 10 | 1043 · 1098ms | 0 | 1098ms | `error_rate` |
| `after` | 느림 | 0 | 1238 · 1278ms | 1103ms | 3560ms | `p95_ms` |
| `normal` | 평소 | 0 | 17 · 39ms | 997ms | 2147ms | 지킴 |

- `replay-normal` **10/10** (0.8~2.3초), `lab03-cost` **4/4**. 이 예제의 답: 늘어난 시간은 모두 FAQ 단계 — timeout은 "견디기"이고 "빠르게"가 아님. 진짜 고칠 곳은 FAQ 검색이 느려지는 원인.

## 과제 1 · 요청문 예

```text
my-work/weekly.json 을 새로 만들어 줘. 웹훅 POST my-weekly, 본문 from · to · prev_from · prev_to, 이름 "77 Weekly report (my)".
This week · Last week: my-log-report 를 두 번 부른다 (이번 주 from · to, 지난주 prev_from · prev_to). Summary: my-log-summary 를 이번 주로 부른다 (timeout 60000).
Write report(Code)가 마크다운을 만든다. ## 숫자: | 지표 | 지난주 | 이번 주 | 표 (요청 · 오류율 · p95 · 답 못 함 · SLO), 비율은 0.0588 을 5.88%처럼.
## 문제: 실패 · 답하지 못한 질문 · 이상 시간대("2026-10-26 09시"). ## 요약: LLM 요약과 숫자 확인 결과.
## 다음 할 일: LLM 이 아니라 규칙으로 — 답 못 한 주제가 있으면 "FAQ에 '<주제>' 항목 추가", Search FAQ 실패가 있으면 timeout 점검, 429 가 있으면 사용량 한도 점검.
결과 {markdown, total, error_rate, slo_ok, numbers_ok}. 기대 결과 cases/lab03-challenge.json.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `my-log-summary` | Lab 02 과제 2의 요약을 다시 부름 (숫자 확인 포함) |
| ② | `5.88%` | 사람이 읽는 보고 — ×100, 소수 2자리 |
| ③ | 규칙 | 문제 → 할 일이 정해져 있으면 규칙이 늘 같게 씀. LLM은 요약만 |
| ④ | `numbers_ok` | 요약의 숫자 확인 결과를 보고와 함께 |

정답: [answers/77-lab03-challenge-weekly.json](answers/77-lab03-challenge-weekly.json)

| 10/31 결과 | |
| --- | --- |
| 고치기 전 (`answers/22`) | **0/7** · 404 |
| 고친 뒤 (`answers/23`) | **7/7** (1.7~3.6초) · 요청 309 → 357, 오류율 0% → 5.88%, p95 2525 → 2598ms, 답 못 함 5.5% → 4.76%, SLO 위반 1 → 2, 문제 다섯 줄, 할 일 셋 (규칙) |

## 과제 2 · 요청문 예

```text
my-work/slo-alert.json 을 새로 만들어 줘. 웹훅 POST my-slo-alert, 본문 from · to · tag · source · slo, 이름 "77 SLO alert (my)".
Get report: my-log-report 를 부른다 (본문 그대로). Recent alerts: POST http://data-api:8800/alerts/list {workflow: "slo", reason: "slo", within: 600}.
Decide(Code): breaches 가 없으면 alert "none", 있는데 10분 안의 같은 알림이 있으면 "suppressed", 아니면 "sent".
message 는 "SLO breach: error_rate 0.0588 > 0.01, …" 처럼 지표 · 값 · 기준. Send it?(If): sent 일 때만 POST /alerts {workflow: "slo", severity: "high", reason: "slo", breaches, message}.
두 갈래 모두 같은 결과 {ok, breaches, alert, message, total} 로 응답. 기대 결과 cases/lab03-challenge2.json.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `600` | 10분 = 600초 (76일차 알림 폭주 막기와 같음) |
| ② | `suppressed` | 보내지 않았다는 것도 결과에 남김 |
| ③ | `high` | SLO 위반은 급하지만 문의를 잃는 중은 아님 (76일차 등급) |
| ④ | 응답 | sent · suppressed · none 어느 갈래든 같은 모양 |

정답: [answers/77-lab03-challenge2-slo-alert.json](answers/77-lab03-challenge2-slo-alert.json)

| 10/31 결과 | |
| --- | --- |
| 고치기 전 (`answers/24`) | **0/6** · 404, 알림 0 |
| 고친 뒤 (`answers/25`) | **6/6** · 둘째 주 `sent` → 다시 `suppressed` → 알림 1개, 첫 주 기준 0.06 `none`. 알림 `[high] slo · SLO breach: error_rate 0.0588 > 0.01, unanswered_rate 0.0476 > 0.02`. `lab03-slo` 4/4 |

- 76일차 Lab 02 과제 2(알림 폭주 막기)와 같은 모양이라는 것을 짚습니다: 판정 → 최근 같은 알림 → 보낼지. 79일차 Ops Assistant로 이어집니다.
