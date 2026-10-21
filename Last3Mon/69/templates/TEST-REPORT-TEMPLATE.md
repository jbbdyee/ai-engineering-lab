# 테스트 보고서 · IT 공지문 작성 팀

- 이름:
- 사용한 CLI 에이전트: codex / claude / agy
- 워크플로우 파일: `my-work/notice.json`

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
| `cases/lab03.json --repeat 3` (3케이스) | Passed  /9 |
| `cases/lab03-down.json` (검토자 꺼짐) | Passed  /2 |
| `cases/my-cases.json --repeat 3` | Passed  / |

## 4. 남은 문제 · 배운 점

- 지시문(systemMessage)으로 고친 것과 규칙 노드(If·Code)로 고친 것 중 어느 쪽이 더 안정적이었나?
-
