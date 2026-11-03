# Lab 02 · 품질 게이트 · 막고, 격리하고, 알리기

> **강사용 정답본** · 학생 저장소에는 수업이 끝난 뒤 올립니다. 학생용 문제는 [LAB-02-Q-QUALITY-GATE.md](LAB-02-Q-QUALITY-GATE.md).
> 요청문은 예시이며 CLI 에이전트로 보내 재지는 않았습니다. 결과 숫자는 2026-11-01 정답 워크플로우 1회 실행 값입니다 (LLM `gpt-4.1-mini` · temperature 0, 시간은 그때그때 다름). 명령 · 출력 전부: [answers/LAB-TEST-RESULT.md](answers/LAB-TEST-RESULT.md).

## 예제 1 · 요청문 예

```text
my-work/faq-import.json 을 새로 만들어 줘. 웹훅 POST my-faq-import, 이름 "78 FAQ import (my)".
Run check: 규칙을 다시 쓰지 말고 HTTP POST http://localhost:5678/webhook/my-faq-check 로 부른다 (본문 그대로, neverError, timeout 30000).
Batch ok?(IF): invalid / total 이 기준 이하일 때만 받는다. 기준은 본문 max_invalid_ratio, 없으면 0.3. 넘으면 HTTP 422 {error: "batch rejected", batch, invalid_ratio (4자리), max_invalid_ratio, codes}.
Split rows → Store row: 줄마다 ok 면 POST /faq/add, 아니면 POST /quarantine {items: [{batch, row, errors}]} — IF 로 가르지 말고 HTTP 노드 하나에서 주소를 표현식으로.
Summarize: {batch, total, imported, quarantined, rejected: false, score (imported / total, 4자리), max_invalid_ratio, codes, imported_ids, quarantined_ids}. 기대 결과 cases/lab02.json 앞 네 케이스.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `my-faq-check` | 규칙을 다시 쓰지 않고 Lab 01의 검사를 부름 — 규칙이 한 벌 |
| ② | `0.3` | AGENTS.md 3절 기본 기준. 예제 3에서 바꿔 봄 |
| ③ | `422` | 받았지만 처리할 수 없는 내용 (400은 모양이 틀린 것) |
| ④ | 하나 | IF로 갈랐다가 Merge로 합치면 LLM을 더한 뒤 격리 수가 틀림 (AGENTS.md 5절) |

정답: [reference/lab02-example1-import.json](reference/lab02-example1-import.json)

| 11/01 결과 | |
| --- | --- |
| 고치기 전 (`answers/09`, 기준에 같은 테스트) | **0/6** · B-1 **12줄 넣음**(FAQ-105만 API가 막음, FAQ-109 전화 · FAQ-110 링크 · FAQ-003 두 벌), B-2 10줄 (메일 주소 포함), 격리 0 |
| 고친 뒤 (`answers/10`) | **5/6** · B-1 422 (`invalid_ratio` 0.7692), B-2 9줄 · FAQ-209 격리 · `score` 0.9, B-3 FAQ-305 격리. FAQ-210만 ✘ (예제 2) |

## 예제 2 · 요청문 예

```text
my-work/faq-import.json 에 LLM 검사를 더해 줘.
Split rows 뒤에 Only passed(Code) 로 규칙을 통과한 줄만 Judge(AI Agent + OpenAI gpt-4.1-mini, temperature 0) 에게 보낸다.
지시문: 제목과 답만 주고 "답이 제목의 질문에 답하나?" 를 {"match": true|false, "reason"} JSON 으로만.
Decide(Code): Judge 의 i번째 결과를 Only passed 의 i번째 줄과 맞추고, 읽을 수 없으면 match false. match 가 false 면 errors 에 llm_mismatch.
Judge 의 onError 는 continueRegularOutput. 규칙에 걸린 줄은 LLM 에 보내지 않고 그대로 격리. 앞의 칸은 그대로. 기대 결과 cases/lab02.json 전체.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | 통과한 | 규칙에 걸린 줄은 이미 격리 — LLM 비용을 쓸 까닭이 없음 (75일차) |
| ② | `false` | 판정을 읽을 수 없으면 넣지 않음 (fail-closed, 73일차) |
| ③ | `llm_mismatch` | AGENTS.md 3절 코드. 격리함에서 이유가 보임 |
| ④ | `continueRegularOutput` | LLM 오류여도 멈추지 않고 그 줄을 격리로 |

정답: [reference/lab02-example2-import.json](reference/lab02-example2-import.json)

| 11/01 결과 | |
| --- | --- |
| 고치기 전 | **5/6** (예제 1 그대로) |
| 고친 뒤 (`answers/11`) | **6/6** · B-2 8줄 · FAQ-209(`pii`) · FAQ-210(`llm_mismatch`) 격리 · `score` 0.8, B-3 5줄. B-2 1.4초 → **9.3초** |

- LLM이 막은 줄은 FAQ-210 **하나**. 풀이 때: "드문 한 줄을 위해 줄마다 1초" — 가져오기라 괜찮지만 헬프데스크 답이라면?

