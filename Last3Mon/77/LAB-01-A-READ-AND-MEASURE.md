# Lab 01 · 실행 기록을 읽고, 지표로 만들기

> **강사용 정답본** · 학생 저장소에는 수업이 끝난 뒤 올립니다. 학생용 문제는 [LAB-01-Q-READ-AND-MEASURE.md](LAB-01-Q-READ-AND-MEASURE.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 실습을 5개로 늘린 뒤 정답 워크플로우를 학생 순서대로 2026-10-31에 1회씩 실행한 값입니다 (강사 Mac). 지표는 두 주 기록을 정의대로 센 것이라 누가 돌려도 같습니다. 명령 · 출력 전부: [answers/LAB-TEST-RESULT.md](answers/LAB-TEST-RESULT.md).

## 예제 1 · 결과 (에이전트 없이, `answers/01`)

| 질문 | `logs` (그대로) | 기준 보고서 | 다른 까닭 |
| --- | --- | --- | --- |
| 두 주 실행 | 666 | **602** | 기준은 `started_at < to` → 끝날(10/30, 64건)이 빠짐 |
| 오류율 | 21건 · 3.2% | **3.488…** | 백분율 · 반올림 없음 · 분모 602 |
| 10/26 하루 | 70 · 오류 16 | **0 · `null`** | 끝날을 빼니 하루가 통째로 빠짐, 0 / 0 |
| 느린 정도 | (p95는 예제 2) | 평균 1249.2ms | p50 · p95 없음 |
| 오류 갈래 | 오류 21 | 없음 | `route: null`을 건너뜀 (갈래 합 581 ≠ 602) |

- 풀이 때: "기준이 틀렸나?" → 아니오, **정의가 다르다.** 운영 회의에서 "두 주에 602건"이라고 말해 온 것이 문제입니다. 차이 64를 보고 끝날을 의심하는 것이 첫 실마리입니다 (▶ 1단계).
- 하루에 오류 16건(22.9%)이 몰린 것은 Lab 02의 이상 시간대로 이어집니다.

## 예제 2 · 요청문 예

```text
my-work/log-report.json 을 새로 만들어 줘. 웹훅 POST my-log-report, 이름 "77 Log report (my)".
Get logs(HTTP POST http://data-api:8800/logs/query) 에 웹훅 본문의 from · to · tag · source 를 넘기고, source 가 없으면 all.
Compute metrics(Code) 하나에서 AGENTS.md 3절 정의대로 total · errors · error_rate · p50_ms · p95_ms · by_route 를 계산해 줘.
error_rate 는 errors / total 을 소수 4자리 반올림, 0건이면 0.
p50 · p95 는 duration_ms 를 오름차순으로 놓고 ceil(p × n)번째 값 (1부터 셈, 오류 실행도 포함). route 가 null 이면 by_route 의 "오류".
LLM 은 쓰지 않는다. 기대 결과 cases/lab01.json.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `my-log-report` | AGENTS.md 3절 계약 · 테스트 파일의 `webhook` |
| ② | `all` | 두 주 기록(`seed`)과 오늘 실습 기록(`live`)을 모두. 기본값이 없으면 `source`를 안 보낸 요청이 0건 |
| ③ | `4` | 3절 정의. 0.031531…을 0.0315로 (기준 보고서는 3.488…%를 그대로 냄) |
| ④ | `ceil(p × n)` | 가장 가까운 순위(nearest-rank). 666건이면 p95는 633번째. 평균이나 보간이 아님 |

정답: [reference/lab01-example2-report.json](reference/lab01-example2-report.json)

| 10/31 결과 | |
| --- | --- |
| 고치기 전 (`answers/02`, 기준에 같은 테스트) | **0/5** · `total` 602 · 245 · 293 · 0, 오류율 백분율, `p50`/`p95` 없음, `오류` 갈래 없음 |
| 고친 뒤 (`answers/03`) | **5/5** · 두 주 666 · 21 · 0.0315 · p50 1205 · p95 2537, 둘째 주 357 · 0.0588 · p95 2598, 0.1초 안팎 |

## 예제 3 · 결과 (에이전트 없이, `answers/04`)

| 경계 | 내 보고서 | 기준 | 기준이 틀린 까닭 |
| --- | --- | --- | --- |
| 하루 (from = to) | ✔ 70 · 16 | ✘ 0 | 끝날 제외 |
| 빈 기간 | ✔ 0 · 0 · 0 | ✘ `null` | 0 / 0, p95 칸 없음 |
| 주말 | ✔ 0 | ✔ 0 | 우연히 맞음 (실행 없는 날) |
| 기간 없음 | ✔ 666 | ✔ 666 | 우연히 맞음 (거를 것 없음) |
| `source: seed` | ✔ 666 | ✘ 602 | 끝날 제외 |
| `source: live` | ✔ 0 | ✘ **666** | 본문의 `source`를 무시 (`{source: 'all'}` 고정) |

- 내 보고서 **6/6**, 기준 **2/6**. 이 예제의 답: 기준이 맞은 둘은 정의가 맞아서가 아니라 **경계가 문제를 가려서**. `source: live` 666은 Lab 03에서 "오늘 기록만" 볼 때 위험합니다.

## 과제 1 · 요청문 예

```text
my-work/log-report.json 의 Compute metrics 에 by_day 와 by_release 를 더해 줘.
by_day: started_at 앞 10자(날짜)로 묶어 {"2026-10-26": {total, errors, error_rate}}, 날짜순.
by_release: route 가 "자동 답변" 인 실행만 release 로 묶어 {answers, repeats, repeat_rate}.
repeats 는 repeat 가 true 인 수, repeat_rate = repeats / answers (소수 4자리).
앞의 지표는 그대로 둔다. 기대 결과 cases/lab01-challenge.json, cases/lab01.json 도.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `10` | `2026-10-26T09:05:39` → `2026-10-26` |
| ② | `자동 답변` | 답을 준 실행만. 담당자 연결 · 오류는 '다시 물을' 답이 없음 |
| ③ | `true` | 같은 사람이 10분 안에 같은 주제를 다시 물음 (AGENTS.md 2절) |
| ④ | 그대로 | 같은 파일에 더함. `lab01` 5/5가 그대로여야 함 |

정답: [answers/77-lab01-challenge-day-release.json](answers/77-lab01-challenge-day-release.json)

| 10/31 결과 | |
| --- | --- |
| 고치기 전 (`answers/05`) | **0/6** · 칸 없음 |
| 고친 뒤 (`answers/06`) | **6/6** · 10/26 70 · 16 · 0.2286, 10/29 97 · 5, 1.0.0 402 · 19 · 0.0473, 1.1.0 181 · 14 · 0.0773, 1.2.0 **8** · 5 · 0.625. `lab01` 5/5 |

- 팀장에게 답: 오류는 **월요일(16) · 목요일(5)** 이틀뿐. 1.1.0의 다시 묻는 비율이 1.0.0보다 높음(7.73% > 4.73%). 1.2.0의 62.5%는 8건이라 판단 보류 — 비율 옆에 건수.

## 과제 2 · 요청문 예

```text
my-work/log-report.json 의 Compute metrics 에 steps 와 비용을 더해 줘.
steps: faq_ms · answer_ms 마다, steps 의 그 값이 0보다 큰 실행만 모아 {runs, p50, p95} (백분위 정의는 앞과 같음, 없으면 runs 0 · p50 0 · p95 0).
cost_usd: 실행마다 cost_usd 의 합, 소수 5자리 반올림. cost_per_run: cost_usd / total, 소수 6자리 (0건이면 0).
llm_calls: 실행마다 llm_calls 의 합.
앞의 지표는 그대로. 기대 결과 cases/lab01-challenge2.json, lab01 · lab01-challenge 도 그대로 통과.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | 0보다 큰 | 그 단계를 거치지 않은 실행(`잠시 후` 20건은 FAQ도 답도 0)을 빼야 단계의 진짜 시간 |
| ② | `5` | 0.07836처럼 한 건 0.00012달러 단위가 보이게 |
| ③ | 합 | 실행마다 LLM을 부른 횟수(0 또는 1)를 더함 → 596 |
| ④ | `lab01 · lab01-challenge` | 앞에서 통과한 테스트가 그대로인지 (회귀) |

정답: [answers/77-lab01-challenge2-steps-cost.json](answers/77-lab01-challenge2-steps-cost.json)

| 10/31 결과 | |
| --- | --- |
| 고치기 전 (`answers/07`) | **0/5** · 칸 없음 |
| 고친 뒤 (`answers/08`) | **5/5** · 두 주 FAQ p95 39ms (646건) · 답 p50 1179 · p95 2509ms (596건), 월요일 FAQ p95 **1000ms**, 비용 0.07836 · 실행당 0.000118 · 호출 596. `lab01` 5/5 · `lab01-challenge` 6/6 |

- 운영팀에게 답: 평소 느린 것은 **LLM 답 단계**, 월요일에는 **FAQ 단계**(timeout 1초). 0인 단계 값을 넣으면 답 단계 p50이 작아짐 — `runs`(646 · 596)를 함께 보는 까닭.
