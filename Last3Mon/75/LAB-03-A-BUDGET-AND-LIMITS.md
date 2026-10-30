# Lab 03 · 하루 예산, 사용자별 한도, 비용 보고서, 바꾸면 얼마

> **강사용 정답본** · 학생 저장소에 올리지 않습니다. 학생용 문제는 [LAB-03-Q-BUDGET-AND-LIMITS.md](LAB-03-Q-BUDGET-AND-LIMITS.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 정답 워크플로우를 학생 순서대로 2026-10-28에 1회씩 실행한 값입니다. 명령 · 출력 전부: [answers/LAB-TEST-RESULT.md](answers/LAB-TEST-RESULT.md).

## 예제 1 · 요청문 예

```text
my-work/cost.json 의 Get ticket 뒤에 Within budget?(If) 을 넣어 Get budget 의 over 이 false 일 때만 Rule classify 로, 넘었으면 Over budget(Code) → Send over budget.
Over budget 은 LLM 없이: 접수 건이 있으면 그 상태 · 메모, FAQ 가 있으면 첫 FAQ 의 answer 원문에 "(오늘 자동 답변 한도를 넘어 FAQ 원문으로 안내합니다.)" 를 붙여.
결과는 route ' 한도 초과 ', llm_calls 0, cost_usd 0 , usage 의 토큰도 0.
기대 결과 cases/lab03.json.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `over` | `/budget`이 주는 true/false (`used_usd >= daily_usd`) |
| ② | `answer` | FAQ 항목의 답 글자 |
| ③ | `한도 초과` | AGENTS.md 3절 `route` (72일차 LLM이 멈췄을 때의 `간단 답변`과 다르게) |
| ④ | `0` | LLM을 부르지 않음 |

정답: [reference/lab03-example1-budget.json](reference/lab03-example1-budget.json)

| 10/28 결과 (`cases/lab03.json`) | 고치기 전 (Lab 02 과제 2 정답, `answers/16`) | 고친 뒤 (`answers/17`) |
| --- | --- | --- |
| 한도를 넘으면 · FAQ 원문 | ✘ `자동 답변` · 1 call · $0.000154 | ✔ `한도 초과` · 0 calls · $0 · "인증서" |
| 한도를 넘으면 · 접수 원문 | ✘ `자동 답변` · $0.000115 | ✔ `한도 초과` · "처리 중" |
| 한도 안이면 평소대로 | ✔ | ✔ $0.000156 |
| 합계 | 1/3 | **3/3** |

## 예제 2 · 요청문 예

```text
my-work/cost.json 의 Get budget 바로 뒤(가장 앞)에 Recent requests(HTTP GET http://data-api:8800/usage/user/<user>?window= 60 ) 를 넣어 줘.
Under user limit?(If) 로 count 가 Get budget 의 user_limit_per_min 보다 작으면 Get prices 로, 아니면 Too many(Respond, HTTP 429 ).
Too many 의 본문은 {route: '잠시 후', answer, retry_after: 60, llm_calls: 0, cost_usd: 0}. 이 갈래는 FAQ · 접수 조회도 하지 않는다 .
기대 결과 cases/lab03-limit.json, cases/lab03.json, cases/lab02-challenge.json.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `60` | 1분 = 60초 (이동 창) |
| ② | `user_limit_per_min` | `/budget`의 사용자별 1분 한도 |
| ③ | `429` | Too Many Requests |
| ④ | 하지 않는다 | 맨 앞에서 돌려보내 0원 · 0.0초 |

정답: [reference/lab03-example2-limit.json](reference/lab03-example2-limit.json)

| 10/28 결과 (`cases/lab03-limit.json`) | 고치기 전 (예제 1 정답, `answers/18`) | 고친 뒤 (`answers/19`) |
| --- | --- | --- |
| 이준호 1 · 2번째 | ✔ | ✔ |
| 이준호 3번째 | ✘ 200 · 1.3초 · $0.000156 | ✔ **429 · 0.0초 · $0** |
| 다른 사람 | ✔ | ✔ |
| 합계 | 3/4 | **4/4** |
| `lab03` · `lab02-challenge` | | 3/3 · 7/7 |

## 예제 3 · 결과 (에이전트 없이)

| `answers/20` | 예산 $0.0003 | `--reset` 뒤 ($1.0) |
| --- | --- | --- |
| 1 · 2 · 3번째 (VPN · 프린터 · 비밀번호) | `자동 답변` $0.000141 · 0.000152 · 0.000136 | `자동 답변` |
| 4 · 5 · 6번째 (메일 · 접수 · VPN) | **`한도 초과` · 0 calls · $0** (0.0 ~ 0.1초) | `자동 답변` |
| 쓴 돈 | $0.000430 (예산을 $0.00013, **43%** 넘음) | |

- 두 번째까지 $0.000293으로 예산 아래 → 세 번째도 답함 → 넘음. "예산은 넘은 뒤 멈춘다"를 숫자로.
- `usage`의 route별에는 `자동 답변` 3줄만 — 한도 초과 세 건은 기록이 없습니다.
- `budget --daily 0.0003` 직후의 사용액 $0.000934는 앞 단계 기록입니다 (테스트의 `before`가 비우고 시작). 학생 화면에서도 비슷하게 보이므로 풀이 때 짚습니다.
- 풀이 질문: "넘지 않게 하려면?" → 남은 금액 < 한 건 최대 비용이면 멈춤. 한 건 최대 비용은 Lab 02 과제 2의 입력 상한(긴 질문 $0.00026) + 출력 상한으로 정해집니다.

## 과제 1 · 요청문 예

```text
my-work/cost-report.json 에 새 워크플로우: 웹훅 my-cost-report 에서 Get summary(GET http://data-api:8800/usage/summary) → Get budget(GET http://data-api:8800/budget) → Make report(Code) → Send report.
avg_usd = cost_usd ÷ requests (calls 아님). projected_month_usd = avg_usd × requests_per_day × workdays (기본 22 , requests_per_day 가 없으면 지금 요청 수).
top_user 는 by_user 에서 cost_usd 가 가장 큰 사람. by_model 은 모델마다 cost_usd. 금액은 소수 6 자리에서 반올림 (반올림은 마지막에). LLM 은 쓰지 않는다.
결과 칸은 AGENTS.md 3절 비용 보고서. 기대 결과 cases/lab03-challenge.json.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `my-cost-report` | `cases/lab03-challenge.json`의 `webhook` |
| ② | `requests` | 요청 수 (`request_id`가 다른 것). `calls`로 나누면 평균이 작아짐 |
| ③ | `22` | AGENTS.md 3절 `workdays` 기본값 |
| ④ | `6` | AGENTS.md 3절 보고서 반올림 자리 |

정답: [answers/75-lab03-challenge-report.json](answers/75-lab03-challenge-report.json)

손 계산 (`before`의 네 줄):

| | 값 |
| --- | --- |
| 요청 · 호출 | r1 · r2 · r3 → 3 · 4줄 |
| 비용 합 | 0.00056 + 0.000045 + 0.00112 + 0.000264 = **0.001989** |
| 평균 | 0.001989 ÷ 3 = 0.000663 |
| 100건 × 22일 | 0.000663 × 2,200 = **1.4586** |
| 사람별 | 이준호 0.000869 · 박서연 0.00112 → **박서연** |
| 남은 예산 | 1.0 − 0.001989 = 0.998011 |

| 10/28 결과 | 고치기 전 (`answers/21`) | 고친 뒤 (`answers/22`) |
| --- | --- | --- |
| `cases/lab03-challenge.json` | 0/5 (404, 웹훅 없음) | **5/5** |
| 실제 사용량 (`lab02-challenge` 일곱 건) · `requests_per_day` 1000 | | 평균 $0.000127 · **한 달 $2.80** · top 이준호 |

- 이 기록의 "고치기 전"은 수업 준비 때 미리 올려 둔 `my-cost-report`를 `off`로 내린 뒤 잰 것입니다. 학생은 처음이라 그대로 404.
- 한 달 $2.80은 Lab 01 예제 3의 어림 $20.8의 약 7분의 1. 오늘 줄인 것의 결과를 한 숫자로 보여 줍니다.

## 과제 2 · 요청문 예

```text
my-work/cost-report.json 의 Get budget 뒤에 Get prices(GET http://data-api:8800/prices) 를 넣어 줘.
본문에 what_if_model 이 있으면 Make report 에서 by_model 의 prompt_tokens · completion_tokens 합을 그 모델의 단가(input · output) 로 다시 계산해
what_if: {model, cost_usd, saving_usd, projected_month_usd} 를 더해 줘. saving_usd = 지금 cost_usd − what_if.cost_usd .
단가표에 없는 모델이면 Known model?(If) 로 갈라 HTTP 400 {error: 'unknown model', model, known}.
what_if_model 이 없으면 결과는 과제 1 과 같다 .
기대 결과 cases/lab03-challenge2.json, cases/lab03-challenge.json.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | 단가(`input` · `output`) | `/prices`의 그 모델 값 |
| ② | `what_if.cost_usd` | 새 모델로 다시 계산한 비용 |
| ③ | `400` | 74일차 "없는 릴리스"와 같음 |
| ④ | 같다 | 과제 1 테스트가 그대로 통과해야 함 |

정답: [answers/75-lab03-challenge2-what-if.json](answers/75-lab03-challenge2-what-if.json)

손 계산: 입력 합 1,000 + 100 + 2,000 + 500 = 3,600, 출력 합 100 + 20 + 200 + 40 = 360.

| what-if | 식 | 값 |
| --- | --- | --- |
| 모두 nano | (3,600 × 0.20 + 360 × 1.25) ÷ 10⁶ | **0.00117** · 아낌 0.000819 · 한 달 0.858 |
| 모두 mini | (3,600 × 0.40 + 360 × 1.60) ÷ 10⁶ | 0.002016 · 아낌 **−0.000027** |

| 10/28 결과 (`cases/lab03-challenge2.json`) | 고치기 전 (과제 1 정답, `answers/23`) | 고친 뒤 (`answers/24`) |
| --- | --- | --- |
| 모두 nano였다면 | ✘ `what_if` 없음 | ✔ |
| 원래 숫자는 그대로 | ✔ | ✔ |
| 모두 mini였다면 · 음수 | ✘ | ✔ |
| 없는 모델은 400 | ✘ 200 | ✔ 400 · `known` |
| what_if 없이 | ✔ | ✔ |
| 합계 | 2/5 | **5/5** |
| `lab03-challenge` · `lab02-challenge` | | 5/5 · 7/7 |
| 실제 사용량 일곱 건 · nano | | $0.000929 → $0.00061 (34% 덜) · 한 달 $2.92 → $1.92 |

- 풀이 때: what-if는 34% 덜 든다고 하지만 같은 토큰 수를 가정한 숫자입니다. Lab 02 예제 3에서 **실제로** 답 단계만 nano로 바꿔 잰 평균은 15% 덜 들었고 (다른 구성이라 바로 비교할 수는 없음) 답의 형식이 나빠졌습니다. "숫자로 해 볼 만한지 보고, 바꿀지는 게이트로" — 74일차와 잇습니다.
