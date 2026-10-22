# 테스트 보고서 · 사내 IT 규정 Q&A

- 이름:
- 사용한 CLI 에이전트: codex / claude / agy
- 워크플로우 파일: `my-work/index.json, my-work/search.json, my-work/policy-qa.json`

## 1. 내가 쓴 테스트 (`cases/my-cases.json`)

| 케이스 | 요청 | 기대 결과 (업무 규칙) |
| --- | --- | --- |
|  |  |  |

## 2. 실패와 고친 내용

| 실패한 케이스 | 처음 결과 (3번 중 통과) | 내가 생각한 원인 | 에이전트가 고친 곳 | 고친 뒤 (3번 중 통과) |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## 3. 최종 결과

| 테스트 파일 | 결과 |
| --- | --- |
| `cases/lab02.json` (답과 출처) | Passed  /6 |
| `cases/lab02-challenge.json` (답 검사) | Passed  /8 |
| `cases/retrieval-answer.json` (answer@1) | Passed  /24 |
| `cases/lab03-threshold.json` (기준값) | Passed  /10 |
| `cases/my-cases.json --repeat 3` | Passed  / |

## 4. 남은 문제 · 배운 점

- 지시문(systemMessage)으로 고친 것과 규칙 노드(If·Code)로 고친 것 중 어느 쪽이 더 안정적이었나?
-
