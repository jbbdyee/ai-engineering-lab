# Lab 01 · 자원과 토큰을 재고, 비용을 계산하고, 기록하기

> **강사용 정답본** · 학생 저장소에 올리지 않습니다. 학생용 문제는 [LAB-01-Q-MEASURE-USAGE.md](LAB-01-Q-MEASURE-USAGE.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 실습을 5개로 늘린 뒤 정답 워크플로우를 학생 순서대로 2026-10-28에 1회씩 실행한 값입니다 (강사 Mac, `gpt-4.1-mini` · `gpt-5.4-nano`, 단가는 OpenAI 모델 문서 2026-10-28 확인). 명령 · 출력 전부: [answers/LAB-TEST-RESULT.md](answers/LAB-TEST-RESULT.md).

## 예제 1 · 결과 (에이전트 없이)

| 자원 (`docker stats`, `answers/01`) | CPU | 메모리 |
| --- | --- | --- |
| n8n | 0.27% | 642.6MiB |
| runners | 0.21% | 100.5MiB |
| data-api | 0.02% | 20.3MiB |

| `call base-cost` | 단계 | 입력 | 출력 |
| --- | --- | --- | --- |
| VPN | classify | 78 | 6 |
| VPN | answer | **1,781** | 78 |
| VPN | review | 140 | 66 |
| VPN | 합 | 1,999 | 150 |
| T-1002 | 합 (answer) | 1,973 (**1,791**) | 97 |

- 손 계산: (1,999 × 0.40 + 150 × 1.60) ÷ 1,000,000 = **$0.00104**. 하루 1,000건 × 22일 ≈ $22.9.
- 풀이 때: "answer 입력이 왜 질문 종류와 관계없이 1,780토큰인가?" → 지시문에 붙은 사내 규정 전체. Lab 02 예제 1로.

## 예제 2 · 요청문 예

```text
my-work/cost.json (baseline 을 복사한 것) 의 웹훅 경로를 my-cost 로, 이름을 "75 IT helpdesk (my)" 로 바꿔 줘.
Has question? 뒤에 Get prices(HTTP GET http://data-api:8800/ prices ) 를 넣어 줘.
Build result 에서 단계마다 cost_usd = (prompt_tokens × input + completion_tokens × output) ÷ 1000000 를
그 단계 model 의 단가로 계산해 usage.by_step.<단계>.cost_usd 에, 합을 cost_usd 에 넣어 줘. 소수 8 자리에서 반올림.
기대 결과 cases/lab01.json.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `my-cost` | `cases/lab01.json`의 `webhook` (AGENTS.md 3절) |
| ② | `prices` | 단가를 주는 주소 `GET /prices` (AGENTS.md 2절) |
| ③ | `1000000` | 단가 단위가 "per 1M tokens" |
| ④ | `8` | AGENTS.md 3절 `cost_usd` 반올림 자리 |

정답: [reference/lab01-example2-cost.json](reference/lab01-example2-cost.json)

| 10/28 결과 | |
| --- | --- |
| `cases/lab01.json` (`answers/02`) | **3/3** · VPN $0.001040 (손 계산과 같음) · 접수 $0.000946 |

## 예제 3 · 결과 (에이전트 없이)

| `lab01-mix` (`answers/03`) | 비용 ($) |
| --- | --- |
| FAQ · VPN · 프린터 · 비밀번호 · 메일 | 0.001040 · 0.000960 · 0.000953 · 0.000965 (평균 0.000980) |
| 접수 · T-1002 · T-1001 | 0.000946 · 0.000890 (평균 0.000918) |
| 규칙에 없는 질문 | 0.000830 |
| 합계 | **7/7**, 모두 3 calls |

- 가중(60 · 30 · 10%): $0.000946 × 1,000 × 22 ≈ **$20.8**. 단순 평균: ≈ $20.7. 두 어림이 거의 같은 까닭이 이 예제의 답입니다 — **고정비(규정 전체)가 커서 질문 종류가 비용을 거의 바꾸지 않습니다.**
- Lab 02 과제 1 뒤에는 질문마다 $0.000097 ~ $0.000166으로 벌어집니다 (고정비가 사라지면 변동비가 보임). 시간이 되면 이것을 마지막에 다시 돌려 보게 합니다.

## 과제 1 · 요청문 예

```text
my-work/cost.json 의 Build result 뒤에 Record usage(HTTP POST http://data-api:8800/usage) 를 넣어 줘.
본문은 items: usage.by_step 의 단계마다 한 줄 {request_id, user, step, model, prompt_tokens, completion_tokens, cost_usd, route}.
request_id 는 $execution.id , user 는 웹훅 본문의 user .
기록 응답이 오류여도 멈추지 않게 options.response 에 neverError: true , 그다음 Result again(Code) 이 Build result 의 결과를 다시 꺼내 Send result 로.
기대 결과 cases/lab01-challenge.json.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `$execution.id` | 이번 실행의 번호 — 한 요청의 호출 세 줄을 묶음 (AGENTS.md 5절) |
| ② | `user` | 요청 본문의 사람 이름 칸 (`requests/faq-vpn.json`) |
| ③ | `neverError: true` | 4xx · 5xx 응답도 성공 쪽으로 (74일차 Lab 02 과제 2와 같은 옵션) |
| ④ | `Build result` | 사용자에게 보낼 답을 만든 노드. `Record usage` 뒤의 `$json`은 기록 API의 응답 |

정답: [answers/75-lab01-challenge-record.json](answers/75-lab01-challenge-record.json)

| 10/28 결과 | 고치기 전 (예제 2 정답, `answers/04`) | 고친 뒤 (`answers/05`) |
| --- | --- | --- |
| `cases/lab01-challenge.json` | 3/4 (요약 `requests` 0) | **4/4** |
| `flow.py usage` | | requests 3 · calls 9 · $0.002951 (이준호 $0.001040 · 박서연 $0.000959 · 한지훈 $0.000953) |

## 과제 2 · 요청문 예

```text
my-work/cost.json 의 Record usage 에 options.timeout 3000 과 onError continueRegularOutput 를 넣어 줘.
Result again 은 Build result 의 결과에 recorded 를 더해: 기록 응답의 stored 가 1 이상이면 true, 아니면 false.
기록이 실패해도 사용자에게 가는 answer · cost_usd 는 그대로 .
기대 결과 cases/lab01-challenge2.json, cases/lab01-challenge.json.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `3000` | 3초를 ms로 |
| ② | `continueRegularOutput` | 실패한 항목을 **같은 출력**으로 계속 (74일차의 `continueErrorOutput`은 두 번째 출력으로 따로) |
| ③ | `stored` | 기록 API가 성공하면 `{"stored": <항목 수>, "total"}` |
| ④ | 그대로 | 기록은 운영 쪽 일. 답은 바뀌면 안 됨 |

정답: [answers/75-lab01-challenge2-safe-record.json](answers/75-lab01-challenge2-safe-record.json) (과제 1 정답 + `Record usage`의 `timeout` · `onError`, `Result again`의 `recorded`)

| 10/28 결과 (`cases/lab01-challenge2.json`) | 고치기 전 (과제 1 정답, `answers/06`) | 고친 뒤 (`answers/07`) |
| --- | --- | --- |
| 기록 API 고장 (`usage error`) | ✘ 답은 나감 · `recorded` 없음 (3.4초) | ✔ `recorded: false` (4.4초) |
| 기록 API 느림 (`usage slow` 8초) | ✘ **11.2초** · `recorded` 없음 | ✔ `recorded: false` · **6.1초** |
| 고친 뒤 · 기록됨 | ✘ `recorded` 없음 | ✔ `recorded: true` |
| 요약 · 기록된 요청 1건 | ✔ (고장 두 건은 기록되지 않음) | ✔ |
| 합계 | 1/4 | **4/4** |
| `lab01-challenge` | | 4/4 |

- 고치기 전의 고장 케이스도 답은 나갑니다 (과제 1의 `neverError` 덕분에 500 응답을 받아 넘김). 그래서 이 과제의 핵심은 **시간(느림)**과 **표시(`recorded`)**입니다. 풀이 때 이 차이를 짚습니다.
- **수업 준비 중 실제로 본 것**: 처음 데이터 API는 느림 모드에서 8초 뒤 **결국 저장**했습니다. 워크플로우는 3초에 포기해 `recorded: false`라고 답했는데, 다음 테스트를 시작할 때 늦게 저장된 한 줄이 끼어들어 `requests`가 하나 많았습니다. "시간 초과로 포기해도 상대 서버의 일은 끝나지 않을 수 있다"는 실제 운영 문제라 풀이 때 이야기합니다. 데이터 API는 "늦게 답하고 저장하지 않음"(503)으로 바꿨습니다.
- **다음 단계로 넘기는 질문**: "기록이 빠진 요청은 Lab 03의 예산에서도 빠진다. 그럼 예산은 실제보다 남아 보이지 않나?" → Lab 03 예제 1 ▶ 2단계.
