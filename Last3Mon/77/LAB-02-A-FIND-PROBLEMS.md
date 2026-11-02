# Lab 02 · 문제를 숫자로 찾고, 요약하기

> **강사용 정답본** · 학생 저장소에는 수업이 끝난 뒤 올립니다. 학생용 문제는 [LAB-02-Q-FIND-PROBLEMS.md](LAB-02-Q-FIND-PROBLEMS.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 2026-10-31 정답 워크플로우 1회 실행 값입니다. 명령 · 출력 전부: [answers/LAB-TEST-RESULT.md](answers/LAB-TEST-RESULT.md).

## 예제 1 · 요청문 예

```text
my-work/log-report.json 의 Compute metrics 에 failures 와 unanswered_topics 를 더해 줘.
failures: status 가 error 인 실행을 (error_node, error_message) 로 묶어 [{node, message, count}], 많은 순.
unanswered_topics: route 가 "담당자 연결" 인 실행을 topic 으로 묶어 [{topic, count}], 많은 순.
담당자 연결은 status 가 success 라 failures 에 넣지 않는다. 앞의 지표는 그대로. 기대 결과 cases/lab02.json 앞 세 케이스.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `error_node` | 어느 노드에서 · 무슨 말로 실패했나가 원인의 단위 |
| ② | `담당자 연결` | 답을 못 해 사람에게 넘긴 실행 |
| ③ | `topic` | 무엇을 물었나로 묶어야 FAQ에 무엇이 없는지 보임 |
| ④ | 넣지 않는다 | `status`는 `success` — 오류가 아닌 실패. 따로 셈 |

정답: [reference/lab02-example1-problems.json](reference/lab02-example1-problems.json)

| 10/31 결과 | |
| --- | --- |
| 고치기 전 (`answers/09`) | **0/6** · 칸 없음 |
| 고친 뒤 (`answers/10`) | **3/6** (예제 1 셋 ✔) · `Search FAQ` timeout 16 · `Answer` 429 5 · 담당자 연결 와이파이 **34** |

**문제 목록 (`OPS.md` 3.1 예)**

| 순위 | 문제 | 숫자 | 영향 | 고칠 곳 · 누가 |
| --- | --- | --- | --- | --- |
| 1 | 와이파이 FAQ 없음 | 담당자 연결 34 (두 주), 답 못 함 5.11% | 사용자가 답을 못 받음 · 담당자 일 | FAQ 더하기 — 사람 (Lab 03) |
| 2 | FAQ 검색 timeout | 오류 16, 10/26 09시 16/16 | 그 시간 질문 모두 실패 | Search FAQ timeout · 재시도 — 에이전트 (Lab 03) |
| 3 | LLM 429 | 오류 5, 10/29 15시 5/7 | 그 시간 답 실패 | 사용량 한도 · 대체 경로 (75 · 72일차) |

- 풀이 때: 와이파이(34)를 1위로 둘 수 있는지 토론 — 오류율(3.15%)에는 안 보이지만 건수는 오류보다 많습니다.

## 예제 2 · 요청문 예

```text
my-work/log-report.json 의 Compute metrics 에 anomalies 를 더해 줘.
started_at 앞 13자(예 2026-10-26T09)로 시간마다 묶어 {hour, total, errors, error_rate}.
실행이 5건 이상이고, error_rate 가 그 기간 전체 error_rate 의 3배 이상이고, 오류가 1건 이상인 시간만 시간순으로.
앞의 지표는 그대로. 기대 결과 cases/lab02.json 전체.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `13` | `2026-10-26T09`까지 = 날짜 + 시 |
| ② | `5` | 표본이 작은 시간(1건 중 1건 실패 = 100%)을 뺌 |
| ③ | `3` | 그 기간 전체 오류율의 3배 — 평소보다 크게 나쁜 시간 |
| ④ | 시간순 | 케이스가 `anomalies.0` · `.1`을 순서대로 봄 |

정답: [reference/lab02-example2-anomalies.json](reference/lab02-example2-anomalies.json)

| 10/31 결과 | |
| --- | --- |
| 고치기 전 | **3/6** (예제 1 뒤 그대로) |
| 고친 뒤 (`answers/11`) | **6/6** · 10/26 09시 16 · 16 · 1, 10/29 15시 7 · 5 · 0.7143, 첫 주 `[]`. `lab01-challenge2` 5/5 |

- 16 + 5 = 21 = 두 주 오류 전부 → "두 번의 사건". 09시 = FAQ timeout, 15시 = 429 (원인 묶음과 시간대가 1:1).

## 예제 3 · 결과 (에이전트 없이, `answers/12`)

| 기간 | 전체 오류율 | 문턱 (× 3) | 이상 시간대 |
| --- | --- | --- | --- |
| 첫 주 | 0 | 0 | 없음 (오류 1건 이상 조건) |
| 둘째 주 | 0.0588 | 0.1764 | 09시 · 15시 |
| 월요일만 | 0.2286 | 0.6858 | 09시 |
| 목요일만 | 0.0515 | 0.1545 | 15시 |
| 두 주 | 0.0315 | 0.0945 | 둘 다 |

- **5/5.** 이 예제의 답: 문턱이 기간에 따라 일곱 배 넘게 달라짐. 사건이 비교 기준을 끌어올림 (월요일). 보고에는 기준 기간을 함께.

## 과제 1 · 요청문 예

```text
my-work/log-report.json 의 Compute metrics 에 repeat_topics 를 더해 줘.
route 가 "자동 답변" 인 실행만 topic 으로 묶어 {topic, answers, repeats, repeat_rate}. repeats 가 0 인 주제는 뺀다.
정렬은 repeat_rate 가 높은 순, 같으면 repeats 가 많은 순. repeat_rate 는 repeats / answers, 소수 4자리.
앞의 지표는 그대로. 기대 결과 cases/lab02-challenge.json, cases/lab02.json 도.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `topic` | 어느 주제의 답이 도움이 안 됐나 |
| ② | `0` | 다시 묻지 않은 주제는 문제 목록에서 뺌 |
| ③ | 높은 | 수(비밀번호 9)가 아니라 비율(프린터 9.88%)이 답의 질 |
| ④ | `answers` | 그 주제에 답한 수가 분모 (전체 실행 수가 아님) |

정답: [answers/77-lab02-challenge-repeat-topics.json](answers/77-lab02-challenge-repeat-topics.json)

| 10/31 결과 | |
| --- | --- |
| 고치기 전 (`answers/13`) | **1/5** · 회귀 케이스만 ✔ |
| 고친 뒤 (`answers/14`) | **5/5** · 프린터 81 · 8 · 0.0988, 비밀번호 139 · 9 · 0.0647, VPN 0.0645, 접수 현황 0.0625, 메일 0.0556, 설치 0.0328. `lab02` 6/6 |

- 팀장에게 답: **프린터 FAQ**부터 (비율 1위). 비밀번호는 수(9)로는 1위지만 많이 묻는 주제라서. 와이파이는 "답 못 함" 목록 쪽.

## 과제 2 · 요청문 예

```text
my-work/log-summary.json 을 새로 만들어 줘. 웹훅 POST my-log-summary, 이름 "77 Log summary (my)".
Get report: 지표를 다시 계산하지 말고 HTTP POST http://localhost:5678/webhook/my-log-report 로 부른다 (본문 from · to · tag · source 그대로, timeout 30000).
Write summary(AI Agent + OpenAI gpt-4.1-mini, temperature 0): 통계 중 total · errors · error_rate · failures · unanswered_topics · anomalies 만 JSON 으로 주고, 한국어 3문장으로
가장 많은 답 못 한 주제와 수 · 가장 많은 실패(노드 · 메시지 · 수) · 가장 나쁜 시간대(10월 26일 09시처럼). 통계에 없는 숫자와 짐작한 원인은 쓰지 않는다.
Check numbers(Code): 요약 글의 숫자를 모두 뽑아, 통계의 값 · 비율의 ×100 · 키와 글자 속 숫자(날짜 · 시간)에 있는지 본다. 없는 숫자는 unknown_numbers 에, 하나도 없으면 numbers_ok true.
결과 {summary, numbers_ok, unknown_numbers, top_topic, worst_hour}. 기대 결과 cases/lab02-challenge2.json.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `my-log-report` | 지표를 다시 쓰지 않고 이미 있는 보고서를 부름 — 정의가 한 벌 |
| ② | `3` | 팀장 회의용 세 문장 |
| ③ | `unknown_numbers` | 통계에 없는 숫자를 모아 보여 줌 (지어낸 숫자 찾기) |
| ④ | `true` | 모르는 숫자가 하나도 없을 때만 |

정답: [answers/77-lab02-challenge2-summary.json](answers/77-lab02-challenge2-summary.json)

| 10/31 결과 | |
| --- | --- |
| 고치기 전 (`answers/15`) | **0/3** · 404 |
| 고친 뒤 (`answers/16`) | **3/3** (1.7~3.4초) · 둘째 주 요약 "와이파이로 17건 … timeout of 1000ms exceeded … 16건 … 10월 26일 09시 … 16건 중 16건", `numbers_ok: true` |

- 풀이 때: 숫자 확인을 일부러 깨 보기 — 지시문에서 "통계에 있는 숫자만"을 빼거나 "대략적으로"를 넣으면 `unknown_numbers`에 무엇이 들어오나 (수업 준비 때는 재지 않음).
