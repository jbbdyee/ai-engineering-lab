# Lab 02 · 보내는 것 줄이기, 단계마다 맞는 모델, LLM 한 번, 긴 질문의 상한

> **강사용 정답본** · 학생 저장소에 올리지 않습니다. 학생용 문제는 [LAB-02-Q-REDUCE-COST.md](LAB-02-Q-REDUCE-COST.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 정답 워크플로우를 학생 순서대로 2026-10-28에 1회씩 실행한 값입니다. 명령 · 출력 전부: [answers/LAB-TEST-RESULT.md](answers/LAB-TEST-RESULT.md).

## 한눈에 · VPN 질문 하나의 비용

| 단계 | `answer` 입력 | LLM 호출 | VPN 비용 ($) | 품질 테스트 |
| --- | --- | --- | --- | --- |
| 기준 (Lab 01 과제 2 정답, `answers/08`) | 1,781 | 3 | 0.001007 | ✔ |
| 예제 1 · 보내는 것 줄이기 (`answers/09`) | **165** | 3 | 0.000346 | ✔ |
| 예제 2 · 분류 · 검토 nano (`answers/10`) | 165 | 3 | 0.000278 | ✔ |
| 과제 1 · LLM 한 번 (`answers/13`) | 약 165 | **1** | **0.000156** | ✔ |

## 예제 1 · 요청문 예

```text
my-work/cost.json 의 Answer 지시문에서 참고 자료 (사내 규정 전체) 을 빼고 답 규칙만 남겨 줘.
사용자 메시지에는 질문과, FAQ 는 id · title · answer 만, 접수 건은 ticket_id · title · status · note · error 만 보내 줘 (contact · assignee 는 빼고).
답 길이 상한은 max_completion_tokens 200.
Classify · Review 단계는 그대로 .
기대 결과 cases/lab02.json 앞 세 케이스.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | 참고 자료 (사내 규정 전체) | `Answer` 지시문 끝에 붙은 규정 문서 여덟 개. 답은 FAQ · 접수 건으로만 하라고 돼 있어 쓰이지 않음 |
| ② | `answer` | FAQ 항목에서 답 글자가 든 칸 |
| ③ | `max_completion_tokens` | 출력 상한. `gpt-5.4-nano`는 `max_tokens`를 받지 않음 |
| ④ | 그대로 | 한 번에 하나만 (예제 2에서 바꿈) |

정답: [reference/lab02-example1-lean.json](reference/lab02-example1-lean.json)

| 10/28 결과 (`cases/lab02.json`) | 고치기 전 (`answers/08`) | 고친 뒤 (`answers/09`) |
| --- | --- | --- |
| VPN · 보내는 양 | ✘ answer 입력 1,781 | ✔ 165 |
| 접수 · 보내는 양 | ✘ 1,791 | ✔ 152 |
| 비밀번호 · 품질 | ✔ | ✔ |
| 분류는 작은 모델 (예제 2) | ✘ | ✘ (예제 2에서) |
| 프린터 · 품질 | ✔ | ✔ |
| 합계 | 2/5 | 4/5 |

- `diff`: 바뀐 곳은 `Answer`의 본문 하나 (3,491 → 822자).

## 예제 2 · 요청문 예

```text
my-work/cost.json 의 Classify · Review 두 단계의 model 을 gpt-5.4-nano 로 바꿔 줘. Answer 는 gpt-4.1-mini 그대로 .
Build result 의 단계 목록(steps) 의 model 도 같이 바꿔, 비용이 그 모델의 단가 로 계산되게.
기대 결과 cases/lab02.json 전체, cases/lab01.json.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `Classify` | 세 낱말 중 하나를 고르는 쉬운 단계 |
| ② | `gpt-5.4-nano` | `/prices`의 작은 모델 |
| ③ | `gpt-4.1-mini` 그대로 | 사실을 틀리면 안 되는 단계. 바꿔도 되는지는 예제 3에서 재고 정함 (74일차 2.0.0은 golden을 통과했지만 "비용을 본 뒤"로 미룸) |
| ④ | 단가 | `/prices`에서 읽은 그 모델의 input · output |

정답: [reference/lab02-example2-models.json](reference/lab02-example2-models.json)

| 10/28 결과 (`answers/10`) | |
| --- | --- |
| `cases/lab02.json` | **5/5** · VPN $0.000278 (예제 1 $0.000346) |
| `cases/lab01.json` | 3/3 |

- 줄어든 폭이 작은 까닭: 분류 · 검토는 입력이 적은 단계이고, nano의 출력 단가는 mini의 0.78배라 크게 싸지 않습니다. "작은 모델이면 몇 배 싸다"는 막연한 기대를 단가표로 확인하게 합니다.

## 예제 3 · 결과 (에이전트 없이)

| `answers/11` | 답 mini (내 것) | 답 nano (`nano-answer`) |
| --- | --- | --- |
| `lab02` 낱말 검사 | 5/5 | **5/5** |
| `lab01-mix` 일곱 질문 평균 | $0.000233 | $0.000198 (약 15% 덜) |

답을 읽고 본 것 (`nano-answer`, `-v`):

| 질문 | 답에서 |
| --- | --- |
| T-1002 | "T-1002의 처리 상태는 `**처리 중**`이며, `**인증서 발급 승인 대기 중**`입니다 …" — 마크다운 기호 |
| VPN | "… 접수 건은 ticket_id가 없어 상태를 확인할 수 없으며, 요청하신 티켓 기록은 찾지 못했습니다 …" — 묻지 않은 안쪽 말 |
| 비밀번호 · 프린터 | 끝에 "접수 건은 찾지 못했습니다." — 군더더기 |

- 결정: 아끼는 돈(15%)보다 잃는 것(형식 · 군더더기)이 커서 **답은 mini로 둡니다.** 풀이 때 "그럼 테스트를 어떻게 바꾸면 이걸 잡나?" → `not_contains: ["**", "ticket_id"]` 같은 형식 검사 (Q 문서 ▶ 1단계).
- mini 답에도 "현재 접수된 관련 티켓은 없습니다" 같은 군더더기가 있습니다 (`answers/10`). 둘을 나란히 읽고 무엇이 더 나쁜지 이야기하게 합니다.

## 과제 1 · 요청문 예

```text
my-work/cost.json 의 Get ticket 뒤에 Rule classify(Code) 를 넣어 질문에 T-숫자 4개가 있으면 'ticket', FAQ 검색 결과가 있으면 ' faq ', 둘 다 아니면 'unknown'.
Known?(If) 로 unknown 일 때만 Classify(nano) → Parse category → Answer, 아니면 바로 Answer.
Review 단계는 빼고, 답은 Answer 의 글을 그대로 쓴다.
Build result 는 지나간 LLM 단계만 세어 llm_calls 와 비용을 (지나가지 않은 노드는 isExecuted 로 확인).
기대 결과 cases/lab02-challenge.json, cases/lab02.json, cases/lab01.json, cases/lab01-challenge.json.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `faq` | FAQ 검색에 걸린 질문의 분류 |
| ② | `Review` (검토) | 답 단계의 지시문이 이미 말투 · 길이를 정함 |
| ③ | `Answer` | 이제 LLM 답을 만드는 유일한 단계 |
| ④ | `isExecuted` | 지나가지 않은 `Classify`를 읽으면 오류 (AGENTS.md 5절) |

정답: [answers/75-lab02-challenge-one-call.json](answers/75-lab02-challenge-one-call.json)

| 10/28 결과 (`cases/lab02-challenge.json`) | 고치기 전 (예제 2 정답, `answers/12`) | 고친 뒤 (`answers/13`) |
| --- | --- | --- |
| FAQ 넷 | ✘ 3 calls · $0.000241 ~ 0.000297 | ✔ 1 call · $0.000138 ~ 0.000166 |
| 접수 둘 | ✘ 3 calls · $0.000164 · 0.000238 | ✔ 1 call · $0.000108 · 0.000115 |
| 규칙으로 모르는 질문 | ✘ 3 calls | ✔ 2 calls · $0.000097 (nano 분류 $0.0000254 + 답) |
| 합계 | 0/7 | **7/7** |
| `lab02` · `lab01` · `lab01-challenge` | | 5/5 · 3/3 · 4/4 (요청 3건 $0.000409) |

- 시간도 3초대 → 1초대 (호출이 줄어서). 72일차 "LLM 호출을 줄이면 빨라지고 싸진다"를 숫자로 다시 확인.

## 과제 2 · 요청문 예

```text
my-work/cost.json 의 Has question? 뒤에 Get budget(HTTP GET http://data-api:8800/budget) 을, Get prices 뒤에 Prepare question(Code) 을 넣어 줘.
질문이 Get budget 의 max_question_chars 보다 길면 앞 40% 와 뒤 60 % 만 남기고 가운데를 ' … ' 로 줄여 줘.
Search FAQ 의 q, Rule classify, Answer 는 모두 원래 질문 대신 Prepare question 의 question 을 쓰게.
결과에 trimmed(true/false) 와 question_chars (원래 글자 수) 를 더해 줘.
기대 결과 cases/lab02-challenge2.json, cases/lab02-challenge.json.
```

**빈칸 답** (Q 문서 ▶ 빈칸 채우기 `____①`~`____④`)

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `max_question_chars` | `/budget`의 글자 수 상한 (사람이 정함, 기본 500) |
| ② | `60` | 앞 40% + 뒤 60% |
| ③ | `Prepare question` | 줄인 질문을 만드는 노드 |
| ④ | `question_chars` | "짧은 질문은 그대로" 케이스가 보는 칸 |

정답: [answers/75-lab02-challenge2-long-question.json](answers/75-lab02-challenge2-long-question.json)

| 10/28 결과 (`cases/lab02-challenge2.json`) | 고치기 전 (과제 1 정답, `answers/14`) | 고친 뒤 (`answers/15`) |
| --- | --- | --- |
| 긴 로그 + 끝에 질문 · 프린터 (6,298자) | ✘ **$0.001196** · `trimmed` 없음 | ✔ **$0.000237** · "대기열" |
| 앞에 질문 + 긴 로그 · VPN (6,103자) | ✘ $0.001099 | ✔ $0.000260 · "인증서" |
| 짧은 질문은 그대로 | ✘ `trimmed` 없음 | ✔ `trimmed: false` · `question_chars: 24` |
| 사람이 상한을 늘리면 자르지 않음 | ✘ `trimmed` 없음 | ✔ `trimmed: false` · $0.001196 |
| 합계 | 0/4 | **4/4** |
| `lab02-challenge` | | 7/7 |

- **수업 준비 때 정한 것**: 처음에는 긴 질문도 $0.0002 이하를 기대했는데, 500자로 줄여도 $0.00024 ~ 0.00026, 300자로 줄여도 $0.00021 ~ 0.00022였습니다. 답(출력)만으로 약 $0.0001이 들기 때문입니다. 그래서 상한을 500자로 두고 기대를 **$0.0003 이하**(줄이기 전의 약 4분의 1)로 정했습니다. 풀이 때 "입력을 아무리 줄여도 남는 비용은?" → 출력 · FAQ.
- `cases/lab02-challenge2.json`의 `before` · `after`가 `/budget/reset`으로 상한을 500으로 되돌립니다.