## 예제 3 · 결과 (에이전트 없이, `answers/12`)

| 실험 | 기준 | 결과 |
| --- | --- | --- |
| B-1 | 0.3 | 422 · 0.7692 |
| B-1 | 0.8 | 받음 · 넣음 **2** · 격리 **11** · `score` 0.1538 (FAQ-113은 LLM이 막음) |
| FAQ만 비움 | — | `cleared` 2 |
| B-2 | 0.05 | 422 · 0.1 |
| B-2 | 0.1 | 받음 (딱 같음) · 넣음 8 · 격리 2 |
| 격리함 | — | 13 |

- **6/6.** 수업 준비 때 실험 순서 때문에 두 번 틀렸음: ① B-1을 받은 뒤 B-2의 FAQ-201이 `same_title` → FAQ 비우기를 넣음, ② B-2를 넣은 뒤 0.05를 보내니 9줄 `exists_id`로 0.9 → 0.05를 먼저. 학생에게도 "앞 배치가 다음 판정을 바꾼다"로.
- 강사 결론: 0.3 유지. 토론 질문: "B-2를 한 줄 때문에 돌려보내는 팀과, B-1을 받아 11줄을 격리하는 팀 중 누가 더 일이 많은가?"

## 과제 1 · 요청문 예

```text
my-work/faq-import.json 에 품질 기록과 알림을 더해 줘.
배치마다 POST http://data-api:8800/quality-log 한 줄 {batch, dataset: "faq", total, valid: imported, quarantined, rejected, score, codes} — 거절된 배치도 rejected: true · score 0 으로.
거절이면 POST /alerts {workflow: "faq-import", severity: "high", reason: "batch_rejected", batch, message}.
받은 배치의 score 가 0.9 미만이면 reason "low_quality" 알림.
알림을 보내도 응답은 같은 결과 (Summarize 의 결과를 다시). 기대 결과 cases/lab02-challenge.json, cases/lab02.json 도.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | `rejected: true · score 0` | 거절도 기록해야 보고서에 '나쁜 배치'가 보임 |
| ② | `batch_rejected` | AGENTS.md 3절 알림 이유. 테스트가 이 글자를 찾음 |
| ③ | `0.9` | 열 줄 중 한 줄 넘게 격리되면 사람이 볼 일 |
| ④ | 같은 결과 | 알림은 곁가지. 부른 쪽이 받는 결과는 바뀌지 않아야 함 |

정답: [answers/78-lab02-challenge-log-alert.json](answers/78-lab02-challenge-log-alert.json)

| 11/01 결과 | |
| --- | --- |
| 고치기 전 (`answers/13`) | **2/5** · 가져오기 둘만 ✔, 기록 · 알림 0 |
| 고친 뒤 (`answers/14`) | **5/5** · 기록 B-1(거절 · 0) · B-2(0.8, 8 · 2), 알림 `batch_rejected` · `low_quality`. `lab02` 6/6 |

## 과제 2 · 요청문 예

```text
my-work/faq-import.json 의 결과에 llm_calls 를 더해 줘.
llm_calls = LLM 검사에 보낸 줄 수 (Only passed 의 줄 수). 거절된 배치(422)의 본문에도 llm_calls 0.
LLM 은 규칙을 통과한 줄에만 부른다는 것을 숫자로 보이게 하는 칸이다. 다른 칸은 그대로.
기대 결과 cases/lab02-challenge2.json 을 세 번 돌려 늘 같은지, lab02 · lab02-challenge 도.
```

**빈칸 답**

| 빈칸 | 답 | 왜 |
| --- | --- | --- |
| ① | 수 | `$('Only passed').all().length` |
| ② | `0` | 거절된 배치는 LLM 앞에서 끝남 — 비용 0을 숫자로 |
| ③ | 통과한 | B-2는 10줄 중 9줄, B-3은 6줄 중 5줄만 |
| ④ | 세 번 | LLM 판정이 늘 같은지 (`--repeat`는 같은 배치를 다시 보내 `exists_id`로 막힘 — 실행 결과 참고) |

정답: [answers/78-lab02-challenge2-llm-calls.json](answers/78-lab02-challenge2-llm-calls.json)

| 11/01 결과 | |
| --- | --- |
| 고치기 전 (`answers/15`) | **0/3** · `llm_calls` 없음 |
| 고친 뒤 (`answers/16`) | **3/3 × 세 번** · B-1 0 · B-2 9 · B-3 5, 세 번 모두 FAQ-210만 막음 (B-2 9.4 · 8.1 · 7.6초). `--no-before --repeat 2`는 **2/6** (B-2 · B-3 거절 — `exists_id`). `lab02` 6/6 · `lab02-challenge` 5/5 |

- 풀이 때: `--repeat`의 ✘는 판정이 흔들린 것이 아니라 데이터가 바뀐 것. "같은 배치를 두 번 보내도 FAQ가 두 벌 생기지 않는다"는 덤.
