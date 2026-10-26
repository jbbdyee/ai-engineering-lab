# Lab 01 · 재고, 단계별 시간을 남기고, 병목 찾기

> **강사용 정답본** · 학생 저장소에 올리지 않습니다. 학생용 문제는 [LAB-01-Q-MEASURE-BOTTLENECK.md](LAB-01-Q-MEASURE-BOTTLENECK.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 정답 워크플로우를 2026-10-18에 1회씩 실행한 값입니다 (강사 Mac, gpt-4.1-mini).
> 10/24에 실습을 5개로 늘리며 정답을 학생 순서대로 다시 돌렸습니다 (45단계). 명령 · `-v` 출력 전부와 codex 프롬프트: [answers/LAB-TEST-RESULT.md](answers/LAB-TEST-RESULT.md).

## 예제 1 · 기준

| 요청 | 결과 |
| --- | --- |
| `base-helpdesk` push 직후 첫 호출 (`faq-vpn`) | 6.5초 |
| `bench base-helpdesk requests/faq-vpn.json -n 5` | p50 2.61초 · p95 2.83초 · 실패 0 |
| `call base-helpdesk` `ticket-own` · `off-topic` | 3.3초 · 3.1초 |

- `off-topic`(점심 메뉴)도 LLM을 세 번 부르고 `route: 자동 답변`으로 "찾지 못했습니다"를 답합니다. 3단계 대체 경로와 2단계 규칙에서 다시 이야기합니다.

## 예제 2 · 요청문 예

```text
my-work/helpdesk.json 은 reference/baseline-helpdesk.json 을 복사한 것이야. 웹훅 경로를 my-helpdesk, 이름을 "72 IT helpdesk (my)"로 바꾸고,
답은 그대로 두고 결과에 다음을 더해 줘 (AGENTS.md 3절, 5절의 시각 남기기).
- Has question? 다음에 Start clock, Parse category 뒤에 After classify, Get ticket 뒤에 After data, Answer 뒤에 After answer, Review 뒤에 After review (각각 Date.now()).
- Build result 에서 timings {classify_ms, data_ms, answer_ms, review_ms, total_ms}, steps(지나간 단계), llm_calls(지나간 Agent 수), cached:false.
  지나갔는지는 $('노드').isExecuted 로.
기대 결과 cases/lab01.json.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `After data` | 다른 시각 노드처럼 "After + 끝난 단계". 데이터(FAQ · 접수 조회)가 끝난 뒤 |
| ② | `Date.now()` | 지금 시각을 ms 숫자로 (AGENTS.md 5절 `Start clock` 예) |
| ③ | `data_ms` | `timings` 칸 이름 규칙 `<단계>_ms` (AGENTS.md 3절) |
| ④ | `$('노드').isExecuted` | 노드가 실행됐으면 true (AGENTS.md 5절) |

정답: [reference/lab01-example2-timings.json](reference/lab01-example2-timings.json)

| 수업 준비 때 결과 | |
| --- | --- |
| `cases/lab01.json` | 4/4 (기준 `--webhook base-helpdesk`는 1/4) |
| `faq-vpn`의 `timings` | classify 524 · data 21 · answer 1017 · review 919 · total 2500 ms (다른 실행: 565 · 23 · 1063 · 879 · 2546) |

- LLM 세 번이 전체의 약 99%. 데이터 API 두 번은 20ms대.
- 10/24 다시 돌린 결과: `lab01` **3/4** — 접수 케이스에서 검토 LLM이 "처리 중"을 "승인 대기 중"으로 바꿔 써 실패 (정답의 잘못이 아님). VPN `timings` 616 · 18 · 1124 · 920 · 2698ms.

## 예제 3 · 결과 (에이전트 없이, 10/24)

예제 2 정답(`reference/lab01-example2-timings.json`) 그대로, 캐시 없음.

| 질문 종류 | p50 | p95 | classify | data | answer | review | total | LLM 몫 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FAQ (VPN) | 2.91초 | 3.08초 | 616 | 18 | 1124 | 920 | 2698 | 98.6% |
| 접수 번호 (T-1002) | 2.99초 | 3.12초 | 818 | 43 | 877 | 895 | 2647 | 97.8% |
| IT 밖 (점심 메뉴) | 2.48초 | 2.84초 | 732 | 19 | 740 | 978 | 2482 | 98.7% |

(p50 · p95는 `bench -n 5`, 단계 칸은 `call -v` 한 번의 ms. FAQ 줄의 단계 칸은 예제 2 `call` 값)

- 학생이 쓸 한 줄 예: "세 종류 모두 LLM이 98%. 점심 메뉴는 데이터가 없는데도 LLM 세 번 → 규칙으로 걸러 낼 후보."
- 같은 실행에서 `lab01` 접수 케이스가 한 번 실패했습니다 (검토 LLM이 "처리 중"을 "승인 대기 중"으로 바꿈). Lab 02 과제 1의 이야기 거리.

## 과제 1 · 요청문 예

```text
my-work/helpdesk.json 의 Search FAQ 와 Get ticket 사이에 After FAQ(Date.now()) 를 더해, timings 의 data_ms 를 faq_ms 와 ticket_ms 로 나눠 줘.
total_ms 를 뺀 timings 중 가장 큰 단계 이름(_ms 뺀 것)을 slowest_step 으로. cases/lab01-challenge.json, cases/lab01.json 둘 다 통과.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `After FAQ` | FAQ 검색이 끝난 뒤의 시각 노드 |
| ② | `faq_ms` | `cases/lab01-challenge.json`의 `expect` 칸 이름 |
| ③ | `ticket_ms` | ②와 짝. `data_ms`를 FAQ와 접수 조회로 나눔 |
| ④ | 가장 큰 | "가장 느린" = `_ms` 값이 가장 큰 칸 |

정답: [answers/72-lab01-challenge-timings.json](answers/72-lab01-challenge-timings.json)

| 수업 준비 때 결과 | |
| --- | --- |
| `cases/lab01-challenge.json` | 4/4 (예제 2 상태 0/4) |
| `cases/lab01.json` | 4/4 |
| `faq-vpn` | classify 565 · faq 14 · ticket 9 · answer 1063 · review 879 · total 2546 ms, `slowest_step: answer` |

10/24 다시 돌린 결과: `lab01-challenge` 4/4, `slowest_step`은 네 번 중 answer 2 · review 1 · classify 1 (push 직후 첫 호출에서 classify 1365ms).

## 과제 2 · 요청문 예

```text
my-work/helpdesk.json 의 Build result 에서, 본문 budget_ms (없으면 3000, 숫자로)를 읽어
결과에 llm_ms(classify · answer · review 의 _ms 합, timings 밖에 둔다), budget_ms, over_budget(timings.total_ms > budget_ms)을 더해 줘.
timings, slowest_step 은 그대로. cases/lab01-challenge2.json, cases/lab01-challenge.json, cases/lab01.json 모두 통과.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `budget_ms` | 본문 입력 칸 = 결과 칸 이름 (AGENTS.md 3절 "입력") |
| ② | `3000` | 기본 예산 3초 (조건 표 · AGENTS.md 3절) |
| ③ | 밖 | `timings` 안에 두면 `slowest_step`이 `llm` 합계를 고르게 됨 |
| ④ | `timings.total_ms` | 요청 하나 전체 시간 |

정답: [answers/72-lab01-challenge2-budget.json](answers/72-lab01-challenge2-budget.json) (과제 1 정답의 `Build result`에 세 줄)

| 10/24 결과 | |
| --- | --- |
| 고치기 전 (과제 1 정답) | `lab01-challenge2` 0/4 (칸이 없음) |
| 고친 뒤 | `lab01-challenge2` 4/4 · `lab01-challenge` 4/4 · `lab01` 4/4 |
| 예산 60000 | `total_ms` 3357 (push 직후) · `llm_ms` 3295 · `over_budget: false` |
| 예산 500 | 2609 · 2563 · `true` |
| 기본 3000 (VPN) | 3023 · 2973 · **`true`** (23ms 넘음) |
| 기본 3000 (접수) | 2904 · 2858 · `false` |

- 기본 예산에서 `over_budget`이 실행마다 바뀌는 것이 정상입니다 (VPN이 3초 안팎). 풀이 때 "그래서 2단계에서 줄인다"로 잇습니다.
- 처음 만든 케이스 파일은 접수 케이스에 답 "처리 중"을 기대했는데, 검토 LLM이 문장을 바꿔 실패했습니다 (10/24). 모양을 보는 테스트이므로 `category: ticket`으로 바꿨습니다.
